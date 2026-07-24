#!/usr/bin/env python3
"""Update RSS feed XML for English podcast"""
import os, json
from datetime import datetime

EPISODES_DIR = "episodes"
FEED_FILE = "feed.xml"

def extract_description(script_raw):
    if not script_raw:
        return ""
    try:
        data = json.loads(script_raw)
        parts = []
        for t in data.get("podcast_transcripts", []):
            parts.append(t.get("dialog", ""))
        text = " ".join(parts)
        return text[:500] + "..." if len(text) > 500 else text
    except Exception:
        return ""

def generate_rss():
    episodes = []
    for f in os.listdir(EPISODES_DIR):
        if f.startswith("episode_") and f.endswith(".json"):
            with open(os.path.join(EPISODES_DIR, f)) as fp:
                episodes.append(json.load(fp))

    episodes.sort(key=lambda x: x.get("date", ""), reverse=True)

    items = ""
    for ep in episodes:
        title = ep.get("title", "Untitled")
        link = ep.get("link", "")
        audio = ep.get("audio_file", "")
        date = ep.get("date", "")
        script = ep.get("script", "")
        desc = extract_description(script) or title
        pub_date = ""
        if date:
            try:
                d = datetime.fromisoformat(date.replace("Z", "+00:00"))
                pub_date = d.strftime("%a, %d %b %Y %H:%M:%S GMT")
            except Exception:
                pass

        items += f"""
    <item>
      <title><![CDATA[{title}]]></title>
      <link>{link}</link>
      <description><![CDATA[{desc}]]></description>
      <enclosure url="https://podcast-en.herebuy.us/episodes/{audio}" type="audio/mpeg" length="{ep.get('file_size_kb', 0) * 1024}"/>
      <pubDate>{pub_date}</pubDate>
      <guid isPermaLink="false">{ep.get('id', '')}</guid>
      <itunes:image href="https://img.osp.io/podcastcover.png"/>
    </item>"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
  xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Open Source Pulse (English)</title>
    <link>https://podcast-en.herebuy.us/</link>
    <description>Your English podcast about open source, tech, and developer tools. Powered by AI.</description>
    <language>en</language>
    <itunes:image href="https://img.osp.io/podcastcover.png"/>
    <itunes:category text="Technology"/>
    <atom:link href="https://podcast-en.herebuy.us/feed.xml" rel="self" type="application/rss+xml"/>
{items}
  </channel>
</rss>"""

    with open(FEED_FILE, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"RSS updated with {len(episodes)} episodes")

if __name__ == "__main__":
    generate_rss()
