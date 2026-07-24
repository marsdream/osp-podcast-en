#!/usr/bin/env python3
"""Generate index.html for English podcast site"""
import os, json
from datetime import datetime

EPISODES_DIR = "episodes"
OUTPUT_FILE = "index.html"

def extract_description(script_raw):
    if not script_raw:
        return ""
    try:
        data = json.loads(script_raw)
        parts = [t.get("dialog", "") for t in data.get("podcast_transcripts", [])]
        text = " ".join(parts)
        return text[:300] + "..." if len(text) > 300 else text
    except Exception:
        return ""

def format_date(date_str):
    if not date_str:
        return ""
    try:
        d = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return d.strftime("%Y-%m-%d")
    except Exception:
        return date_str[:10]

def generate_index():
    episodes = []
    for f in os.listdir(EPISODES_DIR):
        if f.startswith("episode_") and f.endswith(".json"):
            with open(os.path.join(EPISODES_DIR, f)) as fp:
                episodes.append(json.load(fp))

    episodes.sort(key=lambda x: x.get("date", ""), reverse=True)

    episode_cards = ""
    for ep in episodes:
        audio_file = ep.get("audio_file", "")
        title = ep.get("title", "Untitled")
        link = ep.get("link", "")
        desc = extract_description(ep.get("script", ""))
        date = format_date(ep.get("date", ""))
        file_size = ep.get("file_size_kb", 0)

        episode_cards += f"""
        <div class="episode-card">
          <div class="episode-meta">{date}</div>
          <h3 class="episode-title"><a href="{link}" target="_blank">{title}</a></h3>
          <p class="episode-desc">{desc}</p>
          <div class="episode-actions">
            <audio controls controlsList="nodownload">
              <source src="episodes/{audio_file}" type="audio/mpeg">
              Your browser does not support the audio element.
            </audio>
            <a href="episodes/{audio_file}" download class="download-btn" title="Download MP3">⬇</a>
          </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Open Source Pulse (English)</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117; color: #e6edf3; max-width: 900px; margin: 0 auto; padding: 20px; }}
    header {{ text-align: center; padding: 40px 0 30px; border-bottom: 1px solid #21262d; margin-bottom: 30px; }}
    h1 {{ font-size: 2.2em; color: #58a6ff; margin-bottom: 8px; }}
    header p {{ color: #8b949e; font-size: 1.1em; }}
    .feed-link {{ display: inline-block; margin-top: 15px; padding: 8px 20px;
                  background: #238636; color: #fff; border-radius: 6px; text-decoration: none; }}
    .feed-link:hover {{ background: #2ea043; }}
    .stats {{ text-align: center; color: #8b949e; margin-bottom: 30px; font-size: 0.9em; }}
    .episode-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px;
                     padding: 20px; margin-bottom: 20px; }}
    .episode-meta {{ font-size: 0.85em; color: #8b949e; margin-bottom: 8px; }}
    .episode-title {{ font-size: 1.3em; margin-bottom: 10px; }}
    .episode-title a {{ color: #58a6ff; text-decoration: none; }}
    .episode-title a:hover {{ text-decoration: underline; }}
    .episode-desc {{ color: #8b949e; line-height: 1.6; margin-bottom: 15px; font-size: 0.95em; }}
    .episode-actions {{ display: flex; gap: 10px; align-items: center; }}
    audio {{ flex: 1; height: 36px; border-radius: 4px; }}
    audio::-webkit-media-controls-panel {{ background: #21262d; }}
    .download-btn {{ padding: 6px 14px; background: #30363d; color: #e6edf3;
                      border-radius: 6px; text-decoration: none; font-size: 0.9em; }}
    .download-btn:hover {{ background: #484f58; }}
    footer {{ text-align: center; color: #8b949e; padding: 30px 0; font-size: 0.85em; }}
    footer a {{ color: #58a6ff; }}
  </style>
</head>
<body>
  <header>
    <h1>Open Source Pulse (English)</h1>
    <p>Your English podcast about open source, tech, and developer tools</p>
    <a href="feed.xml" class="feed-link">📻 Subscribe via RSS</a>
  </header>
  <div class="stats">{len(episodes)} episodes</div>
  <main>
{episode_cards}
  </main>
  <footer>
    Powered by AI · Generated automatically by osp-podcast-en<br>
    <a href="https://github.com/marsdream/osp-podcast-en">View on GitHub</a>
  </footer>
</body>
</html>"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"index.html generated with {len(episodes)} episodes")


if __name__ == "__main__":
    generate_index()
