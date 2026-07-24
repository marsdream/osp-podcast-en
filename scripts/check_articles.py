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
    # Check if article already processed
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            queue = json.load(f)
        links = [a["link"] for a in queue] if isinstance(queue, list) else [queue.get("link", "")]
    else:
        links = []

    article = get_latest_article()
    if not article:
        print("No articles found in RSS")
        exit(1)

    if article["link"] in links:
        print(f"Article already in queue: {article['title']}")
        print("has_new=false")
        exit(0)

    # Save to queue
    queue = [article]
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            old = json.load(f)
        if isinstance(old, list):
            existing_links = [a["link"] for a in old]
            for a in old:
                if a["link"] not in existing_links:
                    queue.append(a)
        elif isinstance(old, dict) and old.get("link") not in [q["link"] for q in queue]:
            queue.append(old)

    with open(STATE_FILE, "w") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)

    print(f"Queued: {article['title']}")
    print(f"has_new=true")
