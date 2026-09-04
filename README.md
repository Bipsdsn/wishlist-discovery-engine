# Wishlist → Purchase Discovery Engine

AI-powered discovery system that analyzes public user conversations at scale to
identify, quantify, and rank the frictions preventing wishlisted fashion items
from being purchased (Myntra focus). Deliverable #1 of the PM Fellowship
graduation project.

## Pipeline

```
collect.py  →  tagger.py  →  analyze.py  →  app.py (Streamlit UI)
(scrape)       (classify)     (score+rank)    (public testable link)
```

1. **collect.py** — scrapes Google Play reviews (google-play-scraper), Apple
   App Store reviews (public iTunes RSS), and Reddit posts/comments (public
   JSON). Dedupes into `data/raw_corpus.csv`.
2. **tagger.py** — multi-label classification of every item against a 14-theme
   friction taxonomy (`taxonomy.py`). Uses an LLM (Claude/GPT) when
   `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is set; otherwise a deterministic
   keyword rule layer (also used as LLM fallback/validation).
3. **analyze.py** — counts only *friction* mentions (praise filtered via
   rating + complaint-language signals), scores each theme:
   `share of decision-journey mentions × avg severity (1–3) × addressability
   without monetary incentives (1.0/0.25) × 100`, and writes the ranked
   opportunity map.
4. **app.py** — Streamlit interface: interactive opportunity map, evidence
   drill-down, and a live classifier so evaluators can test the engine with
   their own text.

## Run locally

```bash
pip install -r requirements.txt
python collect.py        # ~5 min; needs internet
python tagger.py         # set ANTHROPIC_API_KEY or OPENAI_API_KEY for LLM mode
python analyze.py
streamlit run app.py
```

## Deploy (public link — required deliverable)

1. Push this folder to a public GitHub repo (include `data/` outputs).
2. Go to https://share.streamlit.io → New app → pick the repo, main file `app.py`.
3. (Optional) add `ANTHROPIC_API_KEY` in app Secrets for LLM mode.
4. Verify the URL opens in an incognito window before submitting.

## Known constraints of the current run

- **Reddit collection returned 0 from this network** (Reddit 403-blocks
  non-residential IPs). The collector works as written — re-run
  `python collect.py` from a home network to add the community lane, which is
  where wishlist-decision talk (vs post-purchase complaints) lives.
- **Current tagging mode: rules** (no LLM key in this environment). For the
  submission run, set an API key and re-run `tagger.py` + `analyze.py`.
- Store reviews skew toward post-purchase/ops complaints; the friction filter
  and the taxonomy's control themes (app UX, delivery/returns) quarantine that
  bias, but the Reddit + LLM run is what fully balances the corpus.
