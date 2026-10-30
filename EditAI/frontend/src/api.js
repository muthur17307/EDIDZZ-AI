const API_BASE = "";

// Project Persistence APIs
export async function listProjects() {
  const res = await fetch(`${API_BASE}/api/projects`);
  return res.json();
}

export async function createProject(name = "New Project") {
  const res = await fetch(`${API_BASE}/api/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return res.json();
}

export async function getProject(projectId) {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}`);
  if (!res.ok) throw new Error("Failed to load project");
  return res.json();
}

export async function saveProject(projectId, payload) {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function autosaveProject(projectId, payload) {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/autosave`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

// Media Upload APIs
export async function uploadBatchVideos(files) {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }
  const res = await fetch(`${API_BASE}/api/media/upload/batch`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Batch upload failed" }));
    throw new Error(err.detail || "Batch upload failed");
  }
  return res.json();
}

export async function loadMultiSamplePack() {
  const res = await fetch(`${API_BASE}/api/assembly/sample-pack`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to load multi-clip sample pack");
  return res.json();
}

// AI Video-Analysis Pipeline APIs
export async function createPipelineProject(brief, files) {
  const formData = new FormData();
  formData.append("brief", brief);
  for (let i = 0; i < files.length; i++) {
    formData.append("clips", files[i]);
  }
  const res = await fetch(`${API_BASE}/projects`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Pipeline project failed" }));
    throw new Error(err.detail || "Pipeline project failed");
  }
  return res.json();
}

export async function runPipelineOnExisting(payload) {
  const res = await fetch(`${API_BASE}/api/pipeline/run-existing`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Pipeline run failed" }));
    throw new Error(err.detail || "Pipeline run failed");
  }
  return res.json();
}

export async function runPipelineSamplePack(brief = null) {
  const res = await fetch(`${API_BASE}/api/pipeline/sample-pack`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brief }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Pipeline sample pack failed" }));
    throw new Error(err.detail || "Pipeline sample pack failed");
  }
  return res.json();
}

export async function analyzeAndAssembleProduction(payload) {
  const res = await fetch(`${API_BASE}/api/assembly/analyze-and-assemble`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Assembly failed" }));
    throw new Error(err.detail || "Assembly failed");
  }
  return res.json();
}

export async function uploadVideo(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/media/upload/video`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Video upload failed" }));
    throw new Error(err.detail || "Video upload failed");
  }
  return res.json();
}

export async function uploadAudio(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/media/upload/audio`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Audio upload failed" }));
    throw new Error(err.detail || "Audio upload failed");
  }
  return res.json();
}

export async function uploadSubtitle(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/media/upload/subtitle`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Subtitle upload failed" }));
    throw new Error(err.detail || "Subtitle upload failed");
  }
  return res.json();
}

export async function loadSampleProject() {
  const res = await fetch(`${API_BASE}/api/media/load-sample`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to load sample project");
  }
  return res.json();
}

export async function analyzeVideo(filepath, duration) {
  const res = await fetch(`${API_BASE}/api/analysis/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filepath, duration }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Video analysis failed" }));
    throw new Error(err.detail || "Video analysis failed");
  }
  return res.json();
}

export async function sendChatbotCommand(payload) {
  const res = await fetch(`${API_BASE}/api/chatbot/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Chatbot command failed" }));
    throw new Error(err.detail || "Chatbot command failed");
  }
  return res.json();
}

export async function getLLMProviders() {
  try {
    const res = await fetch(`${API_BASE}/api/chatbot/providers`);
    if (!res.ok) return { active_engine: "Semantic NLP" };
    return res.json();
  } catch (e) {
    return { active_engine: "Semantic NLP" };
  }
}

// Timeline APIs
export async function splitTimeline(timeline, splitTime) {
  const res = await fetch(`${API_BASE}/api/timeline/split`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ timeline, split_time: splitTime }),
  });
  return res.json();
}

export async function deleteTimelineSelection(timeline) {
  const res = await fetch(`${API_BASE}/api/timeline/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ timeline }),
  });
  return res.json();
}

export async function cutTimelineSelection(timeline) {
  const res = await fetch(`${API_BASE}/api/timeline/cut`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ timeline }),
  });
  return res.json();
}

export async function trimTimelineRange(timeline, startTime, endTime) {
  const res = await fetch(`${API_BASE}/api/timeline/trim`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ timeline, start_time: startTime, end_time: endTime }),
  });
  return res.json();
}

export async function undoTimelineAction(timeline) {
  const res = await fetch(`${API_BASE}/api/timeline/undo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ timeline }),
  });
  return res.json();
}

export async function redoTimelineAction(timeline) {
  const res = await fetch(`${API_BASE}/api/timeline/redo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ timeline }),
  });
  return res.json();
}

// Export API
export async function renderExport(payload) {
  const res = await fetch(`${API_BASE}/api/export/render`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Render export failed" }));
    throw new Error(err.detail || "Render export failed");
  }
  return res.json();
}
