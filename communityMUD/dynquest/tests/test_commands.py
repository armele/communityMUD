from evennia.utils.create import create_object
from evennia.accounts.models import AccountDB
from evennia.commands.cmdhandler import cmdhandler
from evennia.utils.test_resources import EvenniaTestCase
from dynquest.models import QuestEntry
from datetime import datetime, timedelta
from dynquest.commands import CmdQuestStatus

class TestCmdQuestStatus(EvenniaTestCase):

    def setUp(self):
        super().setUp()
        print(f"Running test: {self._testMethodName}")

        # Create builder account
        self.account = AccountDB.objects.create(username="builder")
        self.account.permissions.add("Builder")
        self.char = create_object("typeclasses.characters.Character", key="TestBuilder")
        self.char.account = self.account
        self.char.save()
        self.account.db._last_puppet = self.char  # 👈 important
        self.account.save()

        # Create a few quest entries
        QuestEntry.objects.create(
            quest_id="test_q1",
            title="The Blight",
            status="built",
            triggered_by=self.account,
            last_updated=datetime.now() - timedelta(hours=1),
            raw_data={"quest": {}}
        )
        QuestEntry.objects.create(
            quest_id="test_q2",
            title="Shrine Collapse",
            status="error",
            triggered_by=self.account,
            last_updated=datetime.now(),
            raw_data={"quest": {}}
        )
        QuestEntry.objects.create(
            quest_id="test_q3",
            title="Unseen Menace",
            status="pending",
            triggered_by=self.account,
            last_updated=datetime.now(),
            raw_data={"quest": {}}
        )


    def test_cmd_queststatus_shows_recent(self):
        # Setup the command manually
        cmd = CmdQuestStatus()
        cmd.caller = self.char
        cmd.account = self.account
        cmd.args = ""
        cmd.cmdstring = "@queststatus"
        cmd.raw_string = "@queststatus"
        cmd.session = None

        # Intercept the message output
        responses = []
        def mock_msg(text=None, **kwargs):
            if text:
                responses.append(str(text))

        cmd.msg = mock_msg

        # Run the command
        cmd.func()

        # Join all output messages
        output = "\n".join(responses)

        # Assertions
        self.assertIn("The Blight", output)
        self.assertIn("Shrine Collapse", output)
        self.assertNotIn("Unseen Menace", output)
        self.assertIn("test_q1", output)
        self.assertIn("built", output)
        self.assertIn("error", output)

