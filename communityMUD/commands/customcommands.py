from evennia import Command, CmdSet
from evennia.objects.objects import DefaultObject

class CmdHello(Command):
    """
    Usage:
      hello [obj]

    Politely greet the specified target.
    """
        
    key = "hello"
    help_category = "Testing"

    def func(self):
        caller: DefaultObject = self.caller  # Type hint

        if self.args:
            obj = self.caller.search(self.args.strip())
        else:
            obj = self.obj
        if not obj:
            return
                
        caller.msg(f"You say: Hello, {obj.key}!")
        print("CmdHello was called!")  # This should appear in the Evennia console

class CmdRead(Command):
    """
    Usage:
      read [obj]

    Read some text of a readable object.
    """

    key = "read"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        """
        Implements the read command. This simply looks for an
        Attribute "readable_text" on the object and displays that.
        """

        if self.args:
            obj = self.caller.search(self.args.strip())
        else:
            obj = self.obj
        if not obj:
            return
        # we want an attribute read_text to be defined.
        readtext = obj.db.readable_text
        if readtext:
            string = "You read |C%s|n:\n  %s" % (obj.key, readtext)
        else:
            string = "There is nothing to read on %s." % obj.key
        self.caller.msg(string)

class CmdSetReadable(CmdSet):
    """
    A CmdSet for readables.
    """

    def at_cmdset_creation(self):
        """
        Called when the cmdset is created.
        """
        self.add(CmdRead())

class CmdClimb(Command):
    """
    Climb an object

    Usage:
      climb <object>

    This allows you to climb.
    """

    key = "climb"
    aliases = ["ascend", "scale"]
    locks = "cmd:all()"
    help_category = "Movement"

    def func(self):
        """Implements function"""

        if not self.args:
            self.caller.msg("What do you want to climb?")
            return
        obj = self.caller.search(self.args.strip())
        if not obj:
            return
        if obj != self.obj:
            self.caller.msg("Try as you might, you cannot climb that.")
            return
        ostring = self.obj.db.climb_text
        if not ostring:
            ostring = "You climb %s. Having looked around, you climb down again." % self.obj.name
        self.caller.msg(ostring)
        # set a tag on the caller to remember that we climbed.
        self.caller.tags.add("tutorial_climbed_tree", category="tutorial_world")


class CmdSetClimbable(CmdSet):
    """Climbing cmdset"""

    def at_cmdset_creation(self):
        """populate set"""
        self.add(CmdClimb())

class CmdMobOnOff(Command):
    """
    Activates/deactivates Mob

    Usage:
        mobon <mob>
        moboff <mob>

    This turns the mob from active (alive) mode
    to inactive (dead) mode. It is used during
    building to  activate the mob once it's
    prepared.
    """

    key = "mobon"
    aliases = "moboff"
    locks = "cmd:superuser()"

    def func(self):
        """
        Uses the mob's set_alive/set_dead methods
        to turn on/off the mob."
        """
        if not self.args:
            self.caller.msg("Usage: mobon||moboff <mob>")
            return
        mob = self.caller.search(self.args)
        if not mob:
            return
        elif not isinstance(mob, typeclasses.creatures.basecreature.Mob): # type: ignore
            self.caller.msg(f"You can't {self.cmdstring} a {mob.key}.")
            return

        if self.cmdstring == "mobon":
            mob.set_alive()
        else:
            mob.set_dead()


class MobCmdSet(CmdSet):
    """
    Holds the admin command controlling the mob
    """

    def at_cmdset_creation(self):
        self.add(CmdMobOnOff())
