import React, { useState, useEffect } from 'react';
import { X, Folder, Plus, Clock, Check } from 'lucide-react';
import { listProjects, createProject, getProject } from '../api';

export default function ProjectListModal({
  isOpen,
  onClose,
  currentProjectId,
  onSwitchProject
}) {
  const [projects, setProjects] = useState([]);
  const [newProjectName, setNewProjectName] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadProjects();
    }
  }, [isOpen]);

  const loadProjects = async () => {
    try {
      const list = await listProjects();
      setProjects(list);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    try {
      setIsLoading(true);
      const proj = await createProject(newProjectName.trim());
      setNewProjectName('');
      await loadProjects();
      onSwitchProject(proj.id);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelect = async (id) => {
    onSwitchProject(id);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4 select-none text-[12px] text-[#a0a4ae]">
      <div className="bg-[#18191d] border border-[#2b2d35] rounded-lg max-w-sm w-full overflow-hidden shadow-2xl flex flex-col">
        {/* Header */}
        <div className="h-10 px-4 border-b border-[#24262c] flex items-center justify-between bg-[#141518]">
          <span className="font-medium text-[#d8dbe4] text-xs">Project Manager</span>
          <button
            onClick={onClose}
            className="p-1 rounded text-[#6f7482] hover:text-[#d0d3dc] hover:bg-[#252830] transition"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Create new project input */}
        <form onSubmit={handleCreate} className="p-3 border-b border-[#212328] flex items-center gap-1.5 bg-[#16171b]">
          <input
            type="text"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            placeholder="New project name..."
            className="flex-1 bg-[#1a1c22] text-[11px] text-[#d8dbe4] rounded px-2.5 py-1.5 border border-[#282b34] focus:outline-none focus:border-[#424653]"
          />
          <button
            type="submit"
            disabled={!newProjectName.trim() || isLoading}
            className="px-2.5 py-1.5 bg-[#252830] hover:bg-[#323642] text-[#e0e3eb] rounded border border-[#343844] text-[11px] font-medium transition disabled:opacity-40"
          >
            Create
          </button>
        </form>

        {/* Projects List */}
        <div className="p-3 max-h-60 overflow-y-auto space-y-1.5">
          {projects.map((p) => {
            const isCurrent = p.id === currentProjectId;
            return (
              <div
                key={p.id}
                onClick={() => handleSelect(p.id)}
                className={`p-2 rounded border cursor-pointer flex items-center justify-between transition ${
                  isCurrent
                    ? 'bg-[#212630] border-[#3e4f68] text-[#e0e3eb]'
                    : 'bg-[#1b1c20] hover:bg-[#212329] border-[#262830] text-[#9da1ad]'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Folder className="w-3.5 h-3.5 text-[#6c7180]" />
                  <span className="font-medium text-[11px]">{p.name}</span>
                </div>
                {isCurrent && <Check className="w-3.5 h-3.5 text-[#5594df]" />}
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="h-10 px-4 border-t border-[#24262c] bg-[#141518] flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-3 py-1 rounded bg-[#202228] hover:bg-[#2a2c34] text-[#9da1ad] transition text-[11px]"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
