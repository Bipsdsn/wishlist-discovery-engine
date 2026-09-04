"""
Data collectors for the Discovery Engine.

Sources:
  1. Google Play Store reviews  (google-play-scraper, no API key needed)
  2. Apple App Store reviews    (public iTunes RSS JSON, no API key needed)
  3. Reddit posts + comments    (public .json endpoints, no API key needed)

Output: data/raw_corpus.csv with columns:
  source, source_detail, text, rating, date, url
"""

import csv
import json
import os
import time

import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (research; wishlist-discovery-engine/1.0)"}


# ---------------------------------------------------------------- Play Store
def collect_play_store(app_id="com.myntra.android", n=3000):
    from google_play_scraper import Sort, reviews

    rows, token = [], None
    while len(rows) < n:
        batch, token = reviews(
            app_id, lang="en", country="in",
            sort=Sort.NEWEST, count=min(200, n - len(rows)),
            continuation_token=token,
        )
        if not batch:
            break
        for r in batch:
            rows.append({
                "source": "play_store",
                "source_detail": app_id,
                "text": (r.get("content") or "").strip(),
                "rating": r.get("score"),
                "date": str(r.get("at") or "")[:10],
                "url": "",
            })
        if token is None:
            break
    print(f"  play_store: {len(rows)} reviews")
    return rows


# ----------------------------------------------------------------- App Store
def _find_ios_app_id(term="myntra"):
    r = requests.get(
        "https://itunes.apple.com/search",
        params={"term": term, "country": "in", "entity": "software", "limit": 5},
        headers=UA, timeout=30,
    )
    for item in r.json().get("results", []):
        if term.lower() in item.get("trackName", "").lower():
            return item["trackId"]
    return None


def collect_app_store(term="myntra", pages=10):
    rows = []
    app_id = _find_ios_app_id(term)
    if not app_id:
        print("  app_store: app id not found, skipping")
        return rows
    for page in range(1, pages + 1):
        url = (f"https://itunes.apple.com/in/rss/customerreviews/"
               f"page={page}/id={app_id}/sortby=mostrecent/json")
        try:
            r = requests.get(url, headers=UA, timeout=30)
            entries = r.json().get("feed", {}).get("entry", [])
        except Exception:
            break
        if not entries:
            break
        for e in entries:
            if "im:rating" not in e:  # first entry is app metadata
                continue
            rows.append({
                "source": "app_store",
                "source_detail": str(app_id),
                "text": (e.get("content", {}).get("label") or "").strip(),
                "rating": int(e["im:rating"]["label"]),
                "date": "",
                "url": "",
            })
        time.sleep(0.5)
    print(f"  app_store: {len(rows)} reviews")
    return rows


# -------------------------------------------------------------------- Reddit
REDDIT_QUERIES = [
    ("IndianFashionAddicts", "wishlist"),
    ("IndianFashionAddicts", "myntra"),
    ("IndianFashionAddicts", "should I buy"),
    ("IndianFashionAddicts", "size"),
    ("onlineshopping", "myntra"),
    ("india", "myntra wishlist"),
    ("IndianTeenagers", "myntra"),
    ("FrugalIndia", "myntra sale"),
    ("fashionadvice", "wishlist can't decide"),
]


def _reddit_search(subreddit, query, limit=50):
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {"q": query, "restrict_sr": 1, "limit": limit, "sort": "relevance"}
    r = requests.get(url, params=params, headers=UA, timeout=30)
    if r.status_code != 200:
        return []
    return r.json().get("data", {}).get("children", [])


def _reddit_comments(permalink, max_comments=40):
    url = f"https://www.reddit.com{permalink}.json"
    try:
        r = requests.get(url, headers=UA, params={"limit": max_comments}, timeout=30)
        if r.status_code != 200:
            return []
        out = []

        def walk(children):
            for c in children:
                d = c.get("data", {})
                body = d.get("body")
                if body and len(body) > 20:
                    out.append(body)
                replies = d.get("replies")
                if isinstance(replies, dict):
                    walk(replies.get("data", {}).get("children", []))

        if len(r.json()) > 1:
            walk(r.json()[1].get("data", {}).get("children", []))
        return out[:max_comments]
    except Exception:
        return []


def collect_reddit(deep=True):
    rows, seen = [], set()
    for subreddit, query in REDDIT_QUERIES:
        for child in _reddit_search(subreddit, query):
            d = child.get("data", {})
            pid = d.get("id")
            if pid in seen:
                continue
            seen.add(pid)
            text = f"{d.get('title', '')}. {d.get('selftext', '')}".strip()
            permalink = d.get("permalink", "")
            rows.append({
                "source": "reddit",
                "source_detail": f"r/{subreddit}",
                "text": text[:3000],
                "rating": "",
                "date": "",
                "url": f"https://www.reddit.com{permalink}",
            })
            if deep and permalink:
                for body in _reddit_comments(permalink):
                    rows.append({
                        "source": "reddit_comment",
                        "source_detail": f"r/{subreddit}",
                        "text": body[:3000],
                        "rating": "",
                        "date": "",
                        "url": f"https://www.reddit.com{permalink}",
                    })
                time.sleep(1)
        time.sleep(1)
    print(f"  reddit: {len(rows)} posts+comments")
    return rows


# --------------------------------------------------------------------- main
def main():
    corpus = []
    print("Collecting…")
    try:
        corpus += collect_play_store()
    except Exception as e:
        print(f"  play_store FAILED: {e}")
    try:
        corpus += collect_app_store()
    except Exception as e:
        print(f"  app_store FAILED: {e}")
    try:
        corpus += collect_reddit()
    except Exception as e:
        print(f"  reddit FAILED: {e}")

    # dedupe + drop empty/too-short
    seen, clean = set(), []
    for row in corpus:
        t = " ".join(row["text"].split())
        if len(t) < 15:
            continue
        key = t[:120].lower()
        if key in seen:
            continue
        seen.add(key)
        row["text"] = t
        clean.append(row)

    out = os.path.join(DATA_DIR, "raw_corpus.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["source", "source_detail", "text",
                                          "rating", "date", "url"])
        w.writeheader()
        w.writerows(clean)
    print(f"Saved {len(clean)} unique items -> {out}")


if __name__ == "__main__":
    main()
