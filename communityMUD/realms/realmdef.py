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
        # Default data; these should be customized when creating the realm
        self.realm_name = "Default Realm"
        self.creature_pool = []
        self.rare_mobs = {}

    def set_creatures(self, creature_pool, rare_mobs):
        """Set the creatures for this realm."""
        self.creature_pool = creature_pool
        self.rare_mobs = rare_mobs

    def get_realm_name(self):
        return self.realm_name

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

class BraveRiverValleyRealm(Realm):
    def __init__(self):
        super().__init__()
        self.realm_name = "Brave River Valley"
        self.creature_pool = ["wolf", "lion", "bear", "boar", "snake", "fox"]
        self.rare_mobs = {"dire wolf": 0.05, "golden lion": 0.02}
