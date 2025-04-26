from evennia.utils.create import create_object
from evennia.utils.test_resources import EvenniaTestCase
from dynquest.models import QuestEntry, QuestProgress
from dynquest.tracker import QuestTracker
from datetime import datetime

class TestQuestTracker(EvenniaTestCase):

    def setUp(self):
        super().setUp()
        self.char = create_object("typeclasses.characters.Character", key="Tester")
        self.quest = QuestEntry.objects.create(
            quest_id="quest_test_001",
            title="Test Quest",
            status="built",
            raw_data={"quest": {"title": "Test Quest"}}
        )
        self.tracker = QuestTracker(self.char)

    def test_begin_quest(self):
        qp = self.tracker.begin(self.quest)
        self.assertEqual(qp.quest, self.quest)
        self.assertEqual(qp.character, self.char)
        self.assertEqual(qp.status, "in_progress")

    def test_complete_quest(self):
        self.tracker.begin(self.quest)
        qp = self.tracker.complete("quest_test_001")
        self.assertEqual(qp.status, "complete")
        self.assertIsNotNone(qp.completed)

    def test_abandon_quest(self):
        self.tracker.begin(self.quest)
        qp = self.tracker.abandon("quest_test_001")
        self.assertEqual(qp.status, "abandoned")
