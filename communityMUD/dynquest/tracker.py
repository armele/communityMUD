from dynquest.models import QuestProgress, QuestEntry
from django.utils import timezone

class QuestTracker:
    def __init__(self, character):
        self.character = character

    def all(self):
        return QuestProgress.objects.filter(character=self.character)

    def active(self):
        return self.all().filter(status="in_progress")

    def completed(self):
        return self.all().filter(status="complete")

    def get(self, quest_id):
        return self.all().filter(quest__quest_id=quest_id).first()

    def begin(self, quest_entry, start_step=None):
        existing = self.get(quest_entry.quest_id)
        if existing:
            return existing
        return QuestProgress.objects.create(
            quest=quest_entry,
            character=self.character,
            current_step=start_step or "",
            status="in_progress"
        )

    def complete(self, quest_id) -> QuestEntry:
        quest: QuestEntry =  self.get(quest_id) # type: ignore
        if quest and quest.status != "complete":
            quest.status = "complete"
            quest.completed = timezone.now()
            quest.save()
        return quest

    def abandon(self, quest_id) -> QuestEntry:
        quest: QuestEntry = self.get(quest_id) # type: ignore
        if quest and quest.status == "in_progress":
            quest.status = "abandoned"
            quest.save()
        return quest
