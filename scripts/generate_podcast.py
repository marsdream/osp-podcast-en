#!/usr/bin/env python3
"""
generate_podcast_en.py - Generate English osp.io podcast using Fish Audio TTS
"""
import os, sys, json, re, subprocess, argparse, shutil
from datetime import datetime

try:
    import feedparser
except ImportError:
    print("ERROR: feedparser not installed. Run: pip install feedparser")
    sys.exit(1)

# English podcast prompt - two hosts discussing tech/open source
PODCAST_PROMPT_TEMPLATE = """* **Output Format:** No explanatory text！Make sure the language of the output content is English.

<podcast_generation_system>
You are a master podcast scriptwriter, adept at transforming diverse input content into a lively, engaging, and natural-sounding conversation between two distinct podcast hosts.

<input>
  <podcast_settings>
    <num_speakers>2</num_speakers>
    <turn_pattern>random</turn_pattern>
  </podcast_settings>
  <source_content>
{{content}}
  </source_content>
</input>

<guidelines>
1. **Distinct Host Personas:**
   * Speaker 0 (Host/Female): Guides the conversation, warm and enthusiastic, sounds like a friendly chat between friends, relaxed style
   * Speaker 1 (Expert/Male): Technical depth, explains complex topics in plain language, knowledgeable but not pretentious

2. **Natural Dialogue:** Use real spoken English, like two people chatting at a coffee shop. Avoid "First, Second, Third". Use "you know, honestly, yeah, right, basically".

3. **Pure Dialog Only:** The dialog field contains only the dialogue content, no role prefixes. No "Host:", "Expert:", "Speaker:" labels.

4. **No Self-Reference by Name:** Speakers must not mention their own names in dialogue. The female host must not say "I am the host" or mention her own name. The male host must not say "as an expert" or mention his own name. Names can only be brought up by the other person (greetings, asking opinions, etc.).

5. **Random Turn Pattern:** Two speakers alternate naturally, like a real conversation rhythm.

6. **Duration:** Approximately 3-5 minutes of dialogue, substantive content.
</guidelines>

<output_format>
{{
"podcast_transcripts": [
  {{
    "speaker_id": 0,
    "dialog": "Hey everyone, welcome back to the show! Today we're diving into"
  }},
  {{
    "speaker_id": 1,
    "dialog": "Yeah, this is a really interesting topic. Let me break it down for you"
  }}
]
}}
</output_format>
</podcast_generation_system>

Transform the source material into a lively and engaging podcast conversation. The final output is a JSON string without code blocks. No explanatory text!
"""

# Fish Audio voice IDs
SPEAKER_VOICES = {
    0: "933563129e564b19a115bedd57b7406a",  # Sarah - female
    1: "536d3a5e000945adb7038665781a4aca",   # Ethan - male
}

FISH_API_KEY = os.environ.get("FISH_API_KEY", "")
FISH_MODEL = "s2.1-pro-free"

