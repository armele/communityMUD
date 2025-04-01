from evennia import DefaultScript

class RealmFactory():
    def get_realm(self, realm_name):
        print(f"Retrieving realm for {realm_name}")
        
        switcher = {
            "realm_test": TestRealm(),
            "realm_brv": BraveRiverValleyRealm()
        }
        return switcher.get(realm_name, Realm())

class Realm(DefaultScript):
    """
    A persistent script representing a Realm. It stores creature pools,
    rare mobs, and other realm-specific configurations.
    """

    def __init__(self):
        super().__init__()
        """
        Initializes the Realm with default data. This should be customized
        when creating a realm.

        Sets the following attributes:
            realm_name: The name of the realm.
            creature_pool: A list of creature names that can be spawned
                in this realm.
            rare_mobs: A dictionary with creature names as keys and a
                decimal value from 0 to 1 as the value, representing the
                chance of that creature being spawned instead of a normal
                creature from the creature pool.
            spawn_chance: A decimal value from 0 to 1 representing the
                chance of a creature being spawned at all.
            spawn_interval: The number of minutes between possible spawns
        """
        self.realm_name = "Default Realm"
        self.creature_pool = []
        self.rare_mobs = {}
        self.spawn_chance = .20
        self.spawn_interval = 15
        self.no_spawn_message = "Soft noises fade into the distance..."

    def set_creatures(self, creature_pool, rare_mobs):
        """Set the creatures for this realm."""
        self.creature_pool = creature_pool
        self.rare_mobs = rare_mobs

    def get_creature_pool(self):
        """Retrieve the creature pool for spawning."""
        return self.creature_pool or []

    def get_rare_mobs(self):
        """Retrieve the rare mob dictionary."""
        return self.rare_mobs or {}
    
class TestRealm(Realm):
    def __init__(self):
        super().__init__()
        self.realm_name = "Test Realm"
        self.creature_pool = ["sand crab", "scorpion", "jackal"]
        self.rare_mobs = {"dust devil": 0.05, "blue scarab": 0.02}
        self.spawn_interval = 1

class BraveRiverValleyRealm(Realm):
    def __init__(self):
        super().__init__()
        self.realm_name = "Brave River Valley"
        self.creature_pool = ["wolf", "lion", "bear", "boar", "snake", "fox"]
        self.rare_mobs = {"dire wolf": 0.05, "golden lion": 0.02}
