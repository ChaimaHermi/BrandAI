import re
from html import unescape


def clean_text(text: str) -> str:
    if not text:
        return ""

    # ─────────────────────────
    # 1. Decode HTML entities
    # ─────────────────────────
    text = unescape(text)

    # ─────────────────────────
    # 2. Normalize unicode
    # ─────────────────────────
    replacements = {
        "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-",
        "\u00A0": " ", "\u200B": "", "\u200C": "", "\u200D": "",
        "\u2026": "...",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    # ─────────────────────────
    # 3. Remove HTML tags
    # ─────────────────────────
    text = re.sub(r"<[^>]+>", " ", text)

    # ─────────────────────────
    # 4. Remove markdown / scraping artifacts
    # ─────────────────────────
    text = re.sub(r"#+\s*\d*\)?", " ", text)        # ### 1)
    text = re.sub(r"\[.*?\]", " ", text)            # [text]
    text = re.sub(r"\(.*?\)", " ", text)            # (text)
    text = re.sub(r"\|\s*", " ", text)              # tables |
    text = re.sub(r"-{2,}", " ", text)              # ----
    
    # ─────────────────────────
    # 5. Remove URLs
    # ─────────────────────────
    text = re.sub(r"http\S+|www\S+", " ", text)

    # ─────────────────────────
    # 6. Remove boilerplate words (common web noise)
    # ─────────────────────────
    noise_patterns = [
        r"cookie(s)? policy",
        r"privacy policy",
        r"terms of service",
        r"accept all cookies",
        r"subscribe now",
        r"sign up",
        r"login",
        r"all rights reserved",
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    # ─────────────────────────
    # 7. Remove repeated punctuation
    # ─────────────────────────
    text = re.sub(r"[!?.]{2,}", ".", text)

    # ─────────────────────────
    # 8. Remove multiple spaces
    # ─────────────────────────
    text = re.sub(r"\s+", " ", text)

    # ─────────────────────────
    # 9. Trim
    # ─────────────────────────
    text = text.strip()

    return text