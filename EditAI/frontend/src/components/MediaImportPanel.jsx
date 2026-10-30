import React, { useRef, useState } from 'react';
import {
  Folder,
  Film,
  Music,
  FileText,
  Plus,
  Trash2,
  Search,
  LayoutGrid,
  List,
  Play,
  PlusCircle,
  Eye
} from 'lucide-react';
import { formatTimecode, formatBytes } from '../utils/timeUtils';

export default function MediaImportPanel({
  mediaPoolVideos = [],
  activeVideoId = null,
  audioTrack = null,
  subtitles = [],
  onUploadVideos,
  onUploadAudio,
  onUploadSubtitle,
  onRemoveVideo,
  onRemoveMedia,
  onSelectVideo,
  onInsertVideoToTimeline
}) {
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'list'
  const [searchQuery, setSearchQuery] = useState('');
  const [isImportMenuOpen, setIsImportMenuOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const videoInputRef = useRef(null);
  const audioInputRef = useRef(null);
  const subtitleInputRef = useRef(null);

  const filteredVideos = mediaPoolVideos.filter((v) =>
    v.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const hasAnyMedia =
    mediaPoolVideos.length > 0 || !!audioTrack || (subtitles && subtitles.length > 0);

  // Drag and drop handlers
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

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      onUploadVideos(files);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`h-full flex flex-col bg-[#141518] text-[#a0a4ae] select-none text-[12px] relative ${
        isDragging ? 'ring-2 ring-[#3b82d4] bg-[#161b24]' : ''
      }`}
    >
      {/* 1. Media Pool Sub-header */}
      <div className="h-8 px-2.5 border-b border-[#212328] flex items-center justify-between bg-[#18191d] text-[11px]">
        {/* Breadcrumb & count */}
        <div className="flex items-center gap-1.5 text-[#c8cbcd]">
          <Folder className="w-3.5 h-3.5 text-[#737887]" />
          <span className="font-medium">Master</span>
          <span className="text-[10px] text-[#636875] font-mono">
            ({mediaPoolVideos.length} clips)
          </span>
        </div>

        {/* Action icons: Grid/List toggle, Search, Import (+) */}
        <div className="flex items-center gap-1 text-[#7a7f8e]">
          <div className="relative">
            <button
              onClick={() => setIsImportMenuOpen(!isImportMenuOpen)}
              className="p-1 rounded hover:bg-[#252830] hover:text-[#d0d3dc] transition flex items-center gap-0.5"
              title="Import Media Files"
            >
              <Plus className="w-3.5 h-3.5 text-[#b5b9c4]" />
            </button>

            {isImportMenuOpen && (
              <div className="absolute top-7 left-0 w-44 bg-[#1a1c22] border border-[#2e313b] rounded shadow-xl py-1 z-30 text-[11px]">
                <button
                  onClick={() => {
                    setIsImportMenuOpen(false);
                    videoInputRef.current?.click();
                  }}
                  className="w-full text-left px-3 py-1.5 hover:bg-[#252934] text-[#d0d3dc] flex items-center gap-2"
                >
                  <Film className="w-3 h-3 text-[#7f8595]" />
                  <span>Import Videos (Multiple)...</span>
                </button>
                <button
                  onClick={() => {
                    setIsImportMenuOpen(false);
                    audioInputRef.current?.click();
                  }}
                  className="w-full text-left px-3 py-1.5 hover:bg-[#252934] text-[#d0d3dc] flex items-center gap-2"
                >
                  <Music className="w-3 h-3 text-[#7f8595]" />
                  <span>Import Audio...</span>
                </button>
                <button
                  onClick={() => {
                    setIsImportMenuOpen(false);
                    subtitleInputRef.current?.click();
                  }}
                  className="w-full text-left px-3 py-1.5 hover:bg-[#252934] text-[#d0d3dc] flex items-center gap-2"
                >
                  <FileText className="w-3 h-3 text-[#7f8595]" />
                  <span>Import Subtitles...</span>
                </button>
              </div>
            )}
          </div>

          <button
            onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
            className="p-1 rounded hover:bg-[#252830] hover:text-[#d0d3dc] transition"
            title="Toggle Grid / List View"
          >
            {viewMode === 'grid' ? <List className="w-3.5 h-3.5" /> : <LayoutGrid className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Search Bar if multiple clips */}
      {mediaPoolVideos.length > 2 && (
        <div className="px-2 py-1 bg-[#121316] border-b border-[#1c1d22]">
          <div className="flex items-center gap-1.5 bg-[#1a1c22] px-2 py-1 rounded border border-[#262830]">
            <Search className="w-3 h-3 text-[#555a66]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search pool..."
              className="w-full bg-transparent text-[10px] text-[#d8dbe4] placeholder-[#555a66] focus:outline-none"
            />
          </div>
        </div>
      )}

      {/* 2. Media Pool Canvas */}
      <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
        {!hasAnyMedia ? (
          /* Empty state */
          <div
            onClick={() => videoInputRef.current?.click()}
            className="h-full flex flex-col items-center justify-center text-center cursor-pointer group p-4 border border-dashed border-[#22242a] rounded"
          >
            <p className="text-[#555a66] text-sm font-normal mb-1 group-hover:text-[#888e9d] transition">
              No clips in media pool
            </p>
            <p className="text-[#3b3e47] text-[11px] group-hover:text-[#555a66] transition">
              Click to select or drop multiple video clips here
            </p>
          </div>
        ) : (
          <div>
            {/* Multiple Video Assets */}
            <div className={viewMode === 'grid' ? 'grid grid-cols-2 gap-2' : 'space-y-1.5'}>
              {filteredVideos.map((clip) => {
                const isActive = clip.id === activeVideoId;
                const dur = clip.metadata?.duration || 0;
                const width = clip.metadata?.width || 1920;
                const height = clip.metadata?.height || 1080;
                const fps = clip.metadata?.fps || 25;

                return (
                  <div
                    key={clip.id}
                    onClick={() => onSelectVideo && onSelectVideo(clip)}
                    className={`bg-[#1c1d22] border rounded p-2 transition relative group cursor-pointer ${
                      isActive
                        ? 'border-[#3b82d4] bg-[#1d222b]'
                        : 'border-[#272932] hover:border-[#3e424e]'
                    } ${viewMode === 'list' ? 'flex items-center justify-between gap-2' : ''}`}
                  >
                    {viewMode === 'grid' && (
                      <div className="w-full aspect-video bg-[#0d0e10] rounded mb-1.5 flex items-center justify-center relative overflow-hidden border border-[#22242a]">
                        <Film className={`w-5 h-5 ${isActive ? 'text-[#7ea5dc]' : 'text-[#424653]'}`} />
                        <span className="absolute bottom-1 right-1 bg-black/80 text-[8px] font-mono text-[#a5abb8] px-1 rounded">
                          {formatTimecode(dur)}
                        </span>
                        {isActive && (
                          <span className="absolute top-1 left-1 bg-[#3b82d4]/80 text-white text-[8px] font-mono px-1 rounded">
                            Active
                          </span>
                        )}
                      </div>
                    )}

                    <div className="min-w-0 flex-1">
                      <p
                        className={`font-medium truncate text-[11px] ${
                          isActive ? 'text-[#e2e7f0]' : 'text-[#c8cbd4]'
                        }`}
                        title={clip.filename}
                      >
                        {clip.filename}
                      </p>
                      <p className="text-[9px] text-[#696e7d] font-mono mt-0.5">
                        {width}x{height} • {fps}fps
                        {viewMode === 'list' && ` • ${formatTimecode(dur)}`}
                      </p>
                    </div>

                    {/* Action buttons on hover */}
                    <div className="flex items-center gap-1 mt-1 justify-end">
                      {onInsertVideoToTimeline && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onInsertVideoToTimeline(clip);
                          }}
                          className="px-1.5 py-0.5 rounded bg-[#202834] hover:bg-[#283546] text-[#86a6d6] text-[9px] font-medium border border-[#304157] transition flex items-center gap-0.5"
                          title="Append this clip to timeline"
                        >
                          <PlusCircle className="w-2.5 h-2.5" />
                          <span>Timeline</span>
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onRemoveVideo) onRemoveVideo(clip.id);
                        }}
                        className="p-1 rounded hover:bg-[#2b2123] hover:text-[#d45555] text-[#555a66] transition opacity-0 group-hover:opacity-100"
                        title="Remove clip from media pool"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* External Audio Item */}
            {audioTrack && (
              <div
                className={`mt-2 bg-[#1c1d22] border border-[#272932] rounded p-2 hover:border-[#3e424e] transition relative group ${
                  viewMode === 'list' ? 'flex items-center justify-between gap-2' : ''
                }`}
              >
                {viewMode === 'grid' && (
                  <div className="w-full aspect-video bg-[#0d0e10] rounded mb-1.5 flex items-center justify-center relative border border-[#22242a]">
                    <Music className="w-5 h-5 text-[#424653]" />
                    <span className="absolute bottom-1 right-1 bg-black/80 text-[8px] font-mono text-[#a5abb8] px-1 rounded">
                      {formatTimecode(audioTrack.duration)}
                    </span>
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-[#d8dbe4] font-medium truncate text-[11px]">{audioTrack.filename}</p>
                  <p className="text-[9px] text-[#696e7d] font-mono mt-0.5">External Audio</p>
                </div>
                <button
                  onClick={() => onRemoveMedia('audio')}
                  className="p-1 rounded hover:bg-[#2b2123] hover:text-[#d45555] text-[#555a66] transition opacity-0 group-hover:opacity-100"
                  title="Remove Audio"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            )}

            {/* Subtitles Item */}
            {subtitles && subtitles.length > 0 && (
              <div
                className={`mt-2 bg-[#1c1d22] border border-[#272932] rounded p-2 hover:border-[#3e424e] transition relative group ${
                  viewMode === 'list' ? 'flex items-center justify-between gap-2' : ''
                }`}
              >
                {viewMode === 'grid' && (
                  <div className="w-full aspect-video bg-[#0d0e10] rounded mb-1.5 flex items-center justify-center relative border border-[#22242a]">
                    <FileText className="w-5 h-5 text-[#424653]" />
                    <span className="absolute bottom-1 right-1 bg-black/80 text-[8px] font-mono text-[#a5abb8] px-1 rounded">
                      {subtitles.length} lines
                    </span>
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-[#d8dbe4] font-medium truncate text-[11px]">Subtitles Track</p>
                  <p className="text-[9px] text-[#696e7d] font-mono mt-0.5">{subtitles.length} cues</p>
                </div>
                <button
                  onClick={() => onRemoveMedia('subtitles')}
                  className="p-1 rounded hover:bg-[#2b2123] hover:text-[#d45555] text-[#555a66] transition opacity-0 group-hover:opacity-100"
                  title="Remove Subtitles"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Hidden Multiple Video File Input */}
        <input
          type="file"
          ref={videoInputRef}
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              onUploadVideos(e.target.files);
            }
            e.target.value = '';
          }}
          multiple
          accept="video/*,.mp4,.mov,.webm,.mkv,.avi,.MP4,.MOV,.WEBM,.MKV,.AVI"
          className="hidden"
        />

        {/* Hidden Audio & Subtitle Inputs */}
        <input
          type="file"
          ref={audioInputRef}
          onChange={(e) => {
            if (e.target.files?.[0]) onUploadAudio(e.target.files[0]);
            e.target.value = '';
          }}
          accept="audio/mp3,audio/wav,audio/aac,audio/m4a"
          className="hidden"
        />
        <input
          type="file"
          ref={subtitleInputRef}
          onChange={(e) => {
            if (e.target.files?.[0]) onUploadSubtitle(e.target.files[0]);
            e.target.value = '';
          }}
          accept=".srt,.vtt,text/plain"
          className="hidden"
        />
      </div>
    </div>
  );
}
