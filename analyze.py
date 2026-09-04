"""
Analyzer: turns the tagged corpus into the ranked Opportunity Map.

Opportunity score per theme =
    frequency_share (0-1, share of decision-journey mentions)
  x severity        (1-3, avg negativity: low ratings / complaint language)
  x addressability  (1 if movable without monetary incentives, 0.25 if not)

Outputs:
  data/theme_summary.csv     - counts, shares, severity, score per theme
  data/opportunity_map.md    - human-readable ranked map with example quotes
"""

import csv
import os
from collections import defaultdict

from taxonomy import TAXONOMY, DECISION_JOURNEY_THEMES

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

COMPLAINT_WORDS = ("worst", "bad", "terrible", "waste", "never", "disappointed",
                   "pathetic", "cheat", "fraud", "poor", "horrible", "scam")

NEGATIVE_HINTS = COMPLAINT_WORDS + (
    "issue", "problem", "wrong", "not able", "unable", "confus", "don't know",
    "dont know", "no option", "difficult", "can't", "cant ", "didn't", "didnt",
    "not as", "different from", "return", "refund", "fake", "misleading",
    "why ", "how do", "which size", "not sure", "unsure", "doubt", "wish there",
    "should i", "help me", "?",
)


def is_friction(row):
    """Only count a theme mention as friction when the item shows a negative,
    uncertain, or help-seeking signal — filters out praise reviews that merely
    contain theme words ('quality is great, fitting is perfect')."""
    rating = (row.get("rating") or "").strip()
    text = row["text"].lower()
    if rating.isdigit():
        r = int(rating)
        if r <= 3:
            return True
        # high-star review: count only with explicit complaint language
        return any(w in text for w in COMPLAINT_WORDS)
    # unrated content (reddit/forums): need a negative/uncertainty hint
    return any(h in text for h in NEGATIVE_HINTS)


def severity(row):
    """1 (mild) to 3 (severe)."""
    s = 1.0
    rating = row.get("rating")
    if rating and rating.strip().isdigit():
        r = int(rating)
        if r <= 2:
            s += 1.0
        elif r == 3:
            s += 0.5
    text = row["text"].lower()
    if any(w in text for w in COMPLAINT_WORDS):
        s += 1.0
    return min(s, 3.0)


def main():
    src = os.path.join(DATA_DIR, "tagged_corpus.csv")
    with open(src, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    counts = defaultdict(int)
    sev_sum = defaultdict(float)
    quotes = defaultdict(list)
    src_counts = defaultdict(lambda: defaultdict(int))

    total_theme_mentions = 0
    skipped_positive = 0
    for row in rows:
        themes = [t for t in row["themes"].split("|") if t]
        if themes and not is_friction(row):
            skipped_positive += 1
            continue
        s = severity(row)
        for t in themes:
            counts[t] += 1
            sev_sum[t] += s
            src_counts[t][row["source"]] += 1
            total_theme_mentions += 1
            if len(quotes[t]) < 5 and 40 < len(row["text"]) < 300:
                quotes[t].append((row["source"], row["text"]))

    dj_total = sum(counts[t] for t in DECISION_JOURNEY_THEMES) or 1

    results = []
    for theme, spec in TAXONOMY.items():
        n = counts[theme]
        if n == 0:
            continue
        share = (n / dj_total) if theme in DECISION_JOURNEY_THEMES else 0.0
        avg_sev = sev_sum[theme] / n
        addr = 1.0 if spec["addressable"] else 0.25
        score = round(share * avg_sev * addr * 100, 2)
        results.append({
            "theme": theme, "label": spec["label"], "kpi_node": spec["kpi_node"],
            "mentions": n, "share_of_decision_journey": round(share, 3),
            "avg_severity": round(avg_sev, 2),
            "addressable_without_incentives": spec["addressable"],
            "opportunity_score": score,
        })
    results.sort(key=lambda r: r["opportunity_score"], reverse=True)

    # CSV
    out_csv = os.path.join(DATA_DIR, "theme_summary.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    # Markdown opportunity map
    out_md = os.path.join(DATA_DIR, "opportunity_map.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Opportunity Map — Wishlist → Purchase Friction (auto-generated)\n\n")
        f.write(f"Corpus: **{len(rows)} items** | friction mentions counted: "
                f"{total_theme_mentions} | positive/praise items excluded: "
                f"{skipped_positive} | tagging mode: {rows[0].get('mode', '?')}\n\n")
        f.write("Score = share of decision-journey mentions × avg severity (1–3) "
                "× addressability without incentives (1.0 / 0.25) × 100\n\n")
        f.write("| # | Theme | KPI node | Mentions | Share | Severity | "
                "Addressable | Score |\n|---|---|---|---|---|---|---|---|\n")
        for i, r in enumerate(results, 1):
            f.write(f"| {i} | {r['label']} | {r['kpi_node']} | {r['mentions']} | "
                    f"{r['share_of_decision_journey']:.1%} | {r['avg_severity']} | "
                    f"{'yes' if r['addressable_without_incentives'] else 'NO'} | "
                    f"**{r['opportunity_score']}** |\n")
        f.write("\n## Source mix per theme\n\n")
        for r in results:
            mix = ", ".join(f"{s}: {c}" for s, c in
                            sorted(src_counts[r["theme"]].items(),
                                   key=lambda x: -x[1]))
            f.write(f"- **{r['label']}** — {mix}\n")
        f.write("\n## Representative verbatims\n\n")
        for r in results:
            f.write(f"### {r['label']}\n")
            for src_name, q in quotes[r["theme"]]:
                f.write(f"- ({src_name}) \"{q}\"\n")
            f.write("\n")

    print(f"Saved -> {out_csv}")
    print(f"Saved -> {out_md}\n")
    print("TOP OPPORTUNITIES:")
    for r in results[:6]:
        print(f"  {r['opportunity_score']:>7}  {r['label']}  "
              f"({r['mentions']} mentions, node {r['kpi_node'][:1]})")


if __name__ == "__main__":
    main()
