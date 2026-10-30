import React from 'react';
import {
  Film,
  Download,
  FolderOpen,
  Save,
  Sliders,
  Sparkles,
  Maximize,
  Volume2,
  Layers,
  FileCode
} from 'lucide-react';

export default function Navbar({
  projectName,
  onSaveProject,
  onNewProject,
  onOpenProjectList,
  onAnalyze,
  isAnalyzing,
  onOpenExport,
  onOpenAssemblyStage,
  onLoadSample,
  hasMedia,
  activeRightTab,
  setActiveRightTab,
  isEdited
}) {
  return (
    <div className="flex flex-col bg-[#121316] border-b border-[#24262b] select-none text-[12px] text-[#a0a4ae]">
      {/* 1. Main Application & File Menu Bar */}
      <div className="h-6 px-3 flex items-center justify-between border-b border-[#1c1d21] text-[11px] bg-[#0e0f11]">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 font-semibold text-[#d0d3dc]">
            {/* Subtle DaVinci-inspired three-circle emblem */}
            <div className="flex items-center gap-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#d4483b]" />
              <span className="w-1.5 h-1.5 rounded-full bg-[#3b82d4]" />
              <span className="w-1.5 h-1.5 rounded-full bg-[#d4a03b]" />
            </div>
            <span className="tracking-wide">EditMind AI</span>
          </div>

          <div className="flex items-center gap-3 text-[#828692]">
            <span className="hover:text-white cursor-pointer" onClick={onNewProject}>File</span>
            <span className="hover:text-white cursor-pointer">Edit</span>
            <span className="hover:text-white cursor-pointer">Trim</span>
            <span className="hover:text-white cursor-pointer">Timeline</span>
            <span className="hover:text-white cursor-pointer">Clip</span>
            <span className="hover:text-white cursor-pointer">Mark</span>
            <span className="hover:text-white cursor-pointer">View</span>
            <span className="hover:text-white cursor-pointer">Playback</span>
            <span className="hover:text-white cursor-pointer">Fusion</span>
            <span className="hover:text-white cursor-pointer">Color</span>
            <span className="hover:text-white cursor-pointer">Fairlight</span>
            <span className="hover:text-white cursor-pointer">Help</span>
          </div>
        </div>

        {/* Quick Demo Sample Loader */}
        <div className="flex items-center gap-3 text-[11px]">
          <button
            onClick={onLoadSample}
            className="flex items-center gap-1 px-2 py-0.5 rounded bg-[#1a1c20] hover:bg-[#25272e] text-[#b5b9c4] border border-[#2b2d35] transition"
            title="Load 30s Multi-Scene Demo Sample Assets"
          >
            <FolderOpen className="w-3 h-3 text-[#828692]" />
            <span>Load Demo Sample</span>
          </button>
        </div>
      </div>

      {/* 2. DaVinci Resolve Secondary Tool Header */}
      <div className="h-9 px-3 flex items-center justify-between bg-[#16171b]">
        {/* Left tabs: Media Pool, Sync Bin, Transitions, etc. */}
        <div className="flex items-center gap-1 text-[11px]">
          <button className="px-2.5 py-1 rounded bg-[#25272e] text-[#e0e3eb] font-medium border border-[#32353e]">
            Media Pool
          </button>
          <button className="px-2 py-1 rounded hover:bg-[#202227] text-[#868a96] hover:text-[#c4c7d0] transition">
            Sync Bin
          </button>
          <button className="px-2 py-1 rounded hover:bg-[#202227] text-[#868a96] hover:text-[#c4c7d0] transition">
            Transitions
          </button>
          <button className="px-2 py-1 rounded hover:bg-[#202227] text-[#868a96] hover:text-[#c4c7d0] transition">
            Titles
          </button>
          <button className="px-2 py-1 rounded hover:bg-[#202227] text-[#868a96] hover:text-[#c4c7d0] transition">
            Effects
          </button>
        </div>

        {/* Center: Project title & Edit status */}
        <div className="flex items-center gap-2">
          <button
            onClick={onOpenProjectList}
            className="font-medium text-[#d8dbe4] hover:text-white text-xs flex items-center gap-1.5"
            title="Open or Switch Project"
          >
            <span>{projectName}</span>
          </button>
          {isEdited && (
            <span className="text-[10px] text-[#737785] tracking-wide uppercase px-1 py-0.2 rounded border border-[#2a2c33]">
              Edited
            </span>
          )}
          <button
            onClick={onSaveProject}
            className="p-1 rounded text-[#7e828e] hover:text-white hover:bg-[#22242a] transition ml-1"
            title="Save Project (Ctrl+S)"
          >
            <Save className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Right action toggles: AI Video Pipeline, Analyze, Quick Export, Inspector, AI Assistant */}
        <div className="flex items-center gap-1.5 text-[11px]">
          <button
            onClick={onOpenAssemblyStage}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#202834] hover:bg-[#283546] text-[#b8cde8] border border-[#344b68] transition shadow-xs"
            title="Open AI Video Pipeline (Upload, Analysis, Global Story Planning, Validation, OTIO Export)"
          >
            <Sparkles className="w-3 h-3 text-[#d48b3b]" />
            <span className="font-medium text-[#e0e3eb]">AI Video Pipeline</span>
          </button>

          <button
            onClick={onAnalyze}
            disabled={!hasMedia || isAnalyzing}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#1f2127] hover:bg-[#282b33] text-[#b8bcc8] border border-[#2d3038] transition disabled:opacity-40"
            title="Analyze Video for Scenes, Silences, and Dialogue"
          >
            <Sparkles className={`w-3 h-3 text-[#b8bcc8] ${isAnalyzing ? 'animate-spin' : ''}`} />
            <span>{isAnalyzing ? 'Analyzing...' : 'Analyze'}</span>
          </button>

          <button
            onClick={onOpenExport}
            disabled={!hasMedia}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#252830] hover:bg-[#2f333d] text-[#e0e3eb] border border-[#373a44] transition disabled:opacity-40"
            title="Render & Export Timeline as MP4"
          >
            <Download className="w-3 h-3 text-[#a5aab8]" />
            <span>Quick Export</span>
          </button>

          <div className="w-px h-3.5 bg-[#2a2c33] mx-1" />

          {/* Inspector Toggle */}
          <button
            onClick={() => setActiveRightTab('inspector')}
            className={`flex items-center gap-1 px-2.5 py-1 rounded border transition ${
              activeRightTab === 'inspector'
                ? 'bg-[#252830] text-[#e0e3eb] border-[#3e424e]'
                : 'bg-transparent text-[#7e828e] hover:text-[#c4c7d0] border-transparent'
            }`}
          >
            <Sliders className="w-3 h-3" />
            <span>Inspector</span>
          </button>

          {/* AI Assistant Toggle */}
          <button
            onClick={() => setActiveRightTab('ai')}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded border transition ${
              activeRightTab === 'ai'
                ? 'bg-[#252830] text-[#e0e3eb] border-[#3e424e]'
                : 'bg-transparent text-[#7e828e] hover:text-[#c4c7d0] border-transparent'
            }`}
          >
            <Sparkles className="w-3 h-3 text-[#d48b3b]" />
            <span>AI Assistant</span>
          </button>
        </div>
      </div>
    </div>
  );
}
