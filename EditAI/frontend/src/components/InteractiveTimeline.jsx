import React, { useRef, useState, useEffect } from 'react';
import {
  Scissors,
  Trash2,
  Lock,
  Volume2,
  VolumeX,
  Eye,
  ZoomIn,
  ZoomOut,
  Maximize2,
  MousePointer,
  RotateCcw
} from 'lucide-react';
import { formatSMPTE, formatTimecode } from '../utils/timeUtils';

export default function InteractiveTimeline({
  timeline,
  currentTime,
  onSeek,
  onSelectClip,
  onSelectRange,
  onSplitAtPlayhead,
  onDeleteSelection,
  onUndo,
  fps = 25
}) {
  const containerRef = useRef(null);
  const trackRef = useRef(null);
  const [zoom, setZoom] = useState(1.0);
  const [isDraggingPlayhead, setIsDraggingPlayhead] = useState(false);
  const [activeTool, setActiveTool] = useState('select'); // 'select' | 'blade'

  const totalDuration = timeline?.total_duration || 30.0;
  const clips = timeline?.clips || [];
  const subtitles = timeline?.subtitles || [];
  const audioTrack = timeline?.audio_track;

  // Time <-> Pixel conversion
  const timeToPx = (time) => {
    if (!containerRef.current || totalDuration <= 0) return 0;
    const baseWidth = containerRef.current.clientWidth - 110;
    const pxPerSec = (baseWidth / totalDuration) * zoom;
    return time * pxPerSec;
  };

  const pxToTime = (px) => {
    if (!containerRef.current || totalDuration <= 0) return 0;
    const baseWidth = containerRef.current.clientWidth - 110;
    const pxPerSec = (baseWidth / totalDuration) * zoom;
    if (pxPerSec <= 0) return 0;
    const t = px / pxPerSec;
    return Math.max(0, Math.min(totalDuration, t));
  };

  const handleTrackClick = (e) => {
    if (!trackRef.current) return;
    const rect = trackRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const newTime = pxToTime(clickX);

    if (activeTool === 'blade') {
      onSplitAtPlayhead(newTime);
    } else {
      onSeek(newTime);
    }
  };

  // Playhead dragging
  const handleMouseDownPlayhead = (e) => {
    e.stopPropagation();
    setIsDraggingPlayhead(true);
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDraggingPlayhead || !trackRef.current) return;
      const rect = trackRef.current.getBoundingClientRect();
      const dragX = e.clientX - rect.left;
      const newTime = pxToTime(dragX);
      onSeek(newTime);
    };

    const handleMouseUp = () => {
      setIsDraggingPlayhead(false);
    };

    if (isDraggingPlayhead) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDraggingPlayhead]);

  // Generate ruler tick marks with SMPTE timecode (e.g. 01:00:00:00)
  const renderRulerTicks = () => {
    const step = zoom > 1.8 ? 2 : zoom > 1.2 ? 5 : 10;
    const ticks = [];
    for (let t = 0; t <= Math.ceil(totalDuration); t += step) {
      const left = timeToPx(t);
      ticks.push(
        <div
          key={t}
          style={{ left: `${left}px` }}
          className="absolute top-0 bottom-0 flex flex-col justify-between pointer-events-none"
        >
          <span className="text-[9px] text-[#636875] font-mono pl-1 select-none">
            {formatSMPTE(t, fps)}
          </span>
          <div className="w-px h-1.5 bg-[#2b2d35]" />
        </div>
      );
    }
    return ticks;
  };

  const playheadX = timeToPx(currentTime);
  const totalTrackWidth = timeToPx(totalDuration);

  return (
    <div
      ref={containerRef}
      className="h-full flex flex-col bg-[#121316] border-t border-[#23252b] select-none text-[#a0a4ae]"
    >
      {/* 1. DaVinci Cut-Page Style Mini Overview Strip */}
      <div className="h-4 bg-[#101113] border-b border-[#1c1d22] relative overflow-hidden flex items-center px-2">
        <div className="w-full h-2 bg-[#1b1c20] rounded-sm relative overflow-hidden">
          {/* Mini clip indicators */}
          {clips.map((clip) => {
            const leftPct = (clip.timeline_start / (totalDuration || 1)) * 100;
            const widthPct = (clip.duration / (totalDuration || 1)) * 100;
            return (
              <div
                key={clip.id}
                style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
                className="absolute top-0 bottom-0 bg-[#2b3a4e] border-r border-[#16171a]"
              />
            );
          })}
          {/* Mini Playhead Needle */}
          <div
            style={{ left: `${(currentTime / (totalDuration || 1)) * 100}%` }}
            className="absolute top-0 bottom-0 w-0.5 bg-[#d4483b]"
          />
        </div>
      </div>

      {/* 2. Timeline Toolbar: Tools, Zoom & Selection Actions */}
      <div className="h-7 px-3 border-b border-[#212328] flex items-center justify-between bg-[#16171b] text-[11px]">
        {/* Left: Tools (Select, Razor Blade, Delete, Undo) */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setActiveTool('select')}
            className={`p-1 rounded transition ${
              activeTool === 'select'
                ? 'bg-[#252830] text-[#e0e3eb] border border-[#343844]'
                : 'text-[#6f7482] hover:text-[#c4c7d0]'
            }`}
            title="Selection Tool (A)"
          >
            <MousePointer className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setActiveTool('blade')}
            className={`p-1 rounded transition ${
              activeTool === 'blade'
                ? 'bg-[#252830] text-[#e0e3eb] border border-[#343844]'
                : 'text-[#6f7482] hover:text-[#c4c7d0]'
            }`}
            title="Blade Edit Tool (B)"
          >
            <Scissors className="w-3.5 h-3.5 text-[#d48b3b]" />
          </button>

          <button
            onClick={() => onSplitAtPlayhead(currentTime)}
            className="flex items-center gap-1 px-2 py-0.5 rounded hover:bg-[#202228] text-[#868a96] hover:text-[#d0d3dc] transition text-[10px]"
            title="Split Clip at Playhead (S)"
          >
            <span>Split at Playhead</span>
          </button>

          <button
            onClick={onDeleteSelection}
            className="p-1 rounded hover:bg-[#252830] text-[#6f7482] hover:text-[#d45555] transition ml-1"
            title="Delete Selected Clip or Range (Delete / Backspace)"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={onUndo}
            className="p-1 rounded hover:bg-[#252830] text-[#6f7482] hover:text-[#d0d3dc] transition"
            title="Undo (Ctrl+Z)"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Center: Active Selection Status */}
        {timeline?.selection_range && (
          <span className="text-[10px] text-[#9da1ad] font-mono">
            In/Out: {formatSMPTE(timeline.selection_range[0], fps)} - {formatSMPTE(timeline.selection_range[1], fps)}
          </span>
        )}

        {/* Right: Zoom Controls */}
        <div className="flex items-center gap-1.5 text-[10px]">
          <button
            onClick={() => setZoom(Math.max(0.6, zoom - 0.25))}
            className="p-0.5 rounded text-[#6f7482] hover:text-[#c4c7d0] transition"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="font-mono text-[#5b606c] w-8 text-center">{Math.round(zoom * 100)}%</span>
          <button
            onClick={() => setZoom(Math.min(3.0, zoom + 0.25))}
            className="p-0.5 rounded text-[#6f7482] hover:text-[#c4c7d0] transition"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setZoom(1.0)}
            className="p-0.5 rounded text-[#6f7482] hover:text-[#c4c7d0] transition"
            title="Reset Zoom"
          >
            <Maximize2 className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* 3. Main Multi-Track Horizontal Editor Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Column: Track Headers (V1, A1, Sub1) */}
        <div className="w-20 shrink-0 border-r border-[#212328] bg-[#141518] flex flex-col text-[10px] font-mono select-none">
          {/* Empty corner matching ruler height */}
          <div className="h-5 border-b border-[#212328] bg-[#16171b]" />

          {/* V1 Track Header */}
          <div className="h-10 border-b border-[#212328] px-2 flex items-center justify-between bg-[#17181c]">
            <span className="font-medium text-[#d0d3dc]">V1</span>
            <div className="flex items-center gap-1 text-[#666a77]">
              <Lock className="w-2.5 h-2.5" />
              <Eye className="w-2.5 h-2.5" />
            </div>
          </div>

          {/* A1 Track Header */}
          <div className="h-8 border-b border-[#212328] px-2 flex items-center justify-between bg-[#17181c]">
            <span className="font-medium text-[#d0d3dc]">A1</span>
            <div className="flex items-center gap-1 text-[#666a77]">
              <Lock className="w-2.5 h-2.5" />
              <Volume2 className="w-2.5 h-2.5" />
            </div>
          </div>

          {/* Sub1 Track Header */}
          <div className="h-7 px-2 flex items-center justify-between bg-[#17181c]">
            <span className="font-medium text-[#d0d3dc]">Sub1</span>
            <Lock className="w-2.5 h-2.5 text-[#666a77]" />
          </div>
        </div>

        {/* Right Scrollable Timeline Track Area */}
        <div className="flex-1 overflow-x-auto overflow-y-hidden relative timeline-track-grid bg-[#111215]">
          <div
            ref={trackRef}
            onClick={handleTrackClick}
            style={{ width: `${Math.max(totalTrackWidth + 80, 700)}px` }}
            className={`relative h-full flex flex-col justify-start select-none ${
              activeTool === 'blade' ? 'cursor-crosshair' : 'cursor-pointer'
            }`}
          >
            {/* 3a. SMPTE Time Ruler */}
            <div className="h-5 relative border-b border-[#212328] bg-[#16171b]">
              {renderRulerTicks()}
            </div>

            {/* 3b. Active Selection Highlight */}
            {timeline?.selection_range && (
              <div
                style={{
                  left: `${timeToPx(timeline.selection_range[0])}px`,
                  width: `${timeToPx(timeline.selection_range[1] - timeline.selection_range[0])}px`,
                }}
                className="absolute top-5 bottom-0 bg-[#3b82d4]/15 border-x border-[#3b82d4]/70 pointer-events-none z-10"
              />
            )}

            {/* 3c. VIDEO TRACK (V1) */}
            <div className="h-10 relative flex items-center border-b border-[#1c1d22] bg-[#131417] px-0.5 overflow-hidden">
              {clips.map((clip) => {
                const clipLeft = timeToPx(clip.timeline_start);
                const clipWidth = timeToPx(clip.duration);
                const isSelected = timeline.selected_clip_id === clip.id;

                return (
                  <div
                    key={clip.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectClip(clip.id);
                    }}
                    style={{
                      left: `${clipLeft}px`,
                      width: `${Math.max(clipWidth, 8)}px`,
                    }}
                    className={`absolute top-0.5 bottom-0.5 rounded-sm px-1.5 flex flex-col justify-center cursor-pointer transition border text-[10px] ${
                      isSelected
                        ? 'bg-[#293d56] border-[#5594df] text-white shadow-sm ring-1 ring-[#5594df]/40'
                        : 'bg-[#202834] hover:bg-[#253040] border-[#2d3848] text-[#c4c7d0]'
                    }`}
                    title={`${clip.name} (${clip.duration.toFixed(2)}s)`}
                  >
                    <div className="flex items-center justify-between truncate pointer-events-none">
                      <span className="truncate font-medium">{clip.name}</span>
                      <span className="text-[9px] font-mono text-[#8a91a0] ml-1">{clip.duration.toFixed(1)}s</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* 3d. AUDIO TRACK (A1) */}
            <div className="h-8 relative flex items-center border-b border-[#1c1d22] bg-[#121316] px-1 overflow-hidden">
              <div
                style={{ width: `${totalTrackWidth}px` }}
                className="h-full bg-[#1b2620] border border-[#24352b] rounded-sm flex items-center px-2 relative"
              >
                <span className="text-[9px] text-[#718c7d] font-mono pointer-events-none">
                  {audioTrack ? audioTrack.filename : 'Audio 1 (Embedded A1)'}
                </span>
                {/* Simulated audio waveform */}
                <div className="absolute inset-x-2 bottom-1 h-2 flex items-end gap-0.5 opacity-30 pointer-events-none">
                  {[...Array(60)].map((_, i) => (
                    <div
                      key={i}
                      style={{ height: `${20 + (i % 5) * 16}%` }}
                      className="w-1 bg-[#478a63] rounded-t-sm"
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* 3e. SUBTITLE TRACK (Sub1) */}
            <div className="h-7 relative flex items-center bg-[#121316] px-1 overflow-hidden">
              {subtitles.map((sub) => {
                const subLeft = timeToPx(sub.start_time);
                const subWidth = timeToPx(sub.end_time - sub.start_time);

                return (
                  <div
                    key={sub.id}
                    style={{
                      left: `${subLeft}px`,
                      width: `${Math.max(subWidth, 6)}px`,
                    }}
                    className="absolute top-0.5 bottom-0.5 bg-[#2c261b] hover:bg-[#383022] border border-[#443825] rounded-sm text-[9px] text-[#c4b595] px-1 truncate flex items-center cursor-pointer transition"
                    title={`Subtitle: "${sub.text}"`}
                  >
                    <span className="truncate font-mono">{sub.text}</span>
                  </div>
                );
              })}
            </div>

            {/* 3f. Vertical Red/Amber DaVinci Playhead Needle */}
            <div
              style={{ left: `${playheadX}px` }}
              className="absolute top-0 bottom-0 z-30 pointer-events-none flex flex-col items-center"
            >
              {/* Playhead Top Triangle Knob */}
              <div
                onMouseDown={handleMouseDownPlayhead}
                className="w-3 h-3 bg-[#d4483b] rounded-t-sm rotate-45 pointer-events-auto cursor-ew-resize -translate-y-1 hover:scale-125 transition-transform shadow-md"
                title={`Playhead: ${formatSMPTE(currentTime, fps)}`}
              />
              {/* Vertical needle */}
              <div className="w-[1px] flex-1 bg-[#d4483b]" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
