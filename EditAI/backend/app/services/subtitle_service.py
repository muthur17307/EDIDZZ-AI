import re
from typing import List
from app.models.schemas import SubtitleItem

class SubtitleService:
    @staticmethod
    def parse_time_to_seconds(time_str: str) -> float:
        """Parses SRT '00:01:23,456' or VTT '00:01:23.456' to float seconds."""
        time_str = time_str.strip().replace(",", ".")
        parts = time_str.split(":")
        try:
            if len(parts) == 3:
                h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
                return round(h * 3600 + m * 60 + s, 3)
            elif len(parts) == 2:
                m, s = float(parts[0]), float(parts[1])
                return round(m * 60 + s, 3)
        except ValueError:
            pass
        return 0.0

    @classmethod
    def parse_srt_or_vtt(cls, content: str) -> List[SubtitleItem]:
        """Parses SRT or WebVTT content into a list of SubtitleItems."""
        lines = [line.strip() for line in content.strip().splitlines()]
        subtitles: List[SubtitleItem] = []

        # Remove WEBVTT header if present
        if lines and "WEBVTT" in lines[0].upper():
            lines = lines[1:]

        i = 0
        idx = 1
        time_regex = re.compile(r"(\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d+)?)\s*-->\s*(\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d+)?)")

        while i < len(lines):
            line = lines[i]
            match = time_regex.search(line)
            if match:
                start_sec = cls.parse_time_to_seconds(match.group(1))
                end_sec = cls.parse_time_to_seconds(match.group(2))
                text_lines = []
                i += 1
                while i < len(lines) and lines[i] != "":
                    # Check if next line is a new timestamp or number
                    if time_regex.search(lines[i]):
                        i -= 1
                        break
                    text_lines.append(lines[i])
                    i += 1

                sub_text = " ".join(text_lines).strip()
                if sub_text:
                    subtitles.append(SubtitleItem(
                        id=idx,
                        start_time=start_sec,
                        end_time=end_sec,
                        text=sub_text
                    ))
                    idx += 1
            i += 1

        return subtitles
