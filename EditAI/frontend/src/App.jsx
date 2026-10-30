import React, { useState, useEffect, useCallback, useRef } from 'react';
import Navbar from './components/Navbar';
import MediaImportPanel from './components/MediaImportPanel';
import VideoPlayer from './components/VideoPlayer';
import InteractiveTimeline from './components/InteractiveTimeline';
import Inspector from './components/Inspector';
import AIChatbotPanel from './components/AIChatbotPanel';
import ExportModal from './components/ExportModal';
import ProjectListModal from './components/ProjectListModal';
import BottomPageBar from './components/BottomPageBar';
import MultiVideoAssemblyStage from './components/MultiVideoAssemblyStage';

import {
  uploadBatchVideos,
  uploadVideo,
  uploadAudio,
  uploadSubtitle,
  loadSampleProject,
  analyzeVideo,
  sendChatbotCommand,
  splitTimeline,
  deleteTimelineSelection,
  cutTimelineSelection,
  undoTimelineAction,
  redoTimelineAction,
  createProject,
  saveProject,
  getProject,
  autosaveProject
} from './api';

export default function App() {
  // Project management state
  const [projectId, setProjectId] = useState('proj_default');
  const [projectName, setProjectName] = useState('New Project 1');
  const [isEdited, setIsEdited] = useState(false);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);

  // Media Pool state (multiple videos supported)
  const [mediaPoolVideos, setMediaPoolVideos] = useState([]);
  const [activeVideoId, setActiveVideoId] = useState(null);
  const [videoMetadata, setVideoMetadata] = useState(null);
  const [videoSrc, setVideoSrc] = useState('');
  const [audioTrack, setAudioTrack] = useState(null);
  const [subtitles, setSubtitles] = useState([]);

  // Timeline state
  const [timeline, setTimeline] = useState({
    clips: [],
    total_duration: 0.0,
    selected_clip_id: null,
    selection_range: null,
    audio_track: null,
    subtitles: [],
    playhead_time: 0.0,
  });

  // Playback & Viewer state
  const [currentTime, setCurrentTime] = useState(0.0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackRange, setPlaybackRange] = useState(null);

  // Analysis & Inspector state
  const [analysis, setAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeRightTab, setActiveRightTab] = useState('ai'); // 'inspector' | 'ai'

  // AI Assistant Chat state
  const [chatMessages, setChatMessages] = useState([
    {
      id: 'init_1',
      sender: 'assistant',
      text: 'EditMind AI ready. You can describe any edit in natural language, for example:\n• "Select the clip from 00:10 to 00:25."\n• "Split at 00:18."\n• "Delete the selected segment."\n• "Delete the second half of the selected clip."\n• "Export the edited video."',
      timestamp: 'Ready',
    },
  ]);
  const [isChatProcessing, setIsChatProcessing] = useState(false);

  // Export & Assembly modals
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isAssemblyStageOpen, setIsAssemblyStageOpen] = useState(false);
  const [sourceClips, setSourceClips] = useState([]);
  const [assemblyResult, setAssemblyResult] = useState(null);
  const [activePage, setActivePage] = useState('edit');

  // Handle Multi-Video AI Assembly application
  const handleApplyAssembly = (result) => {
    if (!result) return;
    setAssemblyResult(result);

    const tl = result.timeline_state || {
      clips: [],
      total_duration: result.total_duration || 0,
      selected_clip_id: null,
      selection_range: null,
      subtitles: result.subtitles || [],
      playhead_time: 0.0,
    };
    setTimeline(tl);
    setSubtitles(result.subtitles || tl.subtitles || []);

    if (tl.clips && tl.clips.length > 0) {
      const firstClip = tl.clips[0];
      setVideoSrc(firstClip.stream_url || '');
      setVideoMetadata({
        filename: `Assembled Production (${result.style || 'narrative'})`,
        duration: tl.total_duration || result.total_duration || 10.0,
        width: 1920,
        height: 1080,
        fps: 25.0,
        has_audio: true,
        filepath: firstClip.source_file || '',
      });
    }

    setCurrentTime(0.0);
    setActiveRightTab('inspector');
    setIsEdited(true);
    const cutCount = (result.segments || result.ordered_segments || tl.clips || []).length;
    addChatMessage(
      'assistant',
      `✨ Assembled ${cutCount} sequential cuts into timeline using "${result.style || 'narrative'}".\n• Audio and subtitles synchronized across all cuts.\n• Sequence mounted as editable clips on the timeline.\n• You can now scrub, split, trim, delete, reorder, or refine via natural language chatbot.`
    );
  };

  // Add message helper
  const addChatMessage = useCallback((sender, text, extra = {}) => {
    const newMsg = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      sender,
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      ...extra,
    };
    setChatMessages((prev) => [...prev, newMsg]);
  }, []);

  // 1. Initialize SQLite Default Project on mount
  useEffect(() => {
    async function initProject() {
      try {
        const proj = await createProject('New Project 1');
        setProjectId(proj.id);
        setProjectName(proj.name);
      } catch (err) {
        console.error('Project init error:', err);
      }
    }
    initProject();
  }, []);

  // 2. Autosave periodically if edited
  useEffect(() => {
    if (!isEdited || !projectId) return;

    const timer = setTimeout(async () => {
      try {
        await autosaveProject(projectId, {
          name: projectName,
          settings: { fps: 25.0, resolution: '1080p' },
          clips: timeline.clips,
          subtitles: timeline.subtitles
        });
        setIsEdited(false);
      } catch (e) {
        console.error('Autosave error:', e);
      }
    }, 4000);

    return () => clearTimeout(timer);
  }, [timeline, isEdited, projectId, projectName]);

  // 3. Manual Save Project
  const handleSaveProject = async () => {
    try {
      await saveProject(projectId, {
        name: projectName,
        settings: { fps: 25.0, resolution: '1080p' },
        clips: timeline.clips,
        subtitles: timeline.subtitles
      });
      setIsEdited(false);
      addChatMessage('assistant', `Project "${projectName}" saved to database.`);
    } catch (err) {
      addChatMessage('assistant', `Failed to save: ${err.message}`, { isError: true });
    }
  };

  // 4. Switch Project
  const handleSwitchProject = async (targetId) => {
    try {
      const proj = await getProject(targetId);
      setProjectId(proj.id);
      setProjectName(proj.name);
      setTimeline(proj.timeline);
      setSubtitles(proj.timeline.subtitles || []);
      setIsEdited(false);
      addChatMessage('assistant', `Loaded project "${proj.name}".`);
    } catch (err) {
      console.error(err);
    }
  };

  // 5. Upload Multiple Videos to Media Pool
  const handleUploadVideos = async (files) => {
    try {
      const res = await uploadBatchVideos(files);
      if (!res.items || res.items.length === 0) return;

      const newClips = res.items.map((item) => ({
        id: item.id || `media_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
        filename: item.filename,
        filepath: item.filepath,
        stream_url: item.stream_url,
        metadata: item.metadata
      }));

      setMediaPoolVideos((prev) => [...prev, ...newClips]);
      setSourceClips((prev) => [...prev, ...newClips]);

      // If no active video yet, set first as active
      if (!videoMetadata && newClips.length > 0) {
        const first = newClips[0];
        setVideoMetadata(first.metadata);
        setVideoSrc(first.stream_url);
        setActiveVideoId(first.id);

        if (timeline.clips.length === 0) {
          setTimeline({
            clips: [
              {
                id: `clip_${Date.now()}`,
                source_file: first.filepath,
                source_filename: first.filename,
                source_start: 0.0,
                source_end: first.metadata.duration,
                timeline_start: 0.0,
                timeline_end: first.metadata.duration,
                duration: first.metadata.duration,
                name: first.filename,
                speed: 1.0,
                volume: 1.0,
                stream_url: first.stream_url,
                color: '#2b3a4e'
              }
            ],
            total_duration: first.metadata.duration,
            selected_clip_id: null,
            selection_range: null,
            audio_track: null,
            subtitles: [],
            playhead_time: 0.0
          });
        }
      }

      addChatMessage(
        'assistant',
        `Imported ${newClips.length} video(s) into Media Pool.`
      );
      setIsEdited(true);
    } catch (err) {
      addChatMessage('assistant', `Import error: ${err.message}`, { isError: true });
    }
  };

  // Select video to preview in viewer
  const handleSelectVideo = (clip) => {
    if (!clip || !clip.metadata) return;
    setVideoMetadata(clip.metadata);
    setVideoSrc(clip.stream_url);
    setActiveVideoId(clip.id);
  };

  // Insert a Media Pool video directly into timeline
  const handleInsertVideoToTimeline = (clip) => {
    if (!clip || !clip.metadata) return;
    const curEnd = timeline.total_duration;
    const dur = clip.metadata.duration;
    const newClip = {
      id: `clip_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      source_file: clip.filepath,
      source_filename: clip.filename,
      source_start: 0.0,
      source_end: dur,
      timeline_start: curEnd,
      timeline_end: +(curEnd + dur).toFixed(2),
      duration: dur,
      name: clip.filename,
      speed: 1.0,
      volume: 1.0,
      stream_url: clip.stream_url,
      color: '#2b3a4e'
    };

    setTimeline((prev) => ({
      ...prev,
      clips: [...prev.clips, newClip],
      total_duration: +(curEnd + dur).toFixed(2)
    }));
    setIsEdited(true);
    addChatMessage('assistant', `Appended "${clip.filename}" (${dur.toFixed(1)}s) to timeline.`);
  };

  // Remove individual video from Media Pool
  const handleRemoveMediaPoolVideo = (clipId) => {
    setMediaPoolVideos((prev) => {
      const updated = prev.filter((v) => v.id !== clipId);
      if (activeVideoId === clipId) {
        if (updated.length > 0) {
          setVideoMetadata(updated[0].metadata);
          setVideoSrc(updated[0].stream_url);
          setActiveVideoId(updated[0].id);
        } else {
          setVideoMetadata(null);
          setVideoSrc('');
          setActiveVideoId(null);
        }
      }
      return updated;
    });
    setSourceClips((prev) => prev.filter((c) => c.id !== clipId));
    setIsEdited(true);
  };

  // 6. Upload Audio
  const handleUploadAudio = async (file) => {
    try {
      const res = await uploadAudio(file);
      setAudioTrack(res.audio_track);
      setTimeline((prev) => ({ ...prev, audio_track: res.audio_track }));
      setIsEdited(true);
      addChatMessage('assistant', `Imported audio track "${file.name}".`);
    } catch (err) {
      addChatMessage('assistant', `Audio error: ${err.message}`, { isError: true });
    }
  };

  // 7. Upload Subtitles
  const handleUploadSubtitle = async (file) => {
    try {
      const res = await uploadSubtitle(file);
      setSubtitles(res.subtitles);
      setTimeline((prev) => ({ ...prev, subtitles: res.subtitles }));
      setIsEdited(true);
      addChatMessage('assistant', `Imported ${res.count} subtitle cues from "${file.name}".`);
    } catch (err) {
      addChatMessage('assistant', `Subtitle error: ${err.message}`, { isError: true });
    }
  };

  // 8. Load Sample Project
  const handleLoadSample = async () => {
    try {
      const res = await loadSampleProject();
      setVideoMetadata(res.metadata);
      setTimeline(res.timeline);
      setVideoSrc(res.stream_url);
      setSubtitles(res.timeline.subtitles);
      setCurrentTime(0.0);
      setAnalysis(null);
      setIsEdited(true);

      const sampleItem = {
        id: 'media_sample_demo',
        filename: res.metadata.filename,
        filepath: res.metadata.filepath,
        stream_url: res.stream_url,
        metadata: res.metadata
      };
      setMediaPoolVideos([sampleItem]);
      setActiveVideoId('media_sample_demo');

      addChatMessage(
        'assistant',
        'Loaded demo sample: 30.0s multi-scene video + synchronized SRT subtitles.'
      );
    } catch (err) {
      addChatMessage('assistant', `Failed to load sample: ${err.message}`, { isError: true });
    }
  };

  // 9. Remove media
  const handleRemoveMedia = (type) => {
    if (type === 'video') {
      setVideoMetadata(null);
      setVideoSrc('');
      setActiveVideoId(null);
      setMediaPoolVideos([]);
      setTimeline({ clips: [], total_duration: 0.0, selected_clip_id: null, selection_range: null, subtitles: [], playhead_time: 0 });
      setAnalysis(null);
      setIsEdited(true);
    } else if (type === 'audio') {
      setAudioTrack(null);
      setTimeline((prev) => ({ ...prev, audio_track: null }));
      setIsEdited(true);
    } else if (type === 'subtitles') {
      setSubtitles([]);
      setTimeline((prev) => ({ ...prev, subtitles: [] }));
      setIsEdited(true);
    }
  };

  // 10. Analyze Video
  const handleAnalyze = async () => {
    if (!videoMetadata) return;
    setIsAnalyzing(true);
    setActiveRightTab('inspector');
    try {
      const res = await analyzeVideo(videoMetadata.filepath, videoMetadata.duration);
      setAnalysis(res);
      addChatMessage(
        'assistant',
        `Analysis complete: detected ${res.scenes.length} scene changes, ${res.silences.length} silences, and ${res.low_activity_segments.length} static sections.`
      );
    } catch (err) {
      addChatMessage('assistant', `Analysis error: ${err.message}`, { isError: true });
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 11. Send Chatbot Command with optional LLM config
  const handleSendCommand = async (prompt, llmConfig = null) => {
    addChatMessage('user', prompt);
    setIsChatProcessing(true);

    try {
      const res = await sendChatbotCommand({
        prompt,
        current_timeline: timeline,
        media_metadata: videoMetadata,
        scenes: analysis?.scenes || [],
        llm_config: llmConfig,
      });

      if (res.intent === 'play') {
        setIsPlaying(true);
      } else if (res.intent === 'pause') {
        setIsPlaying(false);
      } else if (res.intent === 'play_selected') {
        if (res.target_range) {
          setPlaybackRange(res.target_range);
          setCurrentTime(res.target_range[0]);
          setIsPlaying(true);
        } else {
          setIsPlaying(true);
        }
      } else if (res.intent === 'show_scenes') {
        setActiveRightTab('inspector');
      } else if (res.intent === 'export') {
        setIsExportOpen(true);
      }

      if (res.updated_timeline) {
        setTimeline(res.updated_timeline);
        setSubtitles(res.updated_timeline.subtitles || []);
        if (res.target_time !== null && res.target_time !== undefined) {
          setCurrentTime(res.target_time);
        }
        setIsEdited(true);
      }

      addChatMessage('assistant', res.message, {
        actionProposal: res.action_proposal,
        actionDescription: res.action_description || (res.updated_timeline ? 'Timeline Updated' : null),
      });
    } catch (err) {
      addChatMessage('assistant', `Error executing command: ${err.message}`, { isError: true });
    } finally {
      setIsChatProcessing(false);
    }
  };

  // 12. Direct Timeline Operations
  const handleSplitAtPlayhead = async (splitTime = currentTime) => {
    try {
      const res = await splitTimeline(timeline, splitTime);
      setTimeline(res.timeline);
      setIsEdited(true);
      addChatMessage('assistant', res.message, { actionDescription: 'Clip Split' });
    } catch (err) {
      addChatMessage('assistant', `Split error: ${err.message}`, { isError: true });
    }
  };

  const handleDelete = async () => {
    try {
      const res = await deleteTimelineSelection(timeline);
      setTimeline(res.timeline);
      setSubtitles(res.timeline.subtitles || []);
      setIsEdited(true);
      addChatMessage('assistant', res.message, { actionDescription: 'Segment Deleted' });
    } catch (err) {
      addChatMessage('assistant', `Delete error: ${err.message}`, { isError: true });
    }
  };

  const handleCut = async () => {
    try {
      const res = await cutTimelineSelection(timeline);
      setTimeline(res.timeline);
      setSubtitles(res.timeline.subtitles || []);
      setIsEdited(true);
      addChatMessage('assistant', res.message, { actionDescription: 'Segment Cut' });
    } catch (err) {
      addChatMessage('assistant', `Cut error: ${err.message}`, { isError: true });
    }
  };

  const handleUndo = async () => {
    try {
      const res = await undoTimelineAction(timeline);
      setTimeline(res.timeline);
      setSubtitles(res.timeline.subtitles || []);
      setIsEdited(true);
      addChatMessage('assistant', res.message, { actionDescription: 'Undo' });
    } catch (err) {
      addChatMessage('assistant', `Undo error: ${err.message}`, { isError: true });
    }
  };

  const handleRedo = async () => {
    try {
      const res = await redoTimelineAction(timeline);
      setTimeline(res.timeline);
      setSubtitles(res.timeline.subtitles || []);
      setIsEdited(true);
      addChatMessage('assistant', res.message, { actionDescription: 'Redo' });
    } catch (err) {
      addChatMessage('assistant', `Redo error: ${err.message}`, { isError: true });
    }
  };

  const handleSelectClip = (clipId) => {
    const clip = timeline.clips.find((c) => c.id === clipId);
    if (!clip) return;
    setTimeline((prev) => ({
      ...prev,
      selected_clip_id: clipId,
      selection_range: [clip.timeline_start, clip.timeline_end],
    }));
    setCurrentTime(clip.timeline_start);
  };

  const handleSeekToScene = (start, end) => {
    setCurrentTime(start);
    setPlaybackRange([start, end]);
    setTimeline((prev) => ({ ...prev, selection_range: [start, end] }));
    setIsPlaying(true);
  };

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;

      if (e.code === 'Space') {
        e.preventDefault();
        setIsPlaying((prev) => !prev);
      } else if (e.key === 's' || e.key === 'S') {
        e.preventDefault();
        handleSplitAtPlayhead();
      } else if (e.key === 'Delete' || e.key === 'Backspace') {
        e.preventDefault();
        handleDelete();
      } else if ((e.ctrlKey || e.metaKey) && (e.key === 'z' || e.key === 'Z')) {
        e.preventDefault();
        if (e.shiftKey) handleRedo();
        else handleUndo();
      } else if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
        e.preventDefault();
        handleSaveProject();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [timeline, currentTime]);

  const selectedClip = (timeline?.clips || []).find((c) => c.id === timeline?.selected_clip_id) || null;

  return (
    <div className="h-screen w-screen flex flex-col bg-[#111215] text-[#b3b7c0] overflow-hidden font-sans">
      {/* 1. DaVinci Resolve Top Navigation & Toolbar */}
      <Navbar
        projectName={projectName}
        onSaveProject={handleSaveProject}
        onNewProject={() => setIsProjectModalOpen(true)}
        onOpenProjectList={() => setIsProjectModalOpen(true)}
        onAnalyze={handleAnalyze}
        isAnalyzing={isAnalyzing}
        onOpenExport={() => setIsExportOpen(true)}
        onOpenAssemblyStage={() => setIsAssemblyStageOpen(true)}
        onLoadSample={handleLoadSample}
        hasMedia={!!videoMetadata}
        activeRightTab={activeRightTab}
        setActiveRightTab={setActiveRightTab}
        isEdited={isEdited}
      />

      {/* 2. Middle Main Workspace (Media Pool | Video Viewer | Inspector/AI) */}
      <div className="flex-1 flex overflow-hidden min-h-0 border-b border-[#212328]">
        {/* Left: Media Pool */}
        <div className="w-80 shrink-0 h-full border-r border-[#212328]">
          <MediaImportPanel
            mediaPoolVideos={mediaPoolVideos}
            activeVideoId={activeVideoId}
            audioTrack={audioTrack}
            subtitles={subtitles}
            onUploadVideos={handleUploadVideos}
            onUploadAudio={handleUploadAudio}
            onUploadSubtitle={handleUploadSubtitle}
            onRemoveVideo={handleRemoveMediaPoolVideo}
            onRemoveMedia={handleRemoveMedia}
            onSelectVideo={handleSelectVideo}
            onInsertVideoToTimeline={handleInsertVideoToTimeline}
          />
        </div>

        {/* Center: Video Viewer */}
        <div className="flex-1 h-full flex flex-col min-w-0">
          <VideoPlayer
            videoSrc={videoSrc}
            timeline={timeline}
            currentTime={currentTime}
            onTimeUpdate={setCurrentTime}
            isPlaying={isPlaying}
            setIsPlaying={setIsPlaying}
            subtitles={subtitles}
            playbackRange={playbackRange}
            onPlaybackComplete={() => setPlaybackRange(null)}
            fps={videoMetadata?.fps || 25}
          />
        </div>

        {/* Right: Inspector & AI Assistant Panel */}
        <div className="w-80 shrink-0 h-full border-l border-[#212328] flex flex-col bg-[#141518]">
          <div className="flex-1 overflow-hidden">
            {activeRightTab === 'inspector' ? (
              <Inspector
                selectedClip={selectedClip}
                timeline={timeline}
                analysis={analysis}
                assemblyResult={assemblyResult}
                onSeekToScene={handleSeekToScene}
                onUpdateClipSpeed={(id, spd) => {
                  setTimeline((prev) => ({
                    ...prev,
                    clips: prev.clips.map((c) => (c.id === id ? { ...c, speed: spd } : c)),
                  }));
                  setIsEdited(true);
                }}
                onUpdateClipVolume={(id, vol) => {
                  setTimeline((prev) => ({
                    ...prev,
                    clips: prev.clips.map((c) => (c.id === id ? { ...c, volume: vol } : c)),
                  }));
                  setIsEdited(true);
                }}
                videoMetadata={videoMetadata}
              />
            ) : (
              <AIChatbotPanel
                chatMessages={chatMessages}
                onSendCommand={handleSendCommand}
                isProcessing={isChatProcessing}
                onSelectSuggestion={(cmd) => handleSendCommand(cmd)}
                onApplyProposal={() => {}}
                onCancelProposal={() => {}}
              />
            )}
          </div>
        </div>
      </div>

      {/* 3. Bottom: DaVinci Multi-Track Timeline */}
      <div className="h-56 shrink-0">
        <InteractiveTimeline
          timeline={timeline}
          currentTime={currentTime}
          onSeek={setCurrentTime}
          onSelectClip={handleSelectClip}
          onSelectRange={(start, end) =>
            setTimeline((prev) => ({ ...prev, selection_range: [start, end] }))
          }
          onSplitAtPlayhead={handleSplitAtPlayhead}
          onDeleteSelection={handleDelete}
          onUndo={handleUndo}
          fps={videoMetadata?.fps || 25}
        />
      </div>

      {/* 4. Bottom DaVinci Page Switcher */}
      <BottomPageBar
        activePage={activePage}
        onSelectPage={(page) => {
          setActivePage(page);
          if (page === 'cut') {
            setIsAssemblyStageOpen(true);
          } else if (page === 'deliver') {
            setIsExportOpen(true);
          }
        }}
      />

      {/* 5. Modals */}
      <MultiVideoAssemblyStage
        isOpen={isAssemblyStageOpen}
        onClose={() => {
          setIsAssemblyStageOpen(false);
          setActivePage('edit');
        }}
        onApplyAssembly={handleApplyAssembly}
        sourceClips={sourceClips}
        setSourceClips={setSourceClips}
        mediaPoolVideos={mediaPoolVideos}
        setMediaPoolVideos={setMediaPoolVideos}
      />

      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        timeline={timeline}
        audioTrack={audioTrack}
        videoMetadata={videoMetadata}
      />

      <ProjectListModal
        isOpen={isProjectModalOpen}
        onClose={() => setIsProjectModalOpen(false)}
        currentProjectId={projectId}
        onSwitchProject={handleSwitchProject}
      />
    </div>
  );
}
