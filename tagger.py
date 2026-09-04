"""
Tagger: assigns friction themes (multi-label) to each corpus item.

Two modes:
  - LLM mode (default when ANTHROPIC_API_KEY or OPENAI_API_KEY is set):
    batches items into an LLM with the taxonomy descriptions and asks for
    multi-label classification + an intent signal. This is the mode the
    deployed engine runs in.
  - Rule mode (fallback, no key needed): keyword/phrase matching against the
    taxonomy seed patterns. Deterministic, transparent, used to validate the
    LLM and to keep the pipeline runnable anywhere.

Output: data/tagged_corpus.csv = raw columns + themes (|-joined) + mode
"""

import csv
import json
import os
import re
import sys

from taxonomy import TAXONOMY

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# ---------------------------------------------------------------- rule mode
def _compile_patterns():
    compiled = {}
    for theme, spec in TAXONOMY.items():
        pats = [re.compile(r"\b" + re.escape(k).replace(r"\ ", r"\s+") + r"\b",
                           re.IGNORECASE) for k in spec["keywords"]]
        compiled[theme] = pats
    return compiled


_PATTERNS = _compile_patterns()


def tag_rule(text):
    themes = []
    for theme, pats in _PATTERNS.items():
        if any(p.search(text) for p in pats):
            themes.append(theme)
    return themes


# ----------------------------------------------------------------- LLM mode
LLM_SYSTEM = (
    "You are a product-research classifier for an Indian fashion e-commerce "
    "wishlist study. For each numbered text, return the matching theme ids "
    "(multi-label, can be empty). Only use these theme ids:\n"
    + "\n".join(f"- {t}: {s['description']}" for t, s in TAXONOMY.items())
    + "\nRespond with pure JSON: {\"<item number>\": [\"theme_id\", ...], ...}"
)


def _llm_call(batch_texts):
    """batch_texts: list[str] -> dict[index -> list[theme]]"""
    numbered = "\n".join(f"{i}. {t[:500]}" for i, t in enumerate(batch_texts))
    if os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-4-5", max_tokens=2000,
            system=LLM_SYSTEM,
            messages=[{"role": "user", "content": numbered}],
        )
        raw = msg.content[0].text
    elif os.environ.get("OPENAI_API_KEY"):
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": LLM_SYSTEM},
                      {"role": "user", "content": numbered}],
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content
    else:
        raise RuntimeError("no LLM key")
    raw = raw[raw.find("{"): raw.rfind("}") + 1]
    parsed = json.loads(raw)
    valid = set(TAXONOMY)
    return {int(k): [t for t in v if t in valid] for k, v in parsed.items()}


def tag_llm(texts, batch_size=25):
    out = [None] * len(texts)
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        try:
            result = _llm_call(batch)
        except Exception as e:
            print(f"  LLM batch {start} failed ({e}); falling back to rules")
            result = {i: tag_rule(t) for i, t in enumerate(batch)}
        for i, t in enumerate(batch):
            out[start + i] = result.get(i, tag_rule(t))
        print(f"  tagged {min(start + batch_size, len(texts))}/{len(texts)}")
    return out


# --------------------------------------------------------------------- main
def main():
    src = os.path.join(DATA_DIR, "raw_corpus.csv")
    with open(src, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    use_llm = bool(os.environ.get("ANTHROPIC_API_KEY")
                   or os.environ.get("OPENAI_API_KEY"))
    if "--rules" in sys.argv:
        use_llm = False
    mode = "llm" if use_llm else "rules"
    print(f"Tagging {len(rows)} items in {mode} mode…")

    if use_llm:
        theme_lists = tag_llm([r["text"] for r in rows])
    else:
        theme_lists = [tag_rule(r["text"]) for r in rows]

    out = os.path.join(DATA_DIR, "tagged_corpus.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        fields = list(rows[0].keys()) + ["themes", "mode"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row, themes in zip(rows, theme_lists):
            row["themes"] = "|".join(themes)
            row["mode"] = mode
            w.writerow(row)
    tagged = sum(1 for t in theme_lists if t)
    print(f"Saved -> {out}  ({tagged}/{len(rows)} items matched >=1 theme)")


if __name__ == "__main__":
    main()
