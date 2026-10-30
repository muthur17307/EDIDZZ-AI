import React, { useState } from 'react';
import {
  Sparkles,
  Play,
  VolumeX,
  MessageSquare,
  AlertTriangle,
  Info,
  Clock,
  Layers,
  Activity
} from 'lucide-react';
import { formatTimecode } from '../utils/timeUtils';

export default function VideoAnalysisPanel({
  analysis,
  onSeekToScene,
  onAnalyze,
  isAnalyzing,
  hasMedia
}) {
  const [activeTab, setActiveTab] = useState('scenes'); // 'scenes', 'speech', 'silence'

  if (!analysis) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 text-center text-slate-400 select-none">
        <Sparkles className="w-10 h-10 text-indigo-400 mb-3 opacity-60" />
        <h3 className="text-sm font-semibold text-slate-200">Video Analysis Not Performed</h3>
        <p className="text-xs text-slate-400 max-w-xs mt-1 mb-4">
          Analyze video to detect scene boundaries, speech dialogue, silences, and visual motion.
        </p>
        <button
          onClick={onAnalyze}
          disabled={!hasMedia || isAnalyzing}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium shadow-md transition disabled:opacity-40"
        >
          {isAnalyzing ? 'Analyzing Media...' : 'Analyze Video'}
        </button>
      </div>
    );
  }

  const { video_metadata, scenes = [], speech_segments = [], silences = [], low_activity_segments = [], limitations = [] } = analysis;

  return (
    <div className="h-full flex flex-col bg-[#141721] text-slate-200 select-none">
      {/* Panel Sub-Tabs */}
      <div className="h-10 px-3 border-b border-[#232936] flex items-center justify-between bg-[#11141c]">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setActiveTab('scenes')}
            className={`px-2.5 py-1 rounded text-xs font-medium transition ${
              activeTab === 'scenes'
                ? 'bg-[#1f2535] text-cyan-400 border border-[#2e374c]'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Scenes ({scenes.length})
          </button>
          <button
            onClick={() => setActiveTab('speech')}
            className={`px-2.5 py-1 rounded text-xs font-medium transition ${
              activeTab === 'speech'
                ? 'bg-[#1f2535] text-indigo-400 border border-[#2e374c]'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Speech ({speech_segments.length})
          </button>
          <button
            onClick={() => setActiveTab('silence')}
            className={`px-2.5 py-1 rounded text-xs font-medium transition ${
              activeTab === 'silence'
                ? 'bg-[#1f2535] text-amber-400 border border-[#2e374c]'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Silences ({silences.length})
          </button>
        </div>

        {/* Quick low-activity badge */}
        {low_activity_segments.length > 0 && (
          <span className="text-[10px] text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 font-medium flex items-center gap-1">
            <Activity className="w-3 h-3" />
            {low_activity_segments.length} Static Segments
          </span>
        )}
      </div>

      {/* Main Tab Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* Transparent Limitations Banner */}
        {limitations.length > 0 && (
          <div className="bg-[#1c1917] border border-amber-500/30 rounded-lg p-2.5 text-[11px] text-amber-300/90 flex items-start gap-2">
            <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-semibold text-amber-300">Analysis Notice:</span>
              {limitations.map((lim, idx) => (
                <p key={idx} className="text-amber-200/80 leading-relaxed">
                  • {lim}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* 1. SCENES TAB */}
        {activeTab === 'scenes' && (
          <div className="space-y-2.5">
            {scenes.map((scene) => (
              <div
                key={scene.scene_id}
                onClick={() => onSeekToScene(scene.start_time, scene.end_time)}
                className="bg-[#181c28] hover:bg-[#202534] border border-[#262c3a] hover:border-cyan-500/40 rounded-lg p-2.5 cursor-pointer transition flex items-center gap-3 group"
              >
                {/* Scene Thumbnail */}
                <div className="w-24 h-14 bg-black rounded overflow-hidden relative shrink-0 border border-[#2a3142]">
                  {scene.thumbnail_url ? (
                    <img
                      src={scene.thumbnail_url}
                      alt={`Scene ${scene.scene_id}`}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-slate-600">
                      <Layers className="w-5 h-5" />
                    </div>
                  )}
                  <span className="absolute bottom-1 right-1 bg-black/80 text-[9px] font-mono text-white px-1 rounded">
                    {scene.duration.toFixed(1)}s
                  </span>
                </div>

                {/* Scene Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-white group-hover:text-cyan-300 transition">
                      Scene {scene.scene_id}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSeekToScene(scene.start_time, scene.end_time);
                      }}
                      className="p-1 rounded bg-[#242b3b] text-slate-400 group-hover:text-cyan-400 hover:bg-cyan-500/20 transition"
                      title="Preview this scene"
                    >
                      <Play className="w-3 h-3" />
                    </button>
                  </div>

                  <p className="text-[11px] font-mono text-cyan-400/90 mt-0.5">
                    {formatTimecode(scene.start_time)} ➔ {formatTimecode(scene.end_time)}
                  </p>

                  <div className="flex items-center gap-1.5 mt-1">
                    {scene.is_low_activity ? (
                      <span className="text-[10px] text-amber-300 bg-amber-500/10 px-1.5 py-0.2 rounded border border-amber-500/20">
                        Low Activity / Presentation
                      </span>
                    ) : (
                      <span className="text-[10px] text-emerald-300 bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/20">
                        Active Motion
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 2. SPEECH TRANSCRIPTION TAB */}
        {activeTab === 'speech' && (
          <div className="space-y-2">
            {speech_segments.length > 0 ? (
              speech_segments.map((sp, idx) => (
                <div
                  key={idx}
                  onClick={() => onSeekToScene(sp.start_time, sp.end_time)}
                  className="bg-[#181c28] hover:bg-[#202534] border border-[#262c3a] rounded-lg p-2.5 cursor-pointer transition"
                >
                  <div className="flex items-center justify-between text-[10px] text-indigo-400 font-mono mb-1">
                    <span>
                      {formatTimecode(sp.start_time)} - {formatTimecode(sp.end_time)}
                    </span>
                    <span className="text-slate-500">Jump to audio</span>
                  </div>
                  <p className="text-xs text-slate-200 italic">"{sp.text}"</p>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-slate-400 text-xs bg-[#181c28] rounded-lg border border-[#262c3a]">
                <MessageSquare className="w-6 h-6 text-slate-600 mx-auto mb-2" />
                <p>No spoken dialogue extracted.</p>
                <p className="text-[11px] text-slate-500 mt-1">
                  Upload an SRT/VTT file or ensure audio has clear speech.
                </p>
              </div>
            )}
          </div>
        )}

        {/* 3. SILENCE & PAUSES TAB */}
        {activeTab === 'silence' && (
          <div className="space-y-2">
            {silences.length > 0 ? (
              silences.map((sil, idx) => (
                <div
                  key={idx}
                  onClick={() => onSeekToScene(sil.start_time, sil.end_time)}
                  className="bg-[#181c28] hover:bg-[#202534] border border-[#262c3a] rounded-lg p-2.5 cursor-pointer transition flex items-center justify-between"
                >
                  <div className="flex items-center gap-2">
                    <VolumeX className="w-4 h-4 text-amber-400" />
                    <div>
                      <p className="text-xs font-medium text-white">Silence Segment {idx + 1}</p>
                      <p className="text-[10px] text-slate-400 font-mono">
                        {formatTimecode(sil.start_time)} ➔ {formatTimecode(sil.end_time)}
                      </p>
                    </div>
                  </div>
                  <span className="text-[11px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                    {sil.duration.toFixed(2)}s
                  </span>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-slate-400 text-xs bg-[#181c28] rounded-lg border border-[#262c3a]">
                <VolumeX className="w-6 h-6 text-slate-600 mx-auto mb-2" />
                <p>No long silence periods detected (&gt; 0.8s).</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