def fish_tts(text, voice_id, output_path):
    """Call Fish Audio TTS API"""
    import urllib.request, urllib.error

    payload = json.dumps({
        "text": text,
        "reference_id": voice_id,
        "format": "mp3",
        "latency": "normal"
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.fish.audio/v1/tts",
        data=payload,
        headers={
            "Authorization": f"Bearer {FISH_API_KEY}",
            "Content-Type": "application/json",
            "model": FISH_MODEL,
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            with open(output_path, "wb") as f:
                f.write(data)
            return True
    except Exception as e:
        print(f"TTS error: {e}", file=sys.stderr)
        return False


def fetch_article_content(url, target_link=None):
    """Fetch article content from RSS feed"""
    feed = feedparser.parse(url)
    if not feed.entries:
        return None, None, "", None

    if target_link:
        for entry in feed.entries:
            if entry.get("link") == target_link:
                content = ""
                if hasattr(entry, "content") and entry.content:
                    content = entry.content[0].value
                elif hasattr(entry, "summary"):
                    content = entry.summary
                else:
                    content = entry.get("description", "")
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                return entry.title, content, entry.get("link", ""), published
        print(f"WARNING: target_link not found, falling back to entry[0]")

    entry = feed.entries[0]
    content = ""
    if hasattr(entry, "content") and entry.content:
        content = entry.content[0].value
    elif hasattr(entry, "summary"):
        content = entry.summary
    else:
        content = entry.get("description", "")
    published = None
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        published = datetime(*entry.published_parsed[:6])
    return entry.title, content, entry.get("link", ""), published


def generate_script(title, content, api_key=None, base_url=None, model=None):
    """Call LLM API to generate podcast script"""
    try:
        import openai
    except ImportError:
        print("ERROR: openai not installed. Run: pip install openai")
        return None, None

    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        print("ERROR: OPENAI_API_KEY not set")
        return None, None

    url = base_url or os.environ.get("LLM_BASE_URL", "https://apihub.agnes-ai.com/v1")
    model_name = model or os.environ.get("LLM_MODEL", "agnes-2.0-flash")

    print(f"Using LLM: {model_name} via {url}")

    client = openai.OpenAI(api_key=key, base_url=url)

    prompt = PODCAST_PROMPT_TEMPLATE.replace("{{content}}", content[:4000])

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a professional English podcast scriptwriter."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=3000,
        temperature=0.7
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'^```\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    try:
        data = json.loads(raw)
        transcripts = data.get("podcast_transcripts", [])
        print(f"Parsed {len(transcripts)} dialogue segments")
        return transcripts, raw
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw: {raw[:300]}")
        return None, raw


def has_intro_outro():
    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    return os.path.exists(os.path.join(template_dir, "intro.mp3")) and \
           os.path.exists(os.path.join(template_dir, "outro.mp3"))


def add_intro_outro(input_mp3, output_mp3):
    """Add intro/outro music with fade in/out"""
    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    intro = os.path.join(template_dir, "intro.mp3")
    outro = os.path.join(template_dir, "outro.mp3")

    if not (os.path.exists(intro) and os.path.exists(outro)):
        shutil.copy2(input_mp3, output_mp3)
        return

    concat_file = output_mp3 + ".concat.txt"
    with open(concat_file, "w") as f:
        f.write(f"file '{os.path.abspath(intro)}'\n")
        f.write(f"file '{os.path.abspath(input_mp3)}'\n")
        f.write(f"file '{os.path.abspath(outro)}'\n")

    result = subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-filter_complex",
        "[0]afade=t=in:st=0:d=1[intro];[1]apad=whole_dur=1[content];[2]afade=t=out:st=0:d=1[outro];[intro][content][outro]concat=n=3:v=0:a=1[out]",
        "-map", "[out]",
        "-codec:a", "libmp3lame", "-b:a", "128k",
        output_mp3
    ], capture_output=True, text=True)

    if result.returncode != 0:
        result = subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-codec:a", "libmp3lame", "-b:a", "128k",
            output_mp3
        ], capture_output=True, text=True)

    os.remove(concat_file)
    if result.returncode == 0:
        print("Added intro/outro music to final output")
    else:
        print(f"Intro/outro merge note: {result.stderr[:100]}")


def make_episode_id(article_date, link, title):
    import re as _re
    date_str = article_date.strftime("%Y%m%d") if article_date else datetime.now().strftime("%Y%m%d")
    m = _re.search(r'/archives/([\w-]+)', link)
    if m:
        slug = m.group(1)
    else:
        slug = _re.sub(r'[^\w\-\uff00]+', '_', title)[:30]
    return f"{date_str}_{slug}"


