"""Deterministic Vietnamese normalization and ranking for Evidence browse/search."""

import re
import unicodedata


SYNONYMS = {
    "diem ren luyen": ("ren luyen", "danh gia ren luyen", "ket qua ren luyen"),
    "tot nghiep": ("xet tot nghiep", "do an tot nghiep"),
}


def normalize_vietnamese(text: str) -> str:
    """Normalize Vietnamese text for exact, deterministic lexical matching."""
    folded = (text or "").casefold().replace("đ", "d")
    unaccented = "".join(
        character
        for character in unicodedata.normalize("NFKD", folded)
        if not unicodedata.combining(character)
    )
    return " ".join(re.sub(r"[^a-z0-9]+", " ", unaccented).split())


def rank_notices(notices: list[dict], searchterm: str, limit: int = 10) -> list[dict]:
    query = normalize_vietnamese(searchterm)
    if not query:
        return []

    query_tokens = set(query.split())
    synonym_phrases = SYNONYMS.get(query, ())
    ranked = []

    for notice in notices:
        title = normalize_vietnamese(notice.get("title", ""))
        category = normalize_vietnamese(notice.get("category", ""))
        text = normalize_vietnamese(notice.get("searchable_text", ""))
        title_tokens = set(title.split())
        text_tokens = set(text.split())
        score = 0
        reasons = []

        if query in title:
            score += 100
            reasons.append("Tiêu đề chứa cụm từ chính xác")
        elif any(phrase in title for phrase in synonym_phrases):
            score += 80
            reasons.append("Tiêu đề chứa cụm từ liên quan")

        if query_tokens and query_tokens.issubset(title_tokens):
            score += 50
            reasons.append("Tiêu đề chứa tất cả từ khóa")

        category_matches = len(query_tokens.intersection(category.split()))
        if category_matches:
            score += category_matches * 15
            reasons.append("Khớp chuyên mục")

        title_matches = len(query_tokens.intersection(title_tokens))
        if title_matches:
            score += title_matches * 20
            if not any(reason.startswith("Tiêu đề") for reason in reasons):
                reasons.append("Tiêu đề chứa một phần từ khóa")

        if query in text or any(phrase in text for phrase in synonym_phrases):
            score += 30
            reasons.append("Nội dung chứa cụm từ liên quan")
        else:
            text_matches = len(query_tokens.intersection(text_tokens))
            if text_matches:
                score += text_matches * 5
                reasons.append("Nội dung chứa từ khóa")

        if score >= 40:
            result = notice.copy()
            result["search_score"] = score
            result["match_reasons"] = list(dict.fromkeys(reasons))
            ranked.append(result)

    # Stable tie-breakers are independent of database row order.
    ranked.sort(key=lambda item: (
        -item["search_score"],
        normalize_vietnamese(item.get("title", "")),
        item["notice_id"],
    ))
    return ranked[:limit]
