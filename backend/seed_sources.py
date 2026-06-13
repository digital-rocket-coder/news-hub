"""
Seed script: adds verified RSS feeds into a running backend.
Usage:
    python seed_sources.py
    python seed_sources.py --api https://your-railway-backend.railway.app
"""

import sys
import httpx

API = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--api" else "http://localhost:8000"

# All URLs verified live as of 2026-06
SOURCES = [
    # ── Russian tech & business ───────────────────────────────────────────────
    {
        "name": "Хабр",
        "url": "https://habr.com/ru/rss/all/all/",
        "category": "Tech/RU",
    },
    {
        "name": "vc.ru",
        "url": "https://vc.ru/rss",
        "category": "Tech/RU",
    },
    {
        "name": "ТАСС",
        "url": "https://tass.ru/rss/v2.xml",
        "category": "News/RU",
    },
    {
        "name": "Ведомости",
        "url": "https://www.vedomosti.ru/rss/news",
        "category": "Business/RU",
    },
    {
        "name": "tech.onliner.by",
        "url": "https://tech.onliner.by/feed",
        "category": "Tech/RU",
    },
    {
        "name": "4PDA",
        "url": "https://4pda.to/feed/",
        "category": "Tech/RU",
    },

    # ── English tech media ────────────────────────────────────────────────────
    {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
        "category": "Tech/EN",
    },
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "category": "Tech/EN",
    },
    {
        "name": "Wired",
        "url": "https://www.wired.com/feed/rss",
        "category": "Tech/EN",
    },
    {
        "name": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "category": "Tech/EN",
    },
    {
        "name": "Engadget",
        "url": "https://www.engadget.com/rss.xml",
        "category": "Tech/EN",
    },
    {
        "name": "The Guardian — Technology",
        "url": "https://www.theguardian.com/technology/rss",
        "category": "Tech/EN",
    },
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
        "category": "Tech/EN",
    },

    # ── AI research & platforms ───────────────────────────────────────────────
    {
        "name": "Google DeepMind Blog",
        "url": "https://deepmind.google/blog/rss.xml",
        "category": "AI",
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "category": "AI",
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "category": "AI",
    },
]


def main():
    added, skipped, failed = 0, 0, 0

    with httpx.Client(base_url=API, timeout=10) as client:
        try:
            existing = {s["url"] for s in client.get("/api/sources/").json()}
        except Exception as e:
            print(f"❌  Cannot reach backend at {API}: {e}")
            print("    Make sure the backend is running: uvicorn app.main:app --reload --port 8000")
            sys.exit(1)

        for src in SOURCES:
            if src["url"] in existing:
                print(f"⏭   skip  {src['name']}")
                skipped += 1
                continue
            try:
                r = client.post("/api/sources/", json=src)
                if r.status_code == 201:
                    print(f"✅  added  [{src['category']}] {src['name']}")
                    added += 1
                else:
                    print(f"⚠️   {r.status_code}  {src['name']}: {r.text[:120]}")
                    failed += 1
            except Exception as e:
                print(f"❌  error  {src['name']}: {e}")
                failed += 1

    print(f"\nDone: {added} added, {skipped} skipped, {failed} failed.")
    if added:
        print("Backend will start polling all sources in the background.")


if __name__ == "__main__":
    main()
