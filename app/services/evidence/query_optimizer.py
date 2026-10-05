import re
from typing import List
from app.models.claims import Claim

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "which", "this", "that", "these", "those", "then", "just", "so", "than",
    "such", "both", "through", "about", "for", "is", "of", "while", "during",
    "to", "from", "in", "out", "on", "off", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "any", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "can", "will",
    "just", "don", "should", "now", "did", "does", "do", "official", "authorities",
    "announce", "announcement", "public", "record", "confirming", "whether"
}

class SearchQueryOptimizer:
    """
    Transforms long natural language claims and verification questions
    into clean, high-precision search engine queries.
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """Removes smart quotes, punctuation artifacts, and extra whitespace."""
        cleaned = text.replace("“", " ").replace("”", " ").replace('"', " ").replace("'", " ")
        cleaned = cleaned.replace("‘", " ").replace("’", " ").replace("—", " ").replace("-", " ")
        cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
        return " ".join(cleaned.split())

    @staticmethod
    def generate_queries(claim: Claim) -> List[str]:
        """
        Produces targeted, distinct search queries ordered from specific to broad.
        """
        raw_text = SearchQueryOptimizer.clean_text(claim.claim_text)
        words = raw_text.split()
        
        # 1. Entity-based queries if entities were extracted
        entity_names = [e.name for e in claim.entities]
        
        # Extract capitalized multi-word phrases as likely named entities (e.g. Donald Trump, Ruby Bradley, Department of Defense)
        capitalized_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', claim.claim_text)
        # Filter out sentence starters that are not proper nouns
        proper_names = [p for p in capitalized_phrases if p.lower() not in {"did", "official", "is", "there", "the"}]

        key_subjects = list(dict.fromkeys(entity_names + proper_names))

        queries = []

        # Query 1: Key subjects + fact check
        if len(key_subjects) >= 2:
            queries.append(f"{' '.join(key_subjects[:3])} fact check")
            queries.append(f"{' '.join(key_subjects[:2])}")
        elif len(key_subjects) == 1:
            queries.append(f"{key_subjects[0]} fact check")

        # Query 2: Salient substantive keywords (excluding stop words)
        substantive = [w for w in words if w.lower() not in STOP_WORDS and len(w) > 2]
        if substantive:
            concise_claim = " ".join(substantive[:6])
            queries.append(f"{concise_claim} fact check")
            queries.append(concise_claim)

        # Fallback to cleaned claim if no queries generated
        if not queries:
            queries.append(raw_text[:80])

        # Deduplicate preserving order
        unique_queries = []
        for q in queries:
            q_clean = " ".join(q.split())
            if q_clean and q_clean not in unique_queries:
                unique_queries.append(q_clean)

        return unique_queries[:3]
