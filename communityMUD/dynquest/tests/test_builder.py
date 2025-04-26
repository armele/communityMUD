from evennia.utils.create import create_object
from evennia.objects.models import ObjectDB
from evennia.utils.test_resources import EvenniaTestCase
from dynquest.builder import TRANSFORMER, LOCATION_SIMILARITY_THRESHOLD
from dynquest.models import QuestEntry
from dynquest.builder import QuestBuilderScript
from evennia.utils.search import search_object
from evennia.utils.test_resources import EvenniaTestCase
from evennia.scripts.models import ScriptDB
import uuid

class TestLocationFunctions(EvenniaTestCase):      
    def setUp(self):
        """
        Set up locations.
        """
        print(f"Running test: {self._testMethodName}")          
        super().setUp()
        self.transformer = TRANSFORMER 
        
        # Create a known location
        self.blackwood = create_object(
            typeclass="typeclasses.rooms.Room",
            key="Blackwood Forest",
            attributes=[
                ("desc", "A dark, misty forest filled with gnarled trees. Whispers of ghosts echo between the trunks.")
            ]
        )
        self.blackwood.db.embedding = TRANSFORMER.encode([self.blackwood.db.desc])[0].tolist()

        self.glade = create_object(
            typeclass="typeclasses.rooms.Room",
            key="Sunny Glade",
            attributes=[
                ("desc", "A peaceful meadow bathed in sunlight, with butterflies and flowers everywhere.")
            ]
        )
        self.glade.db.embedding = TRANSFORMER.encode([self.glade.db.desc])[0].tolist()

        self.cave = create_object(
            typeclass="typeclasses.rooms.Room",
            key="Collapsed Mine",
            attributes=[
                ("desc", "A ruined tunnel with unstable walls. The air smells of earth and old danger.")
            ]
        )
        self.cave.db.embedding = TRANSFORMER.encode([self.cave.db.desc])[0].tolist()

        self.quest_json = {
            "quest": {
                "title": "The Blight Awakens",
                "lore": "A sickness has spread through the forest.",
                "locations": [
                    {"key": "Blighted Grove", "desc": "A dark and twisted forest where shadows cling to the bark."}
                ],
                "objects": [],
                "npcs": [],
                "goals": [{"key": "Investigate Grove", "desc": "Find the source of the blight."}]
            }
        }

        self.quest = QuestEntry.objects.create(
            quest_id="test_001",
            title="The Blight Awakens",
            status="pending",
            raw_data=self.quest_json
        )  

    def test_similar_location_match(self):
        from dynquest.builder import get_similar_locations  # Update path if needed

        query = "A haunted forest where the air feels heavy and shadows linger beneath twisted trees."
        matches = get_similar_locations(query, transformer=TRANSFORMER, threshold=LOCATION_SIMILARITY_THRESHOLD)

        # Should return at least one match
        self.assertTrue(matches)
        
        # Should include Blackwood Forest, not Sunny Glade
        top_keys = [room.key for room, score in matches]
        self.assertIn("Blackwood Forest", top_keys)
        self.assertNotIn("Sunny Glade", top_keys)

        # Similarity should be fairly high
        top_score = matches[0][1]
        self.assertGreaterEqual(top_score, LOCATION_SIMILARITY_THRESHOLD)



    def test_builder_reuses_location(self):
        script = QuestBuilderScript()
        script.do_build(self.quest)

        # Reload the quest and assert it was marked as built
        self.quest.refresh_from_db()
        self.assertEqual(self.quest.status, "built")

        # Should NOT create new room if similarity passes
        rooms = ObjectDB.objects.filter(db_key="Blighted Grove")
        self.assertFalse(rooms.exists(), "Builder should have reused a similar room instead of creating new one.")


class TestBuildError(EvenniaTestCase):
    def setUp(self):
        print(f"Running test: {self._testMethodName}")          
        super().setUp()

    def test_quest_builder_handles_invalid_data(self):
        # Invalid: no "quest" key
        broken_quest = QuestEntry.objects.create(
            quest_id="test_broken",
            title="Broken Quest",
            status="pending",
            raw_data={"not_a_quest": True}
        )

        script = QuestBuilderScript()
        script.do_build(broken_quest)

        broken_quest.refresh_from_db()
        self.assertEqual(broken_quest.status, "failed", "Builder should mark the quest as errored.")


class TestBuilderGoalHandling(EvenniaTestCase):
    def setUp(self):
        super().setUp()
        self.quest_id = str(uuid.uuid4())
        self.quest_data = {
            "quest": {
                "title": "The Glowing Delivery",
                "lore": "A glowing seed must be delivered to an ancient spirit.",
                "locations": [],  # intentionally left blank
                "objects": [],    # intentionally left blank
                "npcs": [],       # intentionally left blank
                "goals": [
                    {
                        "key": "Deliver the Seed",
                        "desc": "Give the glowing seed to the Spirit Guardian.",
                        "type": "giveto",
                        "target": "Spirit Guardian",
                        "object": "Glowing Seed"
                    }
                ]
            }
        }

        self.entry = QuestEntry.objects.create(
            quest_id=self.quest_id,
            title=self.quest_data["quest"]["title"],
            raw_data=self.quest_data,
            status="pending"
        )


    def test_giveto_goal_builds_required_assets(self):
        # Run the builder's at_repeat to process the quest
        script = QuestBuilderScript()
        script.do_build(self.entry)

        # Check that NPC was created
        npc = search_object("Spirit Guardian")
        self.assertTrue(npc)
        self.assertTrue(npc[0].location)
        self.assertTrue(any("quest:" in tag for tag in npc[0].tags.all()))

        # Check that object was created
        obj = search_object("Glowing Seed")
        self.assertTrue(obj)
        self.assertTrue(obj[0].location)
        self.assertTrue(any("quest:" in tag for tag in obj[0].tags.all()))

        # Ensure quest was marked as built
        updated = QuestEntry.objects.get(quest_id=self.quest_id)
        self.assertEqual(updated.status, "built")
