import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  ChevronLeft,
  ChevronRight,
  Repeat,
  Volume2,
  VolumeX,
  Maximize
} from 'lucide-react';
import { formatSMPTE } from '../utils/timeUtils';

export default function VideoPlayer({
  videoSrc,
  timeline,
  currentTime,
  onTimeUpdate,
  isPlaying,
  setIsPlaying,
  subtitles = [],
  playbackRange = null,
  onPlaybackComplete,
  fps = 25
}) {
  const videoRef = useRef(null);
  const containerRef = useRef(null);
  const [volume, setVolume] = useState(1.0);
  const [isMuted, setIsMuted] = useState(false);
  const [activeSubtitle, setActiveSubtitle] = useState('');
  const [isLooping, setIsLooping] = useState(false);
  const [showGuides, setShowGuides] = useState(true);
  const [aspectGuide, setAspectGuide] = useState('9:16'); // '9:16' | '16:9' | '1:1' | 'none'
  const [vuLevel, setVuLevel] = useState({ left: -45, right: -45 });

  // Find active clip at timeline time
  const getActiveClipAtTime = useCallback((tlTime) => {
    if (!timeline || !timeline.clips || timeline.clips.length === 0) return null;
    return (
      timeline.clips.find(
        (c) => tlTime >= c.timeline_start && tlTime < c.timeline_end
      ) || timeline.clips[timeline.clips.length - 1]
    );
  }, [timeline]);

  const activeClip = getActiveClipAtTime(currentTime);
  const activeClipSrc = activeClip?.stream_url || videoSrc;

  // Map timeline time to video source time
  const getSourceTimeForTimelineTime = useCallback((tlTime) => {
    if (!timeline || !timeline.clips || timeline.clips.length === 0) {
      return tlTime;
    }
    const clip = getActiveClipAtTime(tlTime);
    if (!clip) return 0;
    const offset = Math.max(0, tlTime - clip.timeline_start);
    return clip.source_start + (offset * (clip.speed || 1.0));
  }, [timeline, getActiveClipAtTime]);

  // Map video source time to timeline time
  const getTimelineTimeForSourceTime = useCallback((srcTime) => {
    if (!timeline || !timeline.clips || timeline.clips.length === 0) {
      return srcTime;
    }
    const clip = getActiveClipAtTime(currentTime);
    if (!clip) return currentTime;
    const offset = (srcTime - clip.source_start) / (clip.speed || 1.0);
    return Math.max(clip.timeline_start, Math.min(clip.timeline_end, clip.timeline_start + offset));
  }, [timeline, currentTime, getActiveClipAtTime]);

  // Synchronize HTML5 video element when currentTime changes externally
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !activeClipSrc) return;

    const expectedSourceTime = getSourceTimeForTimelineTime(currentTime);
    if (Math.abs(video.currentTime - expectedSourceTime) > 0.3) {
      video.currentTime = expectedSourceTime;
    }
  }, [currentTime, getSourceTimeForTimelineTime, activeClipSrc]);

  // Handle active video source change across clips
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !activeClipSrc) return;

    const expectedSourceTime = getSourceTimeForTimelineTime(currentTime);
    video.currentTime = expectedSourceTime;
    if (isPlaying) {
      video.play().catch(() => {});
    }
  }, [activeClipSrc]);

  // Play / Pause sync
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !activeClipSrc) return;

    if (isPlaying) {
      video.play().catch(() => setIsPlaying(false));
    } else {
      video.pause();
    }
  }, [isPlaying, activeClipSrc, setIsPlaying]);

  // Subtitle synchronization
  useEffect(() => {
    if (!subtitles || subtitles.length === 0) {
      setActiveSubtitle('');
      return;
    }
    const currentSub = subtitles.find(
      (s) => currentTime >= s.start_time && currentTime <= s.end_time
    );
    setActiveSubtitle(currentSub ? currentSub.text : '');
  }, [currentTime, subtitles]);

  // Audio VU Meter simulation while playing
  useEffect(() => {
    if (!isPlaying) {
      setVuLevel({ left: -50, right: -50 });
      return;
    }

    const interval = setInterval(() => {
      // Simulate realistic stereo dB peaks (-18dB to -4dB range during sound)
      const base = -16 + (Math.random() * 12);
      const l = Math.min(-1, Math.max(-50, base + (Math.random() * 4 - 2)));
      const r = Math.min(-1, Math.max(-50, base + (Math.random() * 4 - 2)));
      setVuLevel({ left: Math.round(l), right: Math.round(r) });
    }, 80);

    return () => clearInterval(interval);
  }, [isPlaying]);

  // Time update handler
  const handleTimeUpdate = () => {
    const video = videoRef.current;
    if (!video) return;

    const currentSrcTime = video.currentTime;
    let nextTimelineTime = getTimelineTimeForSourceTime(currentSrcTime);

    // Check if we reached the end of the current clip in a multi-clip timeline
    const active = getActiveClipAtTime(currentTime);
    if (active && timeline?.clips?.length > 1) {
      if (nextTimelineTime >= active.timeline_end - 0.08) {
        const clipIdx = timeline.clips.findIndex((c) => c.id === active.id);
        if (clipIdx !== -1 && clipIdx < timeline.clips.length - 1) {
          const nextClip = timeline.clips[clipIdx + 1];
          onTimeUpdate(nextClip.timeline_start);
          return;
        }
      }
    }

    if (playbackRange) {
      const [start, end] = playbackRange;
      if (nextTimelineTime >= end || nextTimelineTime < start) {
        if (isLooping) {
          nextTimelineTime = start;
          video.currentTime = getSourceTimeForTimelineTime(start);
        } else {
          setIsPlaying(false);
          video.pause();
          if (onPlaybackComplete) onPlaybackComplete();
          return;
        }
      }
    } else if (timeline && timeline.total_duration > 0) {
      if (nextTimelineTime >= timeline.total_duration) {
        if (isLooping) {
          nextTimelineTime = 0;
          video.currentTime = getSourceTimeForTimelineTime(0);
        } else {
          setIsPlaying(false);
          video.pause();
          nextTimelineTime = timeline.total_duration;
        }
      }
    }

    onTimeUpdate(nextTimelineTime);
  };

  const handleVideoEnded = () => {
    const active = getActiveClipAtTime(currentTime);
    if (active && timeline?.clips?.length > 1) {
      const clipIdx = timeline.clips.findIndex((c) => c.id === active.id);
      if (clipIdx !== -1 && clipIdx < timeline.clips.length - 1) {
        const nextClip = timeline.clips[clipIdx + 1];
        onTimeUpdate(nextClip.timeline_start);
        return;
      }
    }
    if (isLooping) {
      jumpToStart();
      if (isPlaying) videoRef.current?.play().catch(() => {});
    } else {
      setIsPlaying(false);
    }
  };

  // Step 1 frame backward / forward
  const stepFrame = (deltaFrames) => {
    const frameDuration = 1 / fps;
    const newTime = Math.max(0, Math.min(timeline?.total_duration || 30.0, currentTime + deltaFrames * frameDuration));
    onTimeUpdate(newTime);
    if (videoRef.current) {
      videoRef.current.currentTime = getSourceTimeForTimelineTime(newTime);
    }
  };

  const jumpToStart = () => {
    onTimeUpdate(0.0);
    if (videoRef.current) videoRef.current.currentTime = getSourceTimeForTimelineTime(0.0);
  };

  const jumpToEnd = () => {
    const end = timeline?.total_duration || 0.0;
    onTimeUpdate(end);
    if (videoRef.current) videoRef.current.currentTime = getSourceTimeForTimelineTime(end);
  };

  const totalDuration = timeline?.total_duration || 30.0;

  // Convert dB (-50 to 0) to percentage (0% to 100%) for VU meter height
  const dbToPercent = (db) => {
    if (db <= -50) return 0;
    return Math.min(100, Math.max(0, ((db + 50) / 50) * 100));
  };

  return (
    <div
      ref={containerRef}
      className="h-full flex flex-col bg-[#111215] select-none text-[#b3b7c0]"
    >
      {/* 1. Video Monitor Canvas & Audio VU Meter Container */}
      <div className="flex-1 relative flex overflow-hidden bg-[#0a0a0c]">
        {/* Main Video Screen */}
        <div className="flex-1 relative flex items-center justify-center overflow-hidden">
          {activeClipSrc ? (
            <video
              ref={videoRef}
              src={activeClipSrc}
              onTimeUpdate={handleTimeUpdate}
              onEnded={handleVideoEnded}
              className="w-full h-full object-contain max-h-[58vh]"
              playsInline
            />
          ) : (
            <div className="flex flex-col items-center justify-center text-[#40434c]">
              <span className="text-xs">No media loaded in viewer</span>
            </div>
          )}

          {/* DaVinci Resolve Vertical Framing Safe Guides (from screenshot) */}
          {showGuides && aspectGuide === '9:16' && (
            <div className="absolute inset-y-0 flex items-center justify-center pointer-events-none">
              <div
                style={{ width: 'calc(58vh * 9 / 16)', height: '58vh' }}
                className="border-x-2 border-white/60 pointer-events-none relative shadow-[0_0_15px_rgba(0,0,0,0.5)]"
              >
                {/* Internal subtle margin line */}
                <div className="absolute inset-y-0 inset-x-2 border-x border-white/20" />
              </div>
            </div>
          )}

          {/* Subtitle Overlay */}
          {activeSubtitle && (
            <div className="absolute bottom-5 left-1/2 -translate-x-1/2 max-w-[85%] text-center pointer-events-none z-10">
              <span className="inline-block px-2.5 py-1 rounded bg-black/85 text-[#f0f2f5] font-normal text-xs md:text-sm border border-white/15 shadow">
                {activeSubtitle}
              </span>
            </div>
          )}

          {/* Top-Right SMPTE Timecode Overlay */}
          <div className="absolute top-2.5 right-3 font-mono text-xs text-[#a0a4ae] bg-black/70 px-2 py-0.5 rounded border border-[#2b2d34]">
            {formatSMPTE(currentTime, fps)}
          </div>
        </div>

        {/* Right Edge: DaVinci Resolve Vertical Stereo Audio VU Meter */}
        <div className="w-9 border-l border-[#1f2025] bg-[#101114] flex flex-col items-center py-2 text-[9px] font-mono text-[#5f636e]">
          <Volume2 className="w-3 h-3 text-[#5f636e] mb-1" />

          {/* Meter Bars Container */}
          <div className="flex-1 w-full flex items-center justify-center gap-1 px-1 relative">
            {/* dB scale labels */}
            <div className="absolute left-0.5 inset-y-0 flex flex-col justify-between text-[8px] text-[#42454d] pointer-events-none">
              <span>0</span>
              <span>-10</span>
              <span>-20</span>
              <span>-30</span>
              <span>-50</span>
            </div>

            {/* Left Channel Bar */}
            <div className="w-1.5 h-full bg-[#1b1c20] rounded-sm relative overflow-hidden flex flex-col justify-end">
              <div
                style={{ height: `${dbToPercent(vuLevel.left)}%` }}
                className={`w-full transition-all duration-75 ${
                  vuLevel.left > -4 ? 'bg-[#d4483b]' : vuLevel.left > -12 ? 'bg-[#d4a03b]' : 'bg-[#3b9a55]'
                }`}
              />
            </div>

            {/* Right Channel Bar */}
            <div className="w-1.5 h-full bg-[#1b1c20] rounded-sm relative overflow-hidden flex flex-col justify-end">
              <div
                style={{ height: `${dbToPercent(vuLevel.right)}%` }}
                className={`w-full transition-all duration-75 ${
                  vuLevel.right > -4 ? 'bg-[#d4483b]' : vuLevel.right > -12 ? 'bg-[#d4a03b]' : 'bg-[#3b9a55]'
                }`}
              />
            </div>
          </div>

          <span className="text-[8px] mt-1 text-[#484b54]">dB</span>
        </div>
      </div>

      {/* 2. Sub-viewer Transport & Navigation Toolbar (Exact DaVinci Layout) */}
      <div className="h-9 bg-[#16171b] border-t border-[#23252b] px-3 flex items-center justify-between text-[#828692] text-xs">
        {/* Left: Aspect guide selector & Frame navigation */}
        <div className="flex items-center gap-2">
          {/* Guide switcher */}
          <select
            value={aspectGuide}
            onChange={(e) => setAspectGuide(e.target.value)}
            className="bg-[#1e2025] text-[10px] text-[#9da1ad] rounded px-1.5 py-0.5 border border-[#2c2f37] focus:outline-none"
            title="Aspect Ratio Framing Guides"
          >
            <option value="9:16">Guides: 9:16 Vertical</option>
            <option value="16:9">Guides: 16:9 Landscape</option>
            <option value="1:1">Guides: 1:1 Square</option>
            <option value="none">Guides: None</option>
          </select>
        </div>

        {/* Center: DaVinci Transport Controls: |<  <  Play/Pause  >  >|  Loop */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={jumpToStart}
            className="p-1 rounded hover:bg-[#252830] hover:text-[#d0d3dc] transition"
            title="Go to Start (Home)"
          >
            <SkipBack className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => stepFrame(-1)}
            className="p-1 rounded hover:bg-[#252830] hover:text-[#d0d3dc] transition"
            title="Step -1 Frame (Left Arrow)"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsPlaying(!isPlaying)}
            disabled={!videoSrc}
            className="w-7 h-7 rounded bg-[#252830] hover:bg-[#30343e] text-[#e0e3eb] flex items-center justify-center border border-[#373a44] transition disabled:opacity-40"
            title={isPlaying ? 'Pause (Space)' : 'Play (Space)'}
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 ml-0.5" />}
          </button>

          <button
            onClick={() => stepFrame(1)}
            className="p-1 rounded hover:bg-[#252830] hover:text-[#d0d3dc] transition"
            title="Step +1 Frame (Right Arrow)"
          >
            <ChevronRight className="w-4 h-4" />
          </button>

          <button
            onClick={jumpToEnd}
            className="p-1 rounded hover:bg-[#252830] hover:text-[#d0d3dc] transition"
            title="Go to End (End)"
          >
            <SkipForward className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setIsLooping(!isLooping)}
            className={`p-1 rounded transition ml-1 ${
              isLooping ? 'bg-[#292c36] text-[#d48b3b]' : 'hover:bg-[#252830] text-[#717582] hover:text-[#c4c7d0]'
            }`}
            title="Toggle Loop Playback"
          >
            <Repeat className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Right: TCG SMPTE Readout */}
        <div className="flex items-center gap-2 font-mono text-[11px] text-[#9aa0ae]">
          <span className="text-[#5b5f6b]">TCG</span>
          <span className="text-[#c4c8d4] font-medium">{formatSMPTE(currentTime, fps)}</span>
        </div>
      </div>
    </div>
  );
}
