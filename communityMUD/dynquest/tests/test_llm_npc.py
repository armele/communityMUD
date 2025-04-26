from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from unittest.mock import patch
from typeclasses.characters import Character
from dynquest.models import QuestEntry
import dynquest.genpc 
import time
from evennia.accounts.models import AccountDB
from dynquest.helpers import QuestEval

class TestPlayer(Character):
    def at_object_creation(self):
        self.last_heard = ""
        self.heard_from = ""

    def msg(self, text, from_obj=None, **kwargs):
        "Custom msg() method reacting to say."

        if from_obj != self:
            # make sure to not repeat what we ourselves said or we'll create a loop
            try:
                # if text comes from a say, `text` is `('say_text', {'type': 'say'})`
                say_text, is_say = text[0], text[1]['type'] == 'say'
            except Exception:
                is_say = False
            if is_say:
                self.at_heard_say(say_text, from_obj, **kwargs)

    def at_heard_say(self, message, msg_obj=None, **kwargs):
        print(f"TestPlayer heard: {message} from {msg_obj}")
        self.last_heard = message
        self.heard_from = msg_obj

class TestGenPC(EvenniaTest):
    def setUp(self):
        """
        Set up test environment.
        """
        print(f"Running test: {self._testMethodName}")        
        super().setUp()
        self.room = create.create_object("evennia.objects.objects.DefaultRoom", key=self._testMethodName, nohome=True)
        self.npc = create.create_object(
            dynquest.genpc.GenPC, key="Storyteller", location=self.room
        )
        self.player = create.create_object(TestPlayer, key="Player", location=self.room)
        self.player.account  = AccountDB.objects.create(username="testaccount")
        self.player.save()

    def test_npc_response(self):
        """Ensure the NPC was created correctly."""
        self.assertEqual(self.npc.location, self.room)
        self.assertEqual(self.npc.key, "Storyteller")
        # self.assertTrue(hasattr(self.npc, "generate_response"))
        """Ensure the Player was created correctly."""
        self.assertEqual(self.player.location, self.room)
        self.assertEqual(self.player.key, "Player")

        """Test that the NPC attempts to generate a response."""
        print(f"About to call npc.at_heard_say() with a source of {self.player}")
        self.npc.at_heard_say("Tell me a story about a ghost train.", from_obj=self.player)

        for i in range(10): 
            if not self.player.last_heard:
                time.sleep(4)  # Pause to allow the player to hear the response.

        goodstory = False
        if any(item in self.player.last_heard.lower() for item in ["train", "ghost", "story", "station", "railway"]):
            goodstory = True

        # Ensure the NPC responds
        self.assertTrue(goodstory, "NPC did not respond to the player's message with a good story...")

    def test_quest_persistence(self):
        """
        Test that a quest was persisted in the database after a "questworthy" response
        """
        quests = QuestEntry.objects.all()
        self.assertEqual(len(quests), 0)

        self.npc.db.quest_giver = True
        dq = QuestEval("You must investigate the Terrible Blight and bring back a cure.")
        quest = self.npc.was_quest(dq)

        self.assertIsNotNone(quest)
        dq.persist_generated_quest(quest, player=self.player.account)

        quests = QuestEntry.objects.all()
        print(f"Quests: {quests}")
        
        self.assertEqual(len(quests), 1)

    def tearDown(self):
        super().tearDown()
        if self.player.account:
            self.player.account.delete()