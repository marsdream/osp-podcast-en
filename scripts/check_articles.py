#!/usr/bin/env python3
"""Check for new articles on osp.io and save to queue"""
import os, json, feedparser

RSS_URL = "https://osp.io/feed"
STATE_FILE = "last_article.json"

def get_latest_article():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return None
    entry = feed.entries[0]
    return {
        "title": entry.get("title", ""),
        "link": entry.get("link", ""),
    }

if __name__ == "__main__":
    article = get_latest_article()
    if not article:
        print("No articles found in RSS")
        print("has_new=false")
        exit(1)

    # Load existing queue
    existing_links = []
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            existing = json.load(f)
        if isinstance(existing, list):
            existing_links = [a["link"] for a in existing]
        elif isinstance(existing, dict):
            existing_links = [existing.get("link", "")]

    if article["link"] in existing_links:
        print(f"Article already in queue: {article['title']}")
        print("has_new=false")
        print("::set-output name=has_new::false")
        exit(0)

    # Prepend new article to queue
    queue = [article]
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            old = json.load(f)
        if isinstance(old, list):
            for a in old:
                if a["link"] not in [q["link"] for q in queue]:
                    queue.append(a)
        elif isinstance(old, dict) and old.get("link") not in [q["link"] for q in queue]:
            queue.append(old)

    with open(STATE_FILE, "w") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)

    print(f"Queued: {article['title']}")
    print("has_new=true")
    print("::set-output name=has_new::true")
