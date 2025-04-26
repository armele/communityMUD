import re
import uuid
from dynquest.models import QuestEntry

class QuestEval():
    def __init__(self, text: str):
        """
        Constructor. Initializes a QuestEval with the given text.

        Args:
            text: The text to be evaluated for quest-like content.
        """
        self.text = text

    def is_quest_worthy(self) -> bool:
        """
        Lightweight keyword-based test to detect quest-like content.
        """
        keywords = [
            "quest", "mission", "task", "assignment",
            "retrieve", "deliver", "investigate", "slay", "find",
            "explore", "track", "hunt", "recover", "return",
            "search", "follow", "protect", "solve", "convince", "negotiate",
            "objective", "reclaim", "uncover", "discover"
        ]
        text_lower = self.text.lower()
        return any(keyword in text_lower for keyword in keywords)

    def quest_confidence_score(self) -> int:
        """
        Scores common quest phrases to add confidence.
        """
        patterns = [
            r"\byour mission is to\b",
            r"\byou must\b",
            r"\bbring back\b",
            r"\btalk to\b",
            r"\binvestigate\b",
            r"\breturn with\b",
            r"\bsearch for\b",
            r"\bgo to\b",
            r"\bdefeat\b",
            r"\bfind\b",
            r"\bslay\b",
            r"\bsolve\b",
            r"\bprotect\b",
            r"\btrack\b",
            r"\bdeliver\b",
            r"\brecover\b",
            r"\breturn\b",
            r"\bexplore\b",
            r"\bfollow\b",
            r"\bhunt\b",        
            r"\bconvince\b",
            r"\buncover\b",
            r"\bdiscover\b"

        ]
        return sum(bool(re.search(pattern, self.text, re.IGNORECASE)) for pattern in patterns)

    def persist_generated_quest(self, data, player=None):
        quest_id = f"quest_{uuid.uuid4().hex[:8]}"
        quest_title = data["title"]

        entry = QuestEntry.objects.create(
            quest_id=quest_id,
            title=quest_title,
            status="pending",
            triggered_by=player,
            raw_data=data
        )
        return entry

    def __str__(self) -> str:
        # A custom string representation for the QuestEval class
        return (f"QuestEval(worthy={self.is_quest_worthy()}, confidence={self.quest_confidence_score()}, text='{self.text}')")
