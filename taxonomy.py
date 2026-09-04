"""
Friction-theme taxonomy for the Wishlist -> Purchase Discovery Engine.

Each theme maps to:
  - kpi_node: node in the metric decomposition tree (A/B/C/D from Phase 1D)
  - addressable: can a Growth PM move this WITHOUT monetary incentives?
  - keywords: seed patterns for rule-based tagging (fallback + LLM validation)
  - description: used verbatim in the LLM tagging prompt
"""

TAXONOMY = {
    "size_fit_uncertainty": {
        "label": "Size & Fit Uncertainty",
        "kpi_node": "C - Decision progression",
        "addressable": True,
        "description": "User is unsure whether the item will fit them or how it will "
                       "look on their body: wrong size received, inconsistent size "
                       "charts across brands, 'runs small/large', fitting doubt.",
        "keywords": [
            "size chart", "sizing", "size issue", "wrong size", "runs small",
            "runs large", "too tight", "too loose", "doesn't fit", "didnt fit",
            "did not fit", "fitting", "fit issue", "measurement", "true to size",
            "size guide", "which size", "what size", "loose fit", "tight fit",
        ],
    },
    "quality_doubt": {
        "label": "Quality / Material Doubt",
        "kpi_node": "C - Decision progression",
        "addressable": True,
        "description": "User doubts fabric, stitching, durability, or overall product "
                       "quality before buying, or reports quality shock after buying.",
        "keywords": [
            "quality", "fabric", "material", "cheap material", "stitching",
            "after wash", "faded", "torn", "flimsy", "durable", "shrunk",
        ],
    },
    "image_reality_gap": {
        "label": "Image vs Reality Gap",
        "kpi_node": "C - Decision progression",
        "addressable": True,
        "description": "Product looks different from photos: colour mismatch, "
                       "different design, 'not as shown', model-vs-me gap.",
        "keywords": [
            "looks different", "different from picture", "different from image",
            "not as shown", "color is different", "colour is different",
            "different colour", "different color", "as shown in", "misleading photo",
            "photo is different", "picture is different", "looked better online",
        ],
    },
    "price_value_anxiety": {
        "label": "Price / Value Anxiety & Sale-Waiting",
        "kpi_node": "C - Decision progression",
        "addressable": False,  # core mechanism would be monetary; only info-framing is allowed
        "description": "User hesitates on worth-it-ness, waits for sales or price "
                       "drops, tracks discounts, feels the price is too high.",
        "keywords": [
            "waiting for sale", "wait for sale", "price drop", "price increased",
            "too expensive", "overpriced", "worth the price", "not worth",
            "discount", "coupon", "offer ended", "eors", "big billion", "price hike",
            "waiting for the price", "when sale", "costly",
        ],
    },
    "review_trust": {
        "label": "Review Trust & Information Gaps",
        "kpi_node": "C - Decision progression",
        "addressable": True,
        "description": "User cannot trust or find enough reviews: fake reviews, no "
                       "photo reviews, no fit feedback from similar buyers.",
        "keywords": [
            "fake review", "paid review", "no reviews", "reviews are fake",
            "cant trust reviews", "can't trust reviews", "misleading reviews",
            "review photos", "genuine review",
        ],
    },
    "comparison_paralysis": {
        "label": "Comparison Paralysis / Too Many Options",
        "kpi_node": "C - Decision progression",
        "addressable": True,
        "description": "User has shortlisted several similar items and cannot choose "
                       "between them; choice overload; endless browsing without deciding.",
        "keywords": [
            "cant decide", "can't decide", "cannot decide", "too many options",
            "confused between", "which one should", "shortlisted", "so many similar",
            "help me choose", "torn between", "compare products", "no compare",
        ],
    },
    "wishlist_bookmark_behavior": {
        "label": "Wishlist as Bookmark / Moodboard (low intent)",
        "kpi_node": "A - Composition quality",
        "addressable": True,
        "description": "User uses the wishlist as a bookmark, moodboard, inspiration "
                       "board, or price-watch list rather than a to-buy list.",
        "keywords": [
            "wishlist", "wish list", "save for later", "saved items", "shortlist",
            "moodboard", "bookmarking", "just saving", "window shopping",
        ],
    },
    "stock_size_unavailability": {
        "label": "Stock-out / Size Unavailability",
        "kpi_node": "A - Composition quality",
        "addressable": True,  # via alerts/alternatives, non-monetary
        "description": "Item or the user's size went out of stock while they were "
                       "deciding; size never available.",
        "keywords": [
            "out of stock", "sold out", "size not available", "size unavailable",
            "my size", "restock", "back in stock", "unavailable",
        ],
    },
    "delivery_return_fear": {
        "label": "Delivery / Return / Refund Fear",
        "kpi_node": "D - Transaction completion",
        "addressable": False,  # ops-owned, not Growth-PM movable in this project
        "description": "Fear or bad experience with delivery time, returns, exchanges "
                       "or refunds that suppresses willingness to order.",
        "keywords": [
            "return policy", "refund", "return rejected", "exchange", "pickup",
            "delivery late", "late delivery", "never delivered", "return issue",
            "no return", "non returnable", "replacement",
        ],
    },
    "styling_occasion_doubt": {
        "label": "Styling / Occasion / Will-it-suit-me Doubt",
        "kpi_node": "C - Decision progression",
        "addressable": True,
        "description": "User is unsure how to style the item, what to pair it with, "
                       "whether it suits their body/complexion, or fits the occasion.",
        "keywords": [
            "how to style", "what to wear with", "will it suit", "suits me",
            "goes with", "pair it with", "for wedding", "for office", "occasion",
            "look good on me", "my skin tone", "my body type",
        ],
    },
    "social_validation": {
        "label": "Social Validation Dependency",
        "kpi_node": "C - Decision progression",
        "addressable": True,
        "description": "User needs friends'/family's opinion before buying: sends "
                       "screenshots, shares links, asks 'should I buy this?'",
        "keywords": [
            "asked my friend", "ask my friends", "showed my", "screenshot",
            "should i buy", "should i get", "opinions?", "what do you think",
            "sent it to", "my sister said", "my mom said",
        ],
    },
    "reengagement_gap": {
        "label": "Forgetting / Re-engagement Gap",
        "kpi_node": "B - Return & re-engagement",
        "addressable": True,
        "description": "User forgets saved items; wishlist is out of sight; only "
                       "remembers via (or complains about) notifications.",
        "keywords": [
            "forgot about", "forgot i had", "reminder", "notification", "spam",
            "too many notifications", "remind me",
        ],
    },
    "app_ux_friction": {
        "label": "App / UX Friction (control theme)",
        "kpi_node": "B - Return & re-engagement",
        "addressable": True,
        "description": "General app problems: crashes, slowness, bad search or "
                       "filters, login issues. Control category to separate app "
                       "complaints from decision-journey friction.",
        "keywords": [
            "app crash", "crashes", "hangs", "slow app", "search is bad",
            "filter", "login issue", "otp", "app not working", "bugs", "lag",
        ],
    },
    "payment_checkout_friction": {
        "label": "Payment / Checkout Friction",
        "kpi_node": "D - Transaction completion",
        "addressable": False,
        "description": "Payment failures, COD unavailability, checkout errors.",
        "keywords": [
            "payment failed", "payment issue", "cod not available",
            "cash on delivery", "checkout", "money deducted", "transaction failed",
        ],
    },
}

# Themes that sit on the wishlist->purchase decision journey (vs general app ops)
DECISION_JOURNEY_THEMES = [
    "size_fit_uncertainty", "quality_doubt", "image_reality_gap",
    "price_value_anxiety", "review_trust", "comparison_paralysis",
    "wishlist_bookmark_behavior", "stock_size_unavailability",
    "styling_occasion_doubt", "social_validation", "reengagement_gap",
]
