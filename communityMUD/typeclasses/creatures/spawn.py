import random
from realms.realmdef import Realm, RealmFactory
from evennia import DefaultScript, create_object, search_script

class RealmSpawner(DefaultScript):
    desc = "A script that randomly spawns creatures from a pool determined by the Realm, with a small chance for a rare named mob."
    """
    A script that randomly spawns creatures from a pool, with a small chance for a rare named mob.
    """

    def at_script_creation(self):
        """Runs when the script is created and assigns its room's realm data."""
        self.key = "realm_spawner"
        self.interval = 60  # Runs every 60 seconds
        self.persistent = True
        self.db.spawn_location = self.obj  # Room where the script is placed

        print(f"Running RealmSpawner creation...")

        self.start()
        
        # Debugging: Log that the script started
        self.db.spawn_location.msg_contents("RandomSpawner script initialized and running.")

    def at_repeat(self):
        print(f"Running RealmSpawner at_repeat...")

        """Spawns creatures based on the configured realm."""
        if any(obj for obj in self.db.spawn_location.contents if obj.is_typeclass("typeclasses.creatures.basecreature.Mob") and not obj.has_account):
            print(f"Mobs found in the room. Skipping spawn.")
            self.db.spawn_location.msg_contents("Soft noises fade into the distance...")
            return  # Don't spawn if a non-player mob is present

        roll = random.random()

        print(f"Roll: {roll}")
        self.db.spawn_location.msg_contents(f"Roll: {roll}")

        if roll < 0.2:
            realm_key = getattr(self.db.spawn_location.db, "realm", "No Realm Set")
            my_realm = RealmFactory().get_realm(realm_key)

            if my_realm:
                creatures = list(my_realm.get_rare_mobs().keys()) + list(my_realm.get_creature_pool())
                weights = [my_realm.get_rare_mobs().get(mob, 1) for mob in creatures]

                spawn_choice = random.choices(creatures, weights=weights, k=1)[0]
                self.db.spawn_location.msg_contents(f"A {spawn_choice} emerges!")

                mob = create_object(
                    "typeclasses.creatures.basecreature.Mob",
                    key=spawn_choice,
                    location=self.db.spawn_location
                )
                mob.tags.add("mob", category="creature")
                print(f"A {spawn_choice} emerges!")
                self.db.spawn_location.msg_contents(f"A {spawn_choice} emerges!")
            else:
                print(f"No realm found for this room using key {realm_key}. Skipping spawn.")
        else:
            self.db.spawn_location.msg_contents("Soft noises echo in the distance...")

class RandomSpawner(DefaultScript):
    
    desc = "A script that randomly spawns creatures from a pool, with a small chance for a rare named mob."
    """
    A script that randomly spawns creatures from a pool, with a small chance for a rare named mob.
    """
    def at_script_creation(self):
        """
        Called once at script creation. Sets up the script's repeating interval
        and the creature pool/rare mob spawn chance. Also sets the spawn location
        to the room that the script is placed in.
        """
        self.interval = 60  # Check every 60 seconds
        self.persistent = True
        self.db.creature_pool = ["wolf", "lion", "bear", "boar", "snake", "fox"]
        self.db.rare_mobs = {"dire_wolf": 0.05, "golden_lion": 0.02}  # Rare mob spawn chance
        self.db.spawn_location = self.obj  # Defaults to where the script is placed
        self.start()

    def at_repeat(self):
        """Spawns a random creature, with a chance for a rare mob, but only if the room has no non-player creatures."""
        if any(obj for obj in self.db.spawn_location.contents if obj.is_typeclass("typeclasses.creatures.basecreature.Mob") and not obj.has_account):
            self.db.spawn_location.msg_contents(f"Soft noises fade into the distance...")
            return  # Skip spawning if there's already a non-player creature in the room

        roll = random.random()
        self.db.spawn_location.msg_contents(f"Spawn roll: {roll}")
        if roll < 0.2:
            creatures = list(self.db.rare_mobs.keys()) + list(self.db.creature_pool)
            weights = [self.db.rare_mobs.get(mob, 1) for mob in creatures]
            self.db.spawn_location.msg_contents(f"Creatures: {creatures}")
            self.db.spawn_location.msg_contents(f"Weights: {weights}")

            spawn_choice = random.choices(creatures, weights=weights, k=1)[0]
            self.db.spawn_location.msg_contents(f"A {spawn_choice} emerges!")

            mob = create_object(
                "typeclasses.creatures.basecreature.Mob",  # Adjust this to your actual creature class path
                key=spawn_choice,
                location=self.db.spawn_location
            )
            mob.tags.add("mob", category="creature")  # Tag for easy identification
        else:
            self.db.spawn_location.msg_contents(f"Soft noises echo in the distance...")