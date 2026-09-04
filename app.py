"""
Wishlist -> Purchase Discovery Engine — public testable interface.

Run locally:   streamlit run app.py
Deploy:        Streamlit Community Cloud (share.streamlit.io) — free, public URL.

Two panels:
  1. Opportunity Explorer — the ranked friction map computed from the corpus
     (interactive: filter by source, KPI node, addressability).
  2. Live Classifier — paste any user text (review / reddit comment / chat)
     and the engine tags it against the taxonomy in real time, so evaluators
     can *test* the engine, not just read its output.
"""

import os

import pandas as pd
import streamlit as st

from taxonomy import TAXONOMY, DECISION_JOURNEY_THEMES
from tagger import tag_rule

DATA = os.path.join(os.path.dirname(__file__), "data")

st.set_page_config(page_title="Wishlist Discovery Engine", layout="wide")
st.title("Wishlist → Purchase Discovery Engine")
st.caption(
    "AI-powered analysis of public user conversations (Play Store, App Store, "
    "Reddit) to identify, quantify and rank the frictions that stop wishlisted "
    "fashion items from being purchased. Built for the Myntra wishlist-to-"
    "purchase conversion problem."
)

tab_map, tab_live, tab_how = st.tabs(
    ["📊 Opportunity Map", "🔍 Live Classifier (test me)", "⚙️ How it works"]
)

# ------------------------------------------------------------ Opportunity map
with tab_map:
    summary_path = os.path.join(DATA, "theme_summary.csv")
    corpus_path = os.path.join(DATA, "tagged_corpus.csv")
    if not os.path.exists(summary_path):
        st.warning("No analysis found. Run collect.py → tagger.py → analyze.py first.")
    else:
        df = pd.read_csv(summary_path)
        corpus = pd.read_csv(corpus_path)

        c1, c2, c3 = st.columns(3)
        c1.metric("Corpus size", f"{len(corpus):,} items")
        c2.metric("Themes tracked", len(TAXONOMY))
        c3.metric("Tagging mode", corpus["mode"].iloc[0])

        col_a, col_b = st.columns(2)
        node = col_a.multiselect(
            "KPI node", sorted(df["kpi_node"].unique()),
            default=sorted(df["kpi_node"].unique()))
        only_addr = col_b.checkbox(
            "Only opportunities addressable WITHOUT monetary incentives", True)

        view = df[df["kpi_node"].isin(node)]
        if only_addr:
            view = view[view["addressable_without_incentives"]]

        st.subheader("Ranked opportunity areas")
        st.dataframe(
            view[["label", "kpi_node", "mentions", "share_of_decision_journey",
                  "avg_severity", "opportunity_score"]]
            .rename(columns={
                "label": "Friction theme", "kpi_node": "KPI node",
                "mentions": "Friction mentions",
                "share_of_decision_journey": "Share of decision journey",
                "avg_severity": "Avg severity (1–3)",
                "opportunity_score": "Opportunity score"}),
            use_container_width=True, hide_index=True)

        st.bar_chart(view.set_index("label")["opportunity_score"])

        st.subheader("Read the evidence")
        theme_pick = st.selectbox(
            "Theme", view["theme"].tolist(),
            format_func=lambda t: TAXONOMY[t]["label"])
        hits = corpus[corpus["themes"].fillna("").str.contains(theme_pick)]
        st.write(f"{len(hits)} tagged items (showing up to 25):")
        st.dataframe(hits[["source", "rating", "text"]].head(25),
                     use_container_width=True, hide_index=True)

# ------------------------------------------------------------ Live classifier
with tab_live:
    st.write(
        "Paste any user text — an app review, a Reddit comment, a WhatsApp "
        "message about a purchase decision — and the engine will tag the "
        "frictions it detects.")
    sample = ("I've had this kurta in my wishlist for 3 weeks. I love it but "
              "I'm between M and L and the size chart makes no sense, and "
              "there are only 2 reviews with no photos. Sent screenshots to "
              "my sister, she says buy, but I don't know what to wear it with.")
    text = st.text_area("User text", value=sample, height=140)
    if st.button("Analyze", type="primary"):
        themes = tag_rule(text)
        if not themes:
            st.info("No taxonomy theme detected — candidate for open coding.")
        for t in themes:
            spec = TAXONOMY[t]
            badge = ("✅ addressable without incentives"
                     if spec["addressable"] else "🚫 needs monetary/ops lever")
            st.success(f"**{spec['label']}** — {spec['kpi_node']} — {badge}\n\n"
                       f"{spec['description']}")
        st.caption(
            "Live tagging runs the deterministic rule layer. The batch "
            "pipeline upgrades to LLM multi-label classification when an "
            "ANTHROPIC_API_KEY / OPENAI_API_KEY is configured.")

# ----------------------------------------------------------------- How-to tab
with tab_how:
    st.markdown("""
### Pipeline
```
[Collect]                 [Tag]                   [Analyze]              [Serve]
Play Store reviews  ─┐    LLM multi-label         Friction filter        This app
App Store reviews   ─┼──▶ classification     ──▶  (excludes praise) ──▶  Ranked map +
Reddit posts+comments┘    vs 14-theme taxonomy    Score = share ×        live classifier
                          (rule fallback)         severity × addressability
```

### Why this is more than sentiment analysis
1. **Taxonomy grounded in the business metric** — every theme maps to a node of
   the wishlist→purchase KPI tree (A composition / B re-engagement / C decision
   progression / D transaction).
2. **Quantified & ranked** — themes are scored by frequency share × severity ×
   addressability-without-monetary-incentives, producing an opportunity map,
   not a word cloud.
3. **Friction-only counting** — praise reviews containing theme words are
   excluded via rating + language signals.
4. **Testable** — the Live Classifier tab lets anyone probe the engine with
   their own text.
""")
