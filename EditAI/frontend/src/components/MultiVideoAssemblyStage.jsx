import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  Upload,
  Film,
  FolderOpen,
  CheckCircle2,
  AlertCircle,
  Play,
  ArrowRight,
  Layers,
  Sliders,
  Scissors,
  Trash2,
  X,
  Download,
  FileCode,
  FileText,
  Clock,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Eye,
  Check,
  ChevronRight
} from 'lucide-react';
import { formatSMPTE, formatTimecode } from '../utils/timeUtils';
import {
  uploadBatchVideos,
  loadMultiSamplePack,
  createPipelineProject,
  runPipelineOnExisting,
  runPipelineSamplePack
} from '../api';

export default function MultiVideoAssemblyStage({
  isOpen,
  onClose,
  onApplyAssembly,
  sourceClips = [],
  setSourceClips,
  mediaPoolVideos = [],
  setMediaPoolVideos
}) {
  // Navigation & View tabs
  const [activeTab, setActiveTab] = useState('setup'); // 'setup' | 'progress' | 'review'
  const [selectedStyle, setSelectedStyle] = useState('narrative');
  const [clientBrief, setClientBrief] = useState(
    'Create a cohesive narrative highlight edit that establishes the speaker intro, cuts to dynamic action b-roll, delivers the core message, and concludes with a scenic outro.'
  );

  // Real Processing Progress state
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [progressDetails, setProgressDetails] = useState('');

  // Results & Error state
  const [pipelineResult, setPipelineResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [activeReviewTab, setActiveReviewTab] = useState('ordered'); // 'ordered' | 'review_items' | 'manifests'

  // Uploading & Drag/Drop state
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const batchInputRef = useRef(null);
  const progressTimerRef = useRef(null);

  const pipelineStages = [
    { id: 'ingest', name: 'Media Ingestion & Validation', desc: 'Validating video formats, durations, frame rates & codec integrity' },
    { id: 'analysis', name: 'Multimodal Feature Extraction', desc: 'Running scene boundary detection, visual motion scoring & audio silence analysis' },
    { id: 'planning', name: 'Global Story Planning (Offline AI)', desc: 'Analyzing brief, evaluating cross-clip repetition & structuring narrative beats' },
    { id: 'validate', name: 'Timing & Boundary Validation', desc: 'Validating source IDs, timestamp ranges, minimum durations & clamping bounds' },
    { id: 'export', name: 'Editable Timeline & OTIO Generation', desc: 'Building OpenTimelineIO manifest, mapping caption tracks & interactive clips' }
  ];

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);
    };
  }, []);

  if (!isOpen) return null;

  // Delete a specific clip from assembly tray
  const handleDeleteClip = (indexToDelete) => {
    setSourceClips((prev) => prev.filter((_, idx) => idx !== indexToDelete));
    setPipelineResult(null);
  };

  // Clear all clips
  const handleClearAllClips = () => {
    setSourceClips([]);
    setPipelineResult(null);
  };

  // Import existing media pool clips into assembly
  const handleImportFromMediaPool = () => {
    if (!mediaPoolVideos || mediaPoolVideos.length === 0) return;
    setSourceClips((prev) => {
      const existingPaths = new Set(prev.map((c) => c.filepath));
      const newItems = mediaPoolVideos.filter((v) => !existingPaths.has(v.filepath));
      return [...prev, ...newItems];
    });
  };

  // Handle multi-clip batch upload (via file picker or drag-and-drop)
  const handleBatchUpload = async (e) => {
    let files = null;
    if (e && e.target && e.target.files) {
      files = e.target.files;
    } else if (e && e.dataTransfer && e.dataTransfer.files) {
      files = e.dataTransfer.files;
    } else if (e instanceof FileList || Array.isArray(e)) {
      files = e;
    }

    if (!files || files.length === 0) return;

    try {
      setIsUploading(true);
      setErrorMsg('');
      const res = await uploadBatchVideos(files);
      if (res && res.items && res.items.length > 0) {
        const formattedClips = res.items.map((item) => ({
          id: item.id || `media_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
          filename: item.filename,
          filepath: item.filepath,
          stream_url: item.stream_url,
          metadata: item.metadata || {
            filename: item.filename,
            filepath: item.filepath,
            duration: 10.0,
            width: 1920,
            height: 1080,
            fps: 30.0,
            has_audio: true
          },
          analysis: null
        }));

        setSourceClips((prev) => {
          const existingPaths = new Set(prev.map((c) => c.filepath));
          const toAdd = formattedClips.filter((c) => !existingPaths.has(c.filepath));
          return [...prev, ...toAdd];
        });

        if (setMediaPoolVideos) {
          setMediaPoolVideos((prev) => {
            const existingPaths = new Set(prev.map((c) => c.filepath));
            const toAdd = formattedClips.filter((c) => !existingPaths.has(c.filepath));
            return [...prev, ...toAdd];
          });
        }
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to upload batch clips.');
    } finally {
      setIsUploading(false);
      if (batchInputRef.current) {
        batchInputRef.current.value = '';
      }
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await handleBatchUpload(e.dataTransfer.files);
    }
  };

  // Load 3-clip demo pack
  const handleLoadDemoPack = async () => {
    try {
      setErrorMsg('');
      const res = await loadMultiSamplePack();
      const items = res.clip_analyses.map((a) => ({
        filename: a.filename,
        filepath: a.filepath,
        stream_url: `/media_files/sample_media/${a.filename}`,
        metadata: {
          filename: a.filename,
          filepath: a.filepath,
          duration: a.duration,
          width: a.width,
          height: a.height,
          fps: a.fps,
          has_audio: a.has_audio
        },
        analysis: a
      }));
      setSourceClips(items);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load sample pack.');
    }
  };

  // Simulate or track smooth stage progress during AI processing
  const startProgressTracking = () => {
    setIsProcessing(true);
    setProgressPercent(8);
    setCurrentStageIndex(0);
    setProgressDetails('Ingesting and probing source media files...');

    let current = 8;
    progressTimerRef.current = setInterval(() => {
      current += Math.floor(Math.random() * 4) + 2;
      if (current >= 94) {
        current = 94;
        clearInterval(progressTimerRef.current);
      }
      setProgressPercent(current);

      if (current < 25) {
        setCurrentStageIndex(0);
        setProgressDetails('Ingesting and probing source media files...');
      } else if (current < 55) {
        setCurrentStageIndex(1);
        setProgressDetails('Detecting scenes, visual motion scores, and audio features...');
      } else if (current < 80) {
        setCurrentStageIndex(2);
        setProgressDetails('Qwen / Offline AI model synthesizing cross-clip story plan...');
      } else if (current < 90) {
        setCurrentStageIndex(3);
        setProgressDetails('Validating source IDs, duration constraints, and clamping bounds...');
      } else {
        setCurrentStageIndex(4);
        setProgressDetails('Generating OpenTimelineIO (.otio) manifest and interactive timeline...');
      }
    }, 450);
  };

  const stopProgressTracking = (success = true) => {
    if (progressTimerRef.current) clearInterval(progressTimerRef.current);
    if (success) {
      setProgressPercent(100);
      setCurrentStageIndex(5);
      setProgressDetails('Pipeline execution successfully completed!');
    }
    setIsProcessing(false);
  };

  // Run the complete AI video-analysis pipeline
  const handleRunPipeline = async () => {
    if (sourceClips.length === 0) {
      setErrorMsg('Please upload or load at least one video clip before running the pipeline.');
      return;
    }
    if (!clientBrief.trim()) {
      setErrorMsg('Please provide a client brief or editing instructions.');
      return;
    }

    try {
      setErrorMsg('');
      setActiveTab('progress');
      startProgressTracking();

      const paths = sourceClips.map((c) => c.filepath || c.source_file || c.filename).filter(Boolean);
      const res = await runPipelineOnExisting({
        brief: clientBrief.trim(),
        media_files: paths,
        style: selectedStyle
      });

      setPipelineResult(res);
      stopProgressTracking(true);
      setActiveTab('review');
    } catch (err) {
      stopProgressTracking(false);
      setErrorMsg(err.message || 'Pipeline processing failed.');
      setActiveTab('setup');
    }
  };

  // Mount to interactive timeline
  const handleCommitToTimeline = () => {
    if (!pipelineResult) return;
    onApplyAssembly(pipelineResult);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-xs flex items-center justify-center p-4 select-none text-[12px] text-[#a0a4ae]">
      <div className="bg-[#141518] border border-[#2b2d35] rounded-lg max-w-5xl w-full h-[90vh] overflow-hidden shadow-2xl flex flex-col">
        {/* 1. DaVinci Header */}
        <div className="h-11 px-4 border-b border-[#212328] flex items-center justify-between bg-[#16171b]">
          <div className="flex items-center gap-3">
            <span className="w-2.5 h-2.5 rounded-full bg-[#d4483b] shadow-sm shadow-[#d4483b]/40" />
            <span className="font-semibold text-[#e1e4ed] text-xs tracking-wide">
              AI Video-Analysis & Story Planning Pipeline
            </span>
            <span className="text-[10px] text-[#6b707e] font-mono border-l border-[#24262c] pl-2.5">
              OpenTimelineIO & Offline Qwen Engine
            </span>
          </div>

          {/* Navigation Pill Switcher */}
          <div className="flex items-center bg-[#101114] border border-[#23252c] rounded-md p-0.5">
            <button
              onClick={() => setActiveTab('setup')}
              className={`px-3 py-1 rounded text-[11px] font-medium transition ${activeTab === 'setup'
                  ? 'bg-[#22252e] text-[#e0e3ec] shadow-xs'
                  : 'text-[#6b707d] hover:text-[#a0a4b0]'
                }`}
            >
              1. Source Clips & Brief
            </button>
            <button
              onClick={() => setActiveTab('progress')}
              disabled={!isProcessing && !pipelineResult}
              className={`px-3 py-1 rounded text-[11px] font-medium transition ${activeTab === 'progress'
                  ? 'bg-[#22252e] text-[#e0e3ec] shadow-xs'
                  : 'text-[#6b707d] hover:text-[#a0a4b0] disabled:opacity-40'
                }`}
            >
              2. Processing Progress
            </button>
            <button
              onClick={() => setActiveTab('review')}
              disabled={!pipelineResult}
              className={`px-3 py-1 rounded text-[11px] font-medium transition ${activeTab === 'review'
                  ? 'bg-[#22252e] text-[#e0e3ec] shadow-xs'
                  : 'text-[#6b707d] hover:text-[#a0a4b0] disabled:opacity-40'
                }`}
            >
              3. Edit-Plan Review
            </button>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded text-[#6f7482] hover:text-[#d0d3dc] hover:bg-[#252830] transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 2. Main Workspace Body */}
        <div className="flex-1 flex overflow-hidden min-h-0">
          {/* TAB 1: SETUP (Source Media & Client Brief) */}
          {activeTab === 'setup' && (
            <div className="flex-1 flex overflow-hidden">
              {/* Left Column: Source Media Tray */}
              <div 
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`w-80 shrink-0 border-r border-[#212328] flex flex-col bg-[#121316] relative transition ${
                  isDragging ? 'ring-2 ring-[#3b82d4] bg-[#161c28]' : ''
                }`}
              >
                <div className="h-8 px-3 border-b border-[#212328] flex items-center justify-between bg-[#16171a] text-[11px]">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-[#c8cbcd]">Source Media ({sourceClips.length})</span>
                    {isUploading && (
                      <RefreshCw className="w-3 h-3 text-[#7ea5dc] animate-spin" />
                    )}
                  </div>
                  <div className="flex items-center gap-1.5">
                    {mediaPoolVideos && mediaPoolVideos.length > 0 && (
                      <button
                        onClick={handleImportFromMediaPool}
                        disabled={isUploading}
                        className="px-2 py-0.5 rounded bg-[#1e232d] hover:bg-[#283242] text-[#86a6d6] border border-[#2b394e] transition text-[10px] disabled:opacity-50"
                        title="Add clips already in Media Pool"
                      >
                        + From Pool
                      </button>
                    )}
                    <button
                      onClick={() => batchInputRef.current?.click()}
                      disabled={isUploading}
                      className="px-2 py-0.5 rounded bg-[#202734] hover:bg-[#2a3648] text-[#8cb3ed] border border-[#344866] transition text-[10px] font-medium flex items-center gap-1 disabled:opacity-50"
                      title="Upload multiple video files from your computer"
                    >
                      <Upload className="w-2.5 h-2.5" />
                      <span>+ Add Clips</span>
                    </button>
                    {sourceClips.length > 0 && (
                      <button
                        onClick={handleClearAllClips}
                        disabled={isUploading}
                        className="px-1.5 py-0.5 rounded hover:bg-[#2a1d20] text-[#868a96] hover:text-[#e06c75] border border-transparent hover:border-[#42252a] transition text-[10px] disabled:opacity-50"
                        title="Remove all source clips"
                      >
                        Clear
                      </button>
                    )}
                  </div>
                </div>

                {isUploading && (
                  <div className="bg-[#1b2535] border-b border-[#2b3e58] px-3 py-1.5 text-[10px] flex items-center gap-2 text-[#8cb3ed]">
                    <RefreshCw className="w-3 h-3 animate-spin shrink-0" />
                    <span className="truncate">Uploading & probing video clips...</span>
                  </div>
                )}

                <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
                  {sourceClips.length === 0 ? (
                    <div 
                      onClick={() => !isUploading && batchInputRef.current?.click()}
                      className={`h-full flex flex-col items-center justify-center text-center p-4 border border-dashed rounded cursor-pointer transition ${
                        isDragging
                          ? 'border-[#3b82d4] bg-[#1a2332]'
                          : 'border-[#2a2d36] hover:border-[#3d4556] bg-[#15161b]'
                      }`}
                    >
                      {isUploading ? (
                        <div className="flex flex-col items-center gap-2">
                          <RefreshCw className="w-7 h-7 text-[#7ea5dc] animate-spin" />
                          <p className="text-[#d8dbe4] text-[12px] font-medium">Uploading video clips...</p>
                          <span className="text-[10px] text-[#636774]">Probing frame rates and metadata</span>
                        </div>
                      ) : (
                        <>
                          <div className="w-10 h-10 rounded-full bg-[#1e222b] border border-[#2e3442] flex items-center justify-center mb-2.5">
                            <Upload className="w-5 h-5 text-[#86a6d6]" />
                          </div>
                          <p className="text-[#d8dbe4] text-[12px] font-medium mb-1">
                            Upload Multiple Video Clips
                          </p>
                          <p className="text-[#6c7180] text-[10px] mb-3 max-w-[200px] leading-tight">
                            Drag & drop multiple videos here, or click to browse files
                          </p>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              batchInputRef.current?.click();
                            }}
                            className="px-3 py-1.5 rounded bg-[#202734] hover:bg-[#2b3548] text-[#8cb3ed] border border-[#344866] transition text-[11px] font-medium flex items-center gap-1.5 mb-2 shadow-xs"
                          >
                            <Upload className="w-3.5 h-3.5" />
                            <span>Browse Files (Select Multiple)</span>
                          </button>

                          {mediaPoolVideos && mediaPoolVideos.length > 0 && (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleImportFromMediaPool();
                              }}
                              className="px-2.5 py-1 rounded bg-[#1b1d24] hover:bg-[#232630] text-[#a0a4b2] border border-[#2b2e38] transition text-[10px] mb-2"
                            >
                              + Add from Media Pool ({mediaPoolVideos.length})
                            </button>
                          )}

                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleLoadDemoPack();
                            }}
                            className="text-[10px] text-[#717684] hover:text-[#9ea4b4] underline underline-offset-2 transition"
                          >
                            Or load 3-clip demo pack
                          </button>
                        </>
                      )}
                    </div>
                  ) : (
                    sourceClips.map((clip, idx) => (
                      <div
                        key={idx}
                        className="bg-[#18191d] border border-[#25272e] rounded p-2 text-[11px] space-y-1 hover:border-[#383b46] transition group"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-[#d8dbe4] truncate max-w-[155px]" title={clip.filename}>
                            {idx + 1}. {clip.filename}
                          </span>
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] font-mono text-[#8a8f9e]">
                              {clip.metadata?.duration ? formatTimecode(clip.metadata.duration) : '--'}
                            </span>
                            <button
                              onClick={() => handleDeleteClip(idx)}
                              className="p-1 rounded text-[#555a66] hover:text-[#e06c75] hover:bg-[#271d20] transition opacity-0 group-hover:opacity-100"
                              title="Remove this video from assembly"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        </div>

                        <div className="flex items-center gap-1 text-[9px]">
                          {clip.analysis?.primary_category ? (
                            <span className="px-1.5 py-0.2 rounded bg-[#202734] text-[#7ea5dc] border border-[#29364a] font-mono">
                              {clip.analysis.primary_category}
                            </span>
                          ) : (
                            <span className="px-1.5 py-0.2 rounded bg-[#1d1f25] text-[#868a96] border border-[#272932] font-mono">
                              Video Clip
                            </span>
                          )}
                          <span className="text-[#636774] font-mono">
                            {clip.metadata?.width ? `${clip.metadata.width}x${clip.metadata.height}` : '1080p'}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>

                <input
                  type="file"
                  ref={batchInputRef}
                  onChange={handleBatchUpload}
                  multiple
                  accept="video/*,.mp4,.mov,.webm,.mkv,.avi,.MP4,.MOV,.WEBM,.MKV,.AVI"
                  className="hidden"
                />
              </div>

              {/* Right Column: Brief & Pipeline Parameters */}
              <div className="flex-1 flex flex-col bg-[#141518] p-5 space-y-4 overflow-y-auto">
                <div>
                  <h3 className="text-sm font-semibold text-[#e1e4ed] mb-1">
                    Client Editorial Brief & Goal
                  </h3>
                  <p className="text-[#757a88] text-[11px] mb-2.5">
                    Describe your intended video story. The offline AI model will evaluate all clips simultaneously, filter repetition, and structure a logical narrative.
                  </p>
                  <textarea
                    value={clientBrief}
                    onChange={(e) => setClientBrief(e.target.value)}
                    rows={4}
                    placeholder="Enter editorial instructions, theme, pacing, or client requirements..."
                    className="w-full bg-[#18191e] border border-[#262830] rounded-md p-3 text-[12px] text-[#e0e3ec] placeholder-[#4e5360] focus:outline-none focus:border-[#425066] font-sans leading-relaxed"
                  />
                </div>

                <div>
                  <span className="text-[#8e92a0] text-[11px] font-medium block mb-2">Narrative Arc Preset</span>
                  <div className="grid grid-cols-4 gap-2 text-[11px]">
                    {[
                      { id: 'narrative', label: 'Narrative Highlight Reel', desc: 'Hook -> Action B-Roll -> Value Proposition -> Scenic Outro' },
                      { id: 'social', label: 'Fast-Paced Social Cut', desc: 'Punchy 15-30s kinetic edits optimized for social platforms' },
                      { id: 'broll', label: 'Interview + B-Roll Assembly', desc: 'Speaker anchor with illustrative visual cutaways' },
                      { id: 'chronological', label: 'Chronological Story Cut', desc: 'Follows natural progression with trimmed static pauses' }
                    ].map((s) => (
                      <button
                        key={s.id}
                        onClick={() => setSelectedStyle(s.id)}
                        className={`p-2.5 rounded-md border text-left transition flex flex-col justify-between ${selectedStyle === s.id
                            ? 'bg-[#212733] border-[#3f5778] text-[#e0e3eb]'
                            : 'bg-[#18191e] border-[#24262e] text-[#777b87] hover:text-[#b8bcc8] hover:border-[#30333d]'
                          }`}
                      >
                        <span className="font-medium text-[11px] text-[#d8dbe4] mb-1">{s.label}</span>
                        <span className="text-[10px] text-[#696e7d] leading-tight">{s.desc}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Workflow Architecture Overview */}
                <div className="bg-[#17181d] border border-[#24262e] rounded-md p-3.5 space-y-2">
                  <span className="text-[11px] font-semibold text-[#8b909e] uppercase tracking-wider block">
                    Automated 5-Stage Pipeline Workflow
                  </span>
                  <div className="grid grid-cols-5 gap-2 text-[10px]">
                    {pipelineStages.map((stg, i) => (
                      <div key={stg.id} className="bg-[#121316] border border-[#1e2026] rounded p-2 space-y-1">
                        <span className="text-[#555a66] font-mono">Stage {i + 1}</span>
                        <p className="font-medium text-[#c0c4ce] leading-tight">{stg.name}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {errorMsg && (
                  <div className="bg-[#2a1d1f] border border-[#442327] p-2.5 rounded-md text-[#e28b8b] text-[11px] flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{errorMsg}</span>
                  </div>
                )}

                <div className="pt-2 flex items-center justify-between">
                  <span className="text-[11px] text-[#626774]">
                    {sourceClips.length} source clip(s) ready for ingestion & global analysis
                  </span>
                  <button
                    onClick={handleRunPipeline}
                    disabled={sourceClips.length === 0}
                    className="px-5 py-2 rounded-md bg-[#2d3a4d] hover:bg-[#394a63] border border-[#445b7e] text-[#e6e9f2] font-medium transition text-[12px] flex items-center gap-2 disabled:opacity-40 shadow-sm"
                  >
                    <Sparkles className="w-4 h-4 text-[#d48b3b]" />
                    <span>Run AI Video Pipeline</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: REAL PROCESSING PROGRESS */}
          {activeTab === 'progress' && (
            <div className="flex-1 flex flex-col bg-[#141518] p-6 space-y-6 overflow-y-auto">
              <div className="border-b border-[#212328] pb-4">
                <h3 className="text-sm font-semibold text-[#e1e4ed]">
                  {isProcessing ? 'AI Video Pipeline In Progress' : 'Pipeline Execution Complete'}
                </h3>
                <p className="text-[#757a88] text-[11px] mt-0.5">
                  {progressDetails}
                </p>
              </div>

              {/* Live Progress Bar */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-[#8c919e]">Overall Pipeline Completion</span>
                  <span className="text-[#d48b3b] font-bold">{progressPercent}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-[#1b1d22] overflow-hidden border border-[#262830]">
                  <div
                    className="h-full bg-gradient-to-r from-[#3b5982] via-[#d48b3b] to-[#5bb676] transition-all duration-300"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>

              {/* Step by Step Stage Indicators */}
              <div className="space-y-2.5">
                {pipelineStages.map((stg, idx) => {
                  const isDone = currentStageIndex > idx || (!isProcessing && pipelineResult);
                  const isCurrent = currentStageIndex === idx && isProcessing;
                  return (
                    <div
                      key={stg.id}
                      className={`p-3 rounded-md border transition flex items-start gap-3 ${isCurrent
                          ? 'bg-[#1b2029] border-[#3f5778] shadow-xs'
                          : isDone
                            ? 'bg-[#15171b] border-[#22252c]'
                            : 'bg-[#121316] border-[#1c1d22] opacity-50'
                        }`}
                    >
                      <div className="mt-0.5">
                        {isDone ? (
                          <CheckCircle2 className="w-4 h-4 text-[#5bb676]" />
                        ) : isCurrent ? (
                          <RefreshCw className="w-4 h-4 text-[#d48b3b] animate-spin" />
                        ) : (
                          <span className="w-4 h-4 rounded-full border border-[#3b3e48] flex items-center justify-center font-mono text-[9px] text-[#555a66]">
                            {idx + 1}
                          </span>
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className={`font-medium text-[11px] ${isCurrent ? 'text-[#e0e3ec]' : isDone ? 'text-[#c0c4ce]' : 'text-[#696e7d]'}`}>
                            Stage {idx + 1}: {stg.name}
                          </span>
                          <span className="text-[10px] font-mono text-[#5b606c]">
                            {isDone ? 'Completed' : isCurrent ? 'Running...' : 'Pending'}
                          </span>
                        </div>
                        <p className="text-[10px] text-[#696e7d] mt-0.5">{stg.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Action Buttons */}
              <div className="pt-4 flex items-center justify-between border-t border-[#212328]">
                <button
                  onClick={() => setActiveTab('setup')}
                  className="px-3.5 py-1.5 rounded bg-[#1e2026] hover:bg-[#282a32] text-[#9ca0ae] text-[11px] transition"
                >
                  Back to Setup
                </button>
                {pipelineResult && (
                  <button
                    onClick={() => setActiveTab('review')}
                    className="px-5 py-2 rounded bg-[#2e3c50] hover:bg-[#394a63] border border-[#445b7e] text-[#e6e9f2] font-medium text-[11px] transition flex items-center gap-1.5 shadow-sm"
                  >
                    <span>Proceed to Edit-Plan Review</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: EDIT-PLAN REVIEW */}
          {activeTab === 'review' && pipelineResult && (
            <div className="flex-1 flex flex-col bg-[#141518] overflow-hidden">
              {/* Review Sub-Header */}
              <div className="p-3 border-b border-[#212328] bg-[#16171b] flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div>
                    <span className="text-[10px] text-[#696e7d] block font-mono">STORY SUMMARY</span>
                    <p className="text-[11px] text-[#d8dbe4] max-w-xl font-medium truncate" title={pipelineResult.story_summary}>
                      {pipelineResult.story_summary}
                    </p>
                  </div>
                  <div className="border-l border-[#24262c] pl-3 font-mono text-[11px]">
                    <span className="text-[#696e7d]">Duration: </span>
                    <span className="text-[#d48b3b] font-medium">
                      {pipelineResult.timeline_state?.total_duration || 0}s
                    </span>
                  </div>
                </div>

                {/* Sub-tab pills */}
                <div className="flex items-center bg-[#101114] border border-[#23252c] rounded p-0.5 text-[11px]">
                  <button
                    onClick={() => setActiveReviewTab('ordered')}
                    className={`px-2.5 py-1 rounded transition ${activeReviewTab === 'ordered'
                        ? 'bg-[#22252e] text-[#e0e3ec] font-medium'
                        : 'text-[#696e7d] hover:text-[#a0a4ae]'
                      }`}
                  >
                    Accepted Cuts ({pipelineResult.ordered_segments?.length || 0})
                  </button>
                  <button
                    onClick={() => setActiveReviewTab('review_items')}
                    className={`px-2.5 py-1 rounded transition flex items-center gap-1 ${activeReviewTab === 'review_items'
                        ? 'bg-[#22252e] text-[#e0e3ec] font-medium'
                        : 'text-[#696e7d] hover:text-[#a0a4ae]'
                      }`}
                  >
                    <span>Flagged Takes ({pipelineResult.review_segments?.length || pipelineResult.review_items || 0})</span>
                    {(pipelineResult.review_segments?.length || 0) > 0 && (
                      <span className="w-1.5 h-1.5 rounded-full bg-[#d48b3b]" />
                    )}
                  </button>
                  <button
                    onClick={() => setActiveReviewTab('manifests')}
                    className={`px-2.5 py-1 rounded transition ${activeReviewTab === 'manifests'
                        ? 'bg-[#22252e] text-[#e0e3ec] font-medium'
                        : 'text-[#696e7d] hover:text-[#a0a4ae]'
                      }`}
                  >
                    OTIO & Manifests
                  </button>
                </div>
              </div>

              {/* Review Tab 1: Ordered / Accepted Segments */}
              {activeReviewTab === 'ordered' && (
                <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
                  {pipelineResult.ordered_segments?.map((seg, idx) => {
                    const dur = +(seg.end - seg.start).toFixed(2);
                    return (
                      <div
                        key={idx}
                        className="bg-[#18191d] border border-[#25272e] rounded-md p-3 text-[11px] space-y-1.5 hover:border-[#393d4a] transition"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded bg-[#202228] text-[#a0a4ae] flex items-center justify-center font-mono text-[10px]">
                              {idx + 1}
                            </span>
                            <span className="font-semibold text-[#d8dbe4]">
                              {seg.story_role ? seg.story_role.replace('_', ' ').toUpperCase() : 'NARRATIVE CUT'}
                            </span>
                            <span className="px-1.5 py-0.2 rounded bg-[#202734] text-[#7ea5dc] border border-[#29364a] text-[9px] font-mono">
                              {seg.clip_id}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 font-mono text-[10px] text-[#8a8f9e]">
                            <span>Source: {seg.start}s - {seg.end}s</span>
                            <span className="text-[#555a66]">|</span>
                            <span className="text-[#d48b3b]">Dur: {dur}s</span>
                          </div>
                        </div>

                        <p className="text-[#9da1ad] leading-relaxed pl-7">
                          {seg.reason}
                        </p>

                        {seg.trimmed_reason && (
                          <p className="text-[10px] text-[#717582] italic pl-7">
                            • Trimmed rationale: {seg.trimmed_reason}
                          </p>
                        )}

                        {seg.transcript && (
                          <div className="pl-7 text-[10px] font-mono text-[#d4a03b] flex items-center gap-1">
                            <span>Caption text: "{seg.transcript}"</span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Review Tab 2: Flagged Takes / Review Items */}
              {activeReviewTab === 'review_items' && (
                <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
                  {(pipelineResult.review_segments?.length || 0) === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center p-6 text-[#555a66]">
                      <ShieldCheck className="w-8 h-8 text-[#5bb676] mb-2" />
                      <p className="text-xs text-[#d8dbe4] font-medium">All Segments Validated Cleanly</p>
                      <p className="text-[11px] text-[#555a66] mt-0.5 max-w-sm">
                        No segments required review or duration warnings. Every proposed take passed boundary validation.
                      </p>
                    </div>
                  ) : (
                    pipelineResult.review_segments.map((item, idx) => (
                      <div
                        key={idx}
                        className="bg-[#1b191a] border border-[#38272b] rounded-md p-3 text-[11px] space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4 text-[#d48b3b]" />
                            <span className="font-medium text-[#e0a89d]">
                              Flagged Review Item #{idx + 1}
                            </span>
                            {item.clip_id && (
                              <span className="px-1.5 py-0.2 rounded bg-[#2b1f22] text-[#d68694] border border-[#44282e] text-[9px] font-mono">
                                {item.clip_id}
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] font-mono text-[#8a8f9e]">
                            Range: {item.start || 0}s - {item.end || 0}s
                          </span>
                        </div>

                        <p className="text-[#bfa4a6] leading-relaxed pl-6">
                          {item.reason || 'Flagged for editorial inspection.'}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Review Tab 3: OpenTimelineIO & Manifests */}
              {activeReviewTab === 'manifests' && (
                <div className="flex-1 overflow-y-auto p-5 space-y-4">
                  <div className="bg-[#18191d] border border-[#25272e] rounded-md p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <FileCode className="w-5 h-5 text-[#86a6d6]" />
                        <div>
                          <h4 className="font-medium text-[#d8dbe4] text-xs">OpenTimelineIO Editable Timeline (.otio)</h4>
                          <p className="text-[10px] text-[#696e7d]">
                            Universal NLE interchange format compatible with DaVinci Resolve, Premiere Pro, and Final Cut Pro.
                          </p>
                        </div>
                      </div>
                      <a
                        href={pipelineResult.timeline_url || `/projects/${pipelineResult.project_id}/timeline`}
                        download="timeline.otio"
                        className="px-3 py-1.5 rounded bg-[#202734] hover:bg-[#2b394e] border border-[#3b4e6b] text-[#9fc0f0] text-[11px] font-medium transition flex items-center gap-1.5"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download .otio</span>
                      </a>
                    </div>
                  </div>

                  <div className="bg-[#18191d] border border-[#25272e] rounded-md p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <FileText className="w-5 h-5 text-[#d48b3b]" />
                        <div>
                          <h4 className="font-medium text-[#d8dbe4] text-xs">Validated Edit Plan (edit_plan.json)</h4>
                          <p className="text-[10px] text-[#696e7d]">
                            Structured JSON containing ordered narrative segments, selection rationales, and review items.
                          </p>
                        </div>
                      </div>
                      <a
                        href={pipelineResult.edit_plan_url || `/projects/${pipelineResult.project_id}/edit-plan`}
                        download="edit_plan.json"
                        className="px-3 py-1.5 rounded bg-[#2b251d] hover:bg-[#3b3225] border border-[#5a4831] text-[#e0b070] text-[11px] font-medium transition flex items-center gap-1.5"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download edit_plan.json</span>
                      </a>
                    </div>
                  </div>

                  <div className="bg-[#18191d] border border-[#25272e] rounded-md p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <Layers className="w-5 h-5 text-[#5bb676]" />
                        <div>
                          <h4 className="font-medium text-[#d8dbe4] text-xs">Multi-Clip Story Context (story_context.json)</h4>
                          <p className="text-[10px] text-[#696e7d]">
                            Consolidated multimodal clip analyses, role groupings, and editorial instructions.
                          </p>
                        </div>
                      </div>
                      <a
                        href={pipelineResult.story_context_url || `/projects/${pipelineResult.project_id}/story-context`}
                        download="story_context.json"
                        className="px-3 py-1.5 rounded bg-[#1d2720] hover:bg-[#25362a] border border-[#34523c] text-[#78c991] text-[11px] font-medium transition flex items-center gap-1.5"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download story_context.json</span>
                      </a>
                    </div>
                  </div>
                </div>
              )}

              {/* 3. Footer Actions */}
              <div className="h-12 px-4 border-t border-[#212328] bg-[#16171a] flex items-center justify-between">
                <span className="text-[11px] text-[#696e7d]">
                  {pipelineResult.ordered_segments?.length || 0} cuts validated and ready for interactive timeline editing
                </span>
                <div className="flex items-center gap-2.5">
                  <button
                    onClick={() => setActiveTab('setup')}
                    className="px-3 py-1.5 rounded bg-[#202228] hover:bg-[#282a32] text-[#9da1ad] transition text-[11px]"
                  >
                    Adjust Setup
                  </button>
                  <button
                    onClick={handleCommitToTimeline}
                    className="px-4 py-1.5 rounded bg-[#2a3848] hover:bg-[#34465a] border border-[#445b78] text-[#e0e3eb] font-medium transition text-[11px] flex items-center gap-1.5 shadow-sm"
                  >
                    <Check className="w-3.5 h-3.5 text-[#5bb676]" />
                    <span>Apply to Timeline & Open Editor</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