def main():
    parser = argparse.ArgumentParser(description="Generate English osp.io podcast with Fish Audio")
    parser.add_argument("--title", help="Article title")
    parser.add_argument("--link", help="Article link")
    parser.add_argument("--auto", action="store_true", help="Auto-fetch latest article from RSS")
    parser.add_argument("--api-key", help="API Key (default from OPENAI_API_KEY env)")
    parser.add_argument("--base-url", default="https://apihub.agnes-ai.com/v1", help="API Base URL")
    parser.add_argument("--model", default="agnes-2.0-flash", help="Model name")
    parser.add_argument("--output-dir", default="episodes", help="Output directory")
    args = parser.parse_args()

    if not FISH_API_KEY:
        print("ERROR: FISH_API_KEY not set")
        sys.exit(1)

    STATE_FILE = "last_article.json"
    target_link = None

    if args.link:
        target_link = args.link
    elif os.environ.get("NEW_ARTICLE_LINK"):
        target_link = os.environ["NEW_ARTICLE_LINK"]
    else:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE) as f:
                queue = json.load(f)
            if isinstance(queue, list) and queue:
                target_link = queue[0]["link"]
                remaining = queue[1:]
                with open(STATE_FILE, "w") as f:
                    json.dump(remaining, f, ensure_ascii=False, indent=2)
                print(f"Queue: processing first of {len(queue)}, {len(remaining)} remaining")

    if not target_link:
        print("ERROR: no article link (need --link or NEW_ARTICLE_LINK or queue in last_article.json)")
        sys.exit(1)

    title, article_content, link, article_date = fetch_article_content("https://osp.io/feed", target_link=target_link)
    if not title:
        print("ERROR: cannot fetch article content")
        sys.exit(1)
    print(f"Article: {title}")

    print("Generating podcast script...")
    transcripts, raw_script = generate_script(
        title, article_content,
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model
    )

    if not transcripts:
        print("ERROR: script generation failed, skipping")
        sys.exit(0)

    episode_id = make_episode_id(article_date, link, title)
    print(f"Episode ID: {episode_id}")

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    temp_files = []
    for i, item in enumerate(transcripts):
        speaker_id = item.get("speaker_id", 0)
        text = item.get("dialog", "").strip()
        if not text:
            continue
        voice_id = SPEAKER_VOICES.get(speaker_id, SPEAKER_VOICES[0])
        temp_file = os.path.join(output_dir, f"temp_{episode_id}_{i}.mp3")
        temp_files.append((speaker_id, voice_id, temp_file, text))

    print(f"Generating {len(temp_files)} audio segments via Fish Audio...")

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(fish_tts, text, voice_id, temp_file): (speaker_id, text[:40])
            for speaker_id, voice_id, temp_file, text in temp_files
        }
        for future in concurrent.futures.as_completed(futures):
            speaker_id, snippet = futures[future]
            try:
                success = future.result()
                role = "Female" if speaker_id == 0 else "Male"
                print(f"  [{'✓' if success else '✗'}] {role}: {snippet}...")
            except Exception as e:
                print(f"  [✗] {e}")

    # Merge audio
    concat_file = os.path.join(output_dir, f"concat_{episode_id}.txt")
    with open(concat_file, "w") as f:
        for _, _, temp_file, _ in temp_files:
            if os.path.exists(temp_file):
                f.write(f"file '{os.path.abspath(temp_file)}'\n")

    content_mp3 = os.path.join(output_dir, f"content_{episode_id}.mp3")
    result = subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file, "-codec:a", "libmp3lame", "-b:a", "128k", content_mp3
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FFmpeg merge error: {result.stderr}")
        sys.exit(1)

    # Cleanup temp files
    for _, _, temp_file, _ in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    os.remove(concat_file)

    # Add intro/outro
    final_mp3 = os.path.join(output_dir, f"episode_{episode_id}.mp3")
    print("Adding intro/outro music...")
    add_intro_outro(content_mp3, final_mp3)

    if os.path.exists(content_mp3):
        os.remove(content_mp3)

    print(f"Podcast generated: {final_mp3}")
    print(f"File size: {os.path.getsize(final_mp3) / 1024:.1f} KB")

    meta = {
        "id": episode_id,
        "title": title,
        "link": link,
        "date": article_date.isoformat() if article_date else datetime.now().isoformat(),
        "audio_file": os.path.basename(final_mp3),
        "file_size_kb": os.path.getsize(final_mp3) // 1024,
        "num_segments": len(temp_files),
        "has_intro_outro": has_intro_outro(),
        "script": raw_script[:1000] if raw_script else ""
    }
    with open(os.path.join(output_dir, f"episode_{episode_id}.json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
