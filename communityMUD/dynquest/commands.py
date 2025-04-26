from evennia import default_cmds
from evennia.utils.utils import inherits_from
from dynquest.models import QuestEntry

class CmdQuestStatus(default_cmds.MuxCommand):
    """
    View recent dynamic quest builds.

    Usage:
      @queststatus [limit]

    Shows recent built or errored quests, defaulting to 10. Use optional limit to change.
    """

    key = "@queststatus"
    locks = "cmd:perm(Builders)"
    help_category = "Building"

    def func(self):
        print(f"queststatus called by {self.caller}")

        limit = 10
        if self.args:
            try:
                limit = int(self.args.strip())
            except ValueError:
                self.msg("Usage: @queststatus [limit]")
                return

        quests = QuestEntry.objects.filter(status__in=["built", "error"]).order_by("-last_updated")[:limit]

        if not quests:
            self.msg("No recent completed or failed quests.")
            return

        lines = ["|wRecent Quests|n:"]
        for quest in quests:
            triggered = quest.triggered_by.username if quest.triggered_by else "Unknown"
            lines.append(f"{quest.quest_id:<12} |c{quest.title}|n ({quest.status}) by {triggered} on {quest.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")

        self.msg("\n".join(lines))
