"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia.objects.objects import DefaultRoom
from commands.customcommands import DetailRoomCmdSet
from .objects import ObjectParent


class Room(ObjectParent, DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects.
    """

    pass

class DetailRoom(DefaultRoom):
    """
    This is the base room type for all rooms in the tutorial world.
    It defines a cmdset on itself for reading tutorial info about the location.
    """

    def at_object_creation(self):
        """Called when room is first created"""
        self.db.tutorial_info = (
            "This is a tutorial room. It allows you to use the 'tutorial' command."
        )
        self.cmdset.add_default(DetailRoomCmdSet)

    def at_object_receive(self, new_arrival, source_location, move_type="move", **kwargs):
        """
        When an object enter a tutorial room we tell other objects in
        the room about it by trying to call a hook on them. The Mob object
        uses this to cheaply get notified of enemies without having
        to constantly scan for them.

        Args:
            new_arrival (Object): the object that just entered this room.
            source_location (Object): the previous location of new_arrival.

        """
        if new_arrival.ndb.batch_batchmode:
            # currently running batchcommand
            return

        if new_arrival.has_account and not new_arrival.ndb.batch_batchmode:
            # this is a character
            for obj in self.contents_get(exclude=new_arrival):
                if hasattr(obj, "at_new_arrival"):
                    obj.at_new_arrival(new_arrival)

    def return_detail(self, detailkey):
        """
        This looks for an Attribute "obj_details" and possibly
        returns the value of it.

        Args:
            detailkey (str): The detail being looked at. This is
                case-insensitive.

        """
        details = self.db.details
        if details:
            return details.get(detailkey.lower(), None)

    def set_detail(self, detailkey, description):
        """
        This sets a new detail, using an Attribute "details".

        Args:
            detailkey (str): The detail identifier to add (for
                aliases you need to add multiple keys to the
                same description). Case-insensitive.
            description (str): The text to return when looking
                at the given detailkey.

        """
        if self.db.details:
            self.db.details[detailkey.lower()] = description
        else:
            self.db.details = {detailkey.lower(): description}