import random
from realms.realmdef import Realm, RealmFactory
from evennia import DefaultScript, create_object, search_script

class RealmSpawner(DefaultScript):
    """
    A script that randomly spawns creatures from a pool determined by the Realm, 
    with a small chance for a rare named mob.

    This script is designed to be attached to a room and will periodically spawn 
    creatures based on the realm's configuration.

    Attributes:
        key (str): The unique identifier for this script.
        interval (int): The time interval in seconds before running at_repeat (default: 60).
        db.tick (int): A counter used to track the number of ticks since the last possible spawn.
        persistent (bool): Whether this script should persist across server restarts.
        db.spawn_location (Room): The room where creatures will be spawned.

    Methods:
        at_script_creation: Called once at script creation to initialize the script.
        at_repeat: Called at regular intervals to spawn creatures.
        do_spawn: Spawns a random creature in the room if the provided roll is less than the realm's spawn chance.
    """
    desc = "A script that randomly spawns creatures from a pool determined by the Realm, with a small chance for a rare named mob."

    def at_script_creation(self):
        """
        Called once at script creation. Sets up the script's repeating interval
        and the creature pool/rare mob spawn chance. Also sets the spawn location
        to the room that the script is placed in.
        """
        self.key = "realm_spawner"
        self.interval = 60  # Runs every 60 seconds
        self.db.tick = 0
        self.persistent = True
        self.db.spawn_location = self.obj  # Room where the script is placed

        print("Running RealmSpawner creation...")

        self.start()
        
        # Debugging: Log that the script started
        self.db.spawn_location.msg_contents("RandomSpawner script initialized and running.")

    def do_spawn(self, my_realm, roll):
        """
        Spawns a random creature, with a chance for a rare mob, but only if the room has no non-player creatures.

        Args:
            my_realm (Realm): The realm that the creature is spawned in.
            roll (float): The roll from 0 to 1 that determines if a creature is spawned at all.

        Returns:
            None

        """
        if roll <= my_realm.spawn_chance:
            creatures = list(my_realm.get_rare_mobs().keys()) + list(my_realm.get_creature_pool())
            weights = [my_realm.get_rare_mobs().get(mob, 1) for mob in creatures]

            spawn_choice = random.choices(creatures, weights=weights, k=1)[0]

            mob = create_object(
                "typeclasses.creatures.basecreature.Mob",
                key=spawn_choice,
                location=self.db.spawn_location
            )
            mob.tags.add("mob", category="creature")
            print(f"A {spawn_choice} emerges!")
            self.db.spawn_location.msg_contents(f"A {spawn_choice} emerges!")
        else:
            if my_realm.no_spawn_message:
                self.db.spawn_location.msg_contents(my_realm.no_spawn_message)

    def at_repeat(self):
        # print("Running RealmSpawner at_repeat...")

        """Spawns creatures based on the configured realm."""
        if any(obj for obj in self.db.spawn_location.contents if obj.is_typeclass("typeclasses.creatures.basecreature.Mob") and not obj.has_account):
            print("Mobs found in the room. Skipping spawn.")
            return  # Don't spawn if a non-player mob is present

        roll = random.random()

        # Debugging: Log the roll
        # print(f"Roll: {roll}")
        # self.db.spawn_location.msg_contents(f"Roll: {roll}")

        realm_key = getattr(self.db.spawn_location.db, "realm", "No Realm Set")
        my_realm = RealmFactory.get_realm(realm_key)

        if not my_realm:
            print(f"No realm found for this room using key {realm_key}. Skipping spawn.")
            return

        self.db.tick += 1
        if not self.db.tick % my_realm.spawn_interval == 0:
            # No chance of spawn this tick
            return

        self.tick = 0   # For long running server instances, guard against overflow
        self.do_spawn(my_realm, roll)