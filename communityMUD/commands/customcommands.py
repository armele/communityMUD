from evennia import Command, CmdSet, default_cmds, search_object, utils
from django.conf import settings
from evennia.objects.objects import DefaultObject

_SEARCH_AT_RESULT = utils.object_from_module(settings.SEARCH_AT_RESULT)


# Pulled from Tutorial as a starting point.
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

# Pulled from Tutorial as a starting point.
class CmdSetReadable(CmdSet):
    """
    A CmdSet for readables.
    """

    def at_cmdset_creation(self):
        """
        Called when the cmdset is created.
        """
        self.add(CmdRead())

# Pulled from Tutorial as a starting point.
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

# Pulled from Tutorial as a starting point.
class CmdSetClimbable(CmdSet):
    """Climbing cmdset"""

    def at_cmdset_creation(self):
        """populate set"""
        self.add(CmdClimb())

# Pulled from Tutorial as a starting point.
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

# Pulled from Tutorial as a starting point.
class MobCmdSet(CmdSet):
    """
    Holds the admin command controlling the mob
    """

    def at_cmdset_creation(self):
        self.add(CmdMobOnOff())

# Pulled from the Tutorial as a starting point
class CmdLook(default_cmds.CmdLook):
    """
    looks at the room and on details

    Usage:
        look <obj>
        look <room detail>
        look *<account>

    Observes your location, details at your location or objects
    in your vicinity.

    This is a child of the default Look command, that also
    allows us to look at "details" in the room.  These details are
    things to examine and offers some extra description without
    actually having to be actual database objects. It uses the
    return_detail() hook on DetailRooms for this.
    """

    # we don't need to specify key/locks etc, this is already
    # set by the parent.
    help_category = "General"

    def func(self):
        """
        Handle the looking. This is a copy of the default look
        code except for adding in the details.
        """
        caller = self.caller
        args = self.args
        if args:
            # we use quiet=True to turn off automatic error reporting.
            # This tells search that we want to handle error messages
            # ourself. This also means the search function will always
            # return a list (with 0, 1 or more elements) rather than
            # result/None.
            looking_at_obj = caller.search(
                args,
                # note: excludes room/room aliases
                candidates=caller.location.contents + caller.contents,
                use_nicks=True,
                quiet=True,
            )
            if len(looking_at_obj) != 1:
                # no target found or more than one target found (multimatch)
                # look for a detail that may match
                detail = self.obj.return_detail(args)
                if detail:
                    self.caller.msg(detail)
                    return
                else:
                    # no detail found, delegate our result to the normal
                    # error message handler.
                    _SEARCH_AT_RESULT(looking_at_obj, caller, args)
                    return
            else:
                # we found a match, extract it from the list and carry on
                # normally with the look handling.
                looking_at_obj = looking_at_obj[0]

        else:
            looking_at_obj = caller.location
            if not looking_at_obj:
                caller.msg("You have no location to look at!")
                return

        if not hasattr(looking_at_obj, "return_appearance"):
            # this is likely due to us having an account instead
            looking_at_obj = looking_at_obj.character
        if not looking_at_obj.access(caller, "view"):
            caller.msg("Could not find '%s'." % args)
            return
        # get object's appearance
        caller.msg(looking_at_obj.return_appearance(caller))
        # the object's at_desc() method.
        looking_at_obj.at_desc(looker=caller)
        return
    
# for the @detail command we inherit from MuxCommand, since
# we want to make use of MuxCommand's pre-parsing of '=' in the
# argument.
# Pulled from the Tutorial as a starting point
class CmdSetDetail(default_cmds.MuxCommand):
    """
    sets a detail on a room

    Usage:
        @detail <key> = <description>
        @detail <key>;<alias>;... = description

    Example:
        @detail walls = The walls are covered in ...
        @detail castle;ruin;tower = The distant ruin ...

    This sets a "detail" on the object this command is defined on
    This detail can be accessed with the CmdLook command sitting on 
    DetailRoom objects (details are set as a simple dictionary on 
    the room). This is a Builder command.

    We custom parse the key for the ;-separator in order to create
    multiple aliases to the detail all at once.
    """

    key = "@detail"
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        """
        All this does is to check if the object has
        the set_detail method and uses it.
        """
        if not self.args or not self.rhs:
            self.caller.msg("Usage: @detail key = description")
            return
        if not hasattr(self.obj, "set_detail"):
            self.caller.msg("Details cannot be set on %s." % self.obj)
            return
        for key in self.lhs.split(";"):
            # loop over all aliases, if any (if not, this will just be
            # the one key to loop over)
            self.obj.set_detail(key, self.rhs)
        self.caller.msg("Detail set: '%s': '%s'" % (self.lhs, self.rhs))

class DetailRoomCmdSet(CmdSet):
    """
    Implements the simple tutorial cmdset. This will overload the look
    command in the default CharacterCmdSet since it has a higher
    priority (ChracterCmdSet has prio 0)
    """

    key = "tutorial_cmdset"
    priority = 1

    def at_cmdset_creation(self):
        """add the tutorial-room commands"""
        self.add(CmdLook())
        self.add(CmdSetDetail())