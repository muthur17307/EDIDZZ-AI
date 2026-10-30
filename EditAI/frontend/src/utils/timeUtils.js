/**
 * Formats seconds into professional SMPTE timecode (HH:MM:SS:FF)
 */
export function formatSMPTE(seconds, fps = 25) {
  if (isNaN(seconds) || seconds === null || seconds === undefined) {
    return "00:00:00:00";
  }
  const totalSecs = Math.max(0, Number(seconds));
  const hrs = Math.floor(totalSecs / 3600);
  const mins = Math.floor((totalSecs % 3600) / 60);
  const secs = Math.floor(totalSecs % 60);
  const frames = Math.floor((totalSecs - Math.floor(totalSecs)) * fps);

  const hh = String(hrs).padStart(2, "0");
  const mm = String(mins).padStart(2, "0");
  const ss = String(secs).padStart(2, "0");
  const ff = String(frames).padStart(2, "0");

  return `${hh}:${mm}:${ss}:${ff}`;
}

export function formatTimecode(seconds, includeMillis = false) {
  if (isNaN(seconds) || seconds === null || seconds === undefined) {
    return includeMillis ? "00:00.00" : "00:00";
  }
  const s = Math.max(0, Number(seconds));
  const hrs = Math.floor(s / 3600);
  const mins = Math.floor((s % 3600) / 60);
  const secs = Math.floor(s % 60);
  const millis = Math.floor((s - Math.floor(s)) * 100);

  const mm = String(mins).padStart(2, "0");
  const ss = String(secs).padStart(2, "0");
  const ms = String(millis).padStart(2, "0");

  if (hrs > 0) {
    const hh = String(hrs).padStart(2, "0");
    return includeMillis ? `${hh}:${mm}:${ss}.${ms}` : `${hh}:${mm}:${ss}`;
  }
  return includeMillis ? `${mm}:${ss}.${ms}` : `${mm}:${ss}`;
}

export function formatBytes(bytes) {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}
