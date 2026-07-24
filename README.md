# osp-podcast-en

English-language podcast for osp.io — AI-generated conversations about open source and tech, powered by Fish Audio TTS.

**Site**: https://podcast-en.herebuy.us/

## How it works

- Fetches latest articles from osp.io RSS feed
- Generates English dialogue scripts via LLM
- Synthesizes audio using **Fish Audio s2.1-pro-free** API (free, unlimited)
- Deploys to GitHub Pages via Cloudflare CNAME

## Voices

- **Female (Host)**: Sarah — `933563129e564b19a115bedd57b7406a`
- **Male (Expert)**: Ethan — `536d3a5e000945adb7038665781a4aca`

## CI Schedule

Runs Mon/Wed/Fri at 10:00 Beijing time via GitHub Actions.

## Development

```bash
# Install dependencies
pip install feedparser openai

# Test locally
FISH_API_KEY=your_key OPENAI_API_KEY=your_key \
  python scripts/generate_podcast.py --auto
```

## Fish Audio Free Tier

`s2.1-pro-free` model is completely free for TTS — no credit card required.
