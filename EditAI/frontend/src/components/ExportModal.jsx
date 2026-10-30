import React, { useState } from 'react';
import {
  X,
  Download,
  Film,
  Music,
  FileText,
  CheckCircle2,
  Sparkles,
  AlertCircle
} from 'lucide-react';
import { renderExport } from '../api';
import { formatBytes, formatSMPTE } from '../utils/timeUtils';

export default function ExportModal({
  isOpen,
  onClose,
  timeline,
  audioTrack,
  videoMetadata
}) {
  const [resolution, setResolution] = useState('original');
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [scalingMode, setScalingMode] = useState('crop');
  const [audioMode, setAudioMode] = useState(audioTrack ? 'mix' : 'original');
  const [burnSubtitles, setBurnSubtitles] = useState(timeline?.subtitles?.length > 0);
  const [isExporting, setIsExporting] = useState(false);
  const [exportResult, setExportResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen) return null;

  const handleStartExport = async () => {
    setIsExporting(true);
    setErrorMessage('');
    setExportResult(null);

    try {
      const res = await renderExport({
        timeline,
        resolution,
        aspect_ratio: aspectRatio,
        scaling_mode: scalingMode,
        burn_subtitles: burnSubtitles,
        audio_mode: audioMode,
        external_audio_path: audioTrack?.filepath || null,
      });
      setExportResult(res);
    } catch (err) {
      setErrorMessage(err.message || 'Export failed.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4 select-none text-[12px] text-[#a0a4ae]">
      <div className="bg-[#18191d] border border-[#2b2d35] rounded-lg max-w-md w-full overflow-hidden shadow-2xl flex flex-col">
        {/* Header */}
        <div className="h-10 px-4 border-b border-[#24262c] flex items-center justify-between bg-[#141518]">
          <span className="font-medium text-[#d8dbe4] text-xs">Quick Export</span>
          <button
            onClick={onClose}
            className="p-1 rounded text-[#6f7482] hover:text-[#d0d3dc] hover:bg-[#252830] transition"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 space-y-4">
          {/* Timeline Summary */}
          <div className="bg-[#1d1f25] border border-[#282a32] rounded p-2.5 flex justify-between items-center font-mono text-[11px]">
            <div>
              <span className="text-[#696e7d]">Duration: </span>
              <span className="text-[#d8dbe4] font-medium">{formatSMPTE(timeline?.total_duration)}</span>
            </div>
            <div>
              <span className="text-[#696e7d]">Clips: </span>
              <span className="text-[#d8dbe4]">{timeline?.clips?.length} segments</span>
            </div>
          </div>

          {/* Preset Aspect Ratios */}
          <div>
            <label className="block text-[#7c8190] text-[11px] mb-1.5 font-medium">Aspect Ratio Preset</label>
            <div className="grid grid-cols-3 gap-1.5">
              {[
                { id: '16:9', label: '16:9 Landscape' },
                { id: '9:16', label: '9:16 Vertical' },
                { id: '1:1', label: '1:1 Square' }
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setAspectRatio(item.id)}
                  className={`py-1.5 px-2 rounded border text-center transition text-[11px] font-mono ${
                    aspectRatio === item.id
                      ? 'bg-[#293240] border-[#4a6b99] text-[#e0e3eb]'
                      : 'bg-[#1e2026] border-[#292b34] text-[#868a96] hover:text-[#c4c7d0]'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {/* Scaling Mode (if 9:16) */}
          {aspectRatio === '9:16' && (
            <div>
              <label className="block text-[#7c8190] text-[11px] mb-1.5 font-medium">Vertical Framing</label>
              <div className="grid grid-cols-2 gap-1.5 text-[11px]">
                <button
                  type="button"
                  onClick={() => setScalingMode('crop')}
                  className={`py-1.5 px-2 rounded border text-center transition ${
                    scalingMode === 'crop'
                      ? 'bg-[#293240] border-[#4a6b99] text-[#e0e3eb]'
                      : 'bg-[#1e2026] border-[#292b34] text-[#868a96]'
                  }`}
                >
                  Fill & Center Crop
                </button>
                <button
                  type="button"
                  onClick={() => setScalingMode('fit')}
                  className={`py-1.5 px-2 rounded border text-center transition ${
                    scalingMode === 'fit'
                      ? 'bg-[#293240] border-[#4a6b99] text-[#e0e3eb]'
                      : 'bg-[#1e2026] border-[#292b34] text-[#868a96]'
                  }`}
                >
                  Fit & Letterbox
                </button>
              </div>
            </div>
          )}

          {/* Audio Mixing */}
          <div>
            <label className="block text-[#7c8190] text-[11px] mb-1.5 font-medium">Audio Mix</label>
            <div className="grid grid-cols-3 gap-1.5 text-[11px]">
              {[
                { id: 'original', label: 'Video Audio' },
                { id: 'external', label: 'External Track', disabled: !audioTrack },
                { id: 'mix', label: 'Mix Both', disabled: !audioTrack }
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  disabled={item.disabled}
                  onClick={() => setAudioMode(item.id)}
                  className={`py-1.5 px-2 rounded border text-center transition ${
                    audioMode === item.id
                      ? 'bg-[#293240] border-[#4a6b99] text-[#e0e3eb]'
                      : 'bg-[#1e2026] border-[#292b34] text-[#868a96]'
                  } disabled:opacity-30`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {/* Subtitles Burn-in */}
          <label className="flex items-center gap-2 cursor-pointer bg-[#1c1d22] border border-[#272932] p-2 rounded">
            <input
              type="checkbox"
              checked={burnSubtitles}
              onChange={(e) => setBurnSubtitles(e.target.checked)}
              disabled={!timeline?.subtitles || timeline.subtitles.length === 0}
              className="rounded bg-[#121316] border-[#373a46] text-[#4a6b99]"
            />
            <span className="text-[11px] text-[#b3b7c0]">Burn synchronized subtitles into video frames</span>
          </label>

          {/* Error notice */}
          {errorMessage && (
            <div className="bg-[#2a1d1f] border border-[#442327] p-2 rounded text-[#e28b8b] text-[11px]">
              {errorMessage}
            </div>
          )}

          {/* Success Result */}
          {exportResult && (
            <div className="bg-[#1b221d] border border-[#2d4b35] rounded p-2.5 space-y-2">
              <div className="flex items-center gap-1.5 text-[#5bb676] font-medium text-[11px]">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Render Complete</span>
              </div>
              <div className="flex justify-between font-mono text-[10px] text-[#8b92a2]">
                <span>{exportResult.filename}</span>
                <span>{formatBytes(exportResult.size_bytes)}</span>
              </div>
              <a
                href={exportResult.download_url}
                download={exportResult.filename}
                className="w-full py-1.5 bg-[#243328] hover:bg-[#2c4032] border border-[#375a40] text-[#e0e3eb] rounded text-center font-medium flex items-center justify-center gap-1.5 transition text-[11px]"
              >
                <Download className="w-3 h-3" />
                <span>Download Rendered MP4</span>
              </a>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="h-11 px-4 border-t border-[#24262c] bg-[#141518] flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-3 py-1 rounded bg-[#202228] hover:bg-[#2a2c34] text-[#9da1ad] hover:text-white transition text-[11px]"
          >
            Close
          </button>
          {!exportResult && (
            <button
              onClick={handleStartExport}
              disabled={isExporting}
              className="px-4 py-1 rounded bg-[#252830] hover:bg-[#313540] border border-[#3e424e] text-[#e0e3eb] font-medium transition text-[11px] disabled:opacity-40"
            >
              {isExporting ? 'Rendering...' : 'Export'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
