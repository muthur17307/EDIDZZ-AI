import React from 'react';
import { History, Undo2, Redo2, Layers, CheckCircle2 } from 'lucide-react';
import { formatTimecode } from '../utils/timeUtils';

export default function HistoryPanel({
  timeline,
  onUndo,
  onRedo,
  historyLog = []
}) {
  const clips = timeline?.clips || [];

  return (
    <div className="h-full flex flex-col bg-[#141721] text-slate-200 select-none">
      {/* Panel Header */}
      <div className="h-10 px-3.5 border-b border-[#232936] flex items-center justify-between bg-[#11141c]">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Edit History & EDL
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={onUndo}
            className="p-1 rounded bg-[#1e2330] hover:bg-[#283042] text-slate-300 transition"
            title="Undo"
          >
            <Undo2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onRedo}
            className="p-1 rounded bg-[#1e2330] hover:bg-[#283042] text-slate-300 transition"
            title="Redo"
          >
            <Redo2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* 1. Operation History Log */}
        <div>
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Recent Actions
          </p>
          <div className="space-y-1.5">
            {historyLog.length > 0 ? (
              historyLog.map((item, idx) => (
                <div
                  key={idx}
                  className="bg-[#181c28] border border-[#252b3a] rounded p-2 text-xs flex items-center justify-between"
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                    <span className="text-slate-200 font-medium">{item.action}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">{item.time}</span>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500 italic p-2 bg-[#181c28] rounded border border-[#252b3a]">
                No edits performed yet. Split, cut, or delete to see history stack.
              </p>
            )}
          </div>
        </div>

        {/* 2. Active Edit Decision List (EDL) */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
              <span>Active Timeline EDL ({clips.length} Clips)</span>
            </p>
          </div>

          <div className="space-y-1.5">
            {clips.map((clip, idx) => (
              <div
                key={clip.id}
                className="bg-[#181c28] border border-[#252b3a] rounded p-2 text-[11px] font-mono space-y-1"
              >
                <div className="flex items-center justify-between text-white font-semibold">
                  <span className="truncate max-w-[170px]">{idx + 1}. {clip.name}</span>
                  <span className="text-cyan-400">{clip.duration.toFixed(2)}s</span>
                </div>
                <div className="flex justify-between text-slate-400 text-[10px]">
                  <span>Timeline: {formatTimecode(clip.timeline_start)} - {formatTimecode(clip.timeline_end)}</span>
                </div>
                <div className="flex justify-between text-slate-500 text-[10px]">
                  <span>Source: {formatTimecode(clip.source_start)} - {formatTimecode(clip.source_end)}</span>
                  <span>{clip.speed}x speed</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
