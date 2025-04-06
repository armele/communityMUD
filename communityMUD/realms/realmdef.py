from evennia import DefaultScript
from sentence_transformers import SentenceTransformer
import json

class RealmFactory():
    @classmethod
    def gatherLore(cls):
        lore = []
       
        for realm in RealmFactory.listRealms():
            print(f"Realm: {realm.realm_name}, {realm.lore}")
            for lorebit in realm.lore:
                lore.append(f"In {realm.realm_name}: {lorebit}")

        return lore
    
    @classmethod
    def embedLore(cls):
        model = SentenceTransformer("all-MiniLM-L6-v2")
        data = []

        for snippet in RealmFactory.gatherLore():
            embedding = model.encode(snippet).tolist()
            data.append({
                "content": snippet,
                "embedding": embedding
            })

        with open("severed_realms_embeddings.json", "w") as f:
            json.dump(data, f, indent=2)

        print("Embedding complete and saved to brave_river_embeddings.json")

    @classmethod
    def listRealms(cls):
        # Add more realms here
        return [TestRealm(), BraveRiverValleyRealm()]

    @classmethod
    def get_realm(cls,realm_name):
        print(f"Retrieving realm for {realm_name}")
        
        for realm in cls.listRealms():
            if realm.realm_tag == realm_name:
                return realm
            
        return None

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
        self.realm_tag = None
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
        self.realm_tag = "realm_test"
        self.realm_name = "Test Realm"
        self.creature_pool = ["sand crab", "scorpion", "jackal"]
        self.rare_mobs = {"dust devil": 0.05, "blue scarab": 0.02}
        self.spawn_interval = 1
        self.lore = [
            "The mystery of the realm is difficult to discern."          
        ]

class BraveRiverValleyRealm(Realm):
    def __init__(self):
        super().__init__()
        self.realm_tag = "realm_brv"
        self.realm_name = "Brave River Valley"
        self.creature_pool = ["wolf", "lion", "bear", "boar", "snake", "fox"]
        self.rare_mobs = {"dire wolf": 0.05, "golden lion": 0.02}
        self.lore = [
            "The Brave River Valley was once a thriving frontier, its bustling mining town fueled by ambition and iron rails. Then the Severing struck.",
            "A tunnel crew, burrowing deep beneath the mountains, unearthed something that should have remained buried—a force older than history, neither dead nor alive, but watching. In an instant, the valley was severed from the world beyond the peaks. The railway lines led nowhere. The telegraph wires hummed with static. The Eastern metropolises became nothing more than distant memories.",
            "The Railyard, a former depot, serves as the valley’s Station — a crossroads where wary humans and Wemic trade news, barter for supplies, and prepare expeditions.",
            "Some seek lost technology in the ruins of the abandoned tunnel. Others delve into the edges of the Eidenwood, hoping to glean wisdom from spirits older than men. But all who remain know one truth… Something in the dark is waking.",
            "Culture and Society: Technological innovation stagnated as townsfolk turned their attention to matters of survival and self-sufficiency. Initial suspicion of strangers quickly gave way to collaboration, as dependency on the goods that reached them through the Station increased.",
            "In the absence of some of the specialized engineering skills needed to advance and repair their steam technology some people have turned to magic - attempting to learn these abilities from visitors to their Realm.",
            "Realm Borders: The western edge of the valley where the trestle bridge crosses Crooked Creek now borders the Eidenwood. Steam engines rust beside forgotten shrines, where miners and mystics drink from the same cups, and where old ghosts whisper along abandoned tracks."            
        ]
