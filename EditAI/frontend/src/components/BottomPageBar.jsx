import React from 'react';
import {
  Folder,
  Scissors,
  Film,
  Sparkles,
  Palette,
  Music,
  Send,
  Home,
  Settings
} from 'lucide-react';

export default function BottomPageBar({
  activePage = 'edit',
  onSelectPage
}) {
  const pages = [
    { id: 'media', label: 'Media', icon: Folder },
    { id: 'cut', label: 'Cut', icon: Scissors },
    { id: 'edit', label: 'Edit', icon: Film },
    { id: 'fusion', label: 'Fusion', icon: Sparkles },
    { id: 'color', label: 'Color', icon: Palette },
    { id: 'fairlight', label: 'Fairlight', icon: Music },
    { id: 'deliver', label: 'Deliver', icon: Send }
  ];

  return (
    <div className="h-7 bg-[#0c0d0f] border-t border-[#1c1d22] px-3 flex items-center justify-between text-[11px] text-[#555a66] select-none">
      {/* Left: DaVinci logo & build text */}
      <div className="flex items-center gap-1.5 text-[10px] text-[#636875]">
        <span className="w-1.5 h-1.5 rounded-full bg-[#d4483b]" />
        <span>DaVinci Resolve 21 Workflow</span>
      </div>

      {/* Center: DaVinci workspace page icons */}
      <div className="flex items-center gap-1">
        {pages.map((p) => {
          const Icon = p.icon;
          const isActive = activePage === p.id;
          return (
            <button
              key={p.id}
              onClick={() => onSelectPage && onSelectPage(p.id)}
              className={`px-3 py-1 flex items-center gap-1.5 transition ${
                isActive
                  ? 'text-[#d8dbe4] bg-[#1a1b20] border-t-2 border-[#d4483b] -mt-0.5'
                  : 'hover:text-[#9fa3af]'
              }`}
              title={p.label}
            >
              <Icon className="w-3 h-3" />
            </button>
          );
        })}
      </div>

      {/* Right: Home & Settings */}
      <div className="flex items-center gap-2 text-[#555a66]">
        <Home className="w-3 h-3 hover:text-[#9fa3af] cursor-pointer" />
        <Settings className="w-3 h-3 hover:text-[#9fa3af] cursor-pointer" />
      </div>
    </div>
  );
}
