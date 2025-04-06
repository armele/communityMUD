from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from typeclasses.creatures.spawn import RealmSpawner
from realms.realmdef import TestRealm
import time

# https://www.evennia.com/docs/latest/Coding/Unit-Testing.html

class TestRealmSpawner(EvenniaTest):
    def countmobs(self):
        spawned_creatures = [
            obj for obj in self.room.contents 
            if obj.is_typeclass("typeclasses.creatures.basecreature.Mob")
        ]
        return len(spawned_creatures)

    def setUp(self):
        print(f"Running test: {self._testMethodName}")
        super().setUp()
        """Set up a test room and attach the spawner script."""
        self.room = create.create_object("evennia.objects.objects.DefaultRoom", key=self._testMethodName, nohome=True) # A new room for every test...
        self.room.db.realm = "realm_test"
        self.spawner = self.room.scripts.add(RealmSpawner)
        self.roomcount = self.countmobs()

    def tearDown(self):
        super().tearDown()  # Ensure any parent tearDown logic runs as well

    def test_spawner_attaches(self):
        """Ensure the spawner script is correctly attached to the room."""
        self.assertIsNotNone(self.spawner, "Spawner script failed to attach")
        self.assertEqual(self.spawner.db.spawn_location, self.room, "Spawner spawn location mismatch")

    def test_spawner_creature_selection(self):
        """Test that the spawner selects a valid creature within 20 attempts.
            I recognize this will improperly fail a small percentage of the time,
            but it's a good enough test for now."""
        for _ in range(20):  # Attempt up to 20 times
            self.spawner.at_repeat()  # Manually trigger a spawn

        self.assertGreater(self.countmobs(), self.roomcount, "No creature was spawned after 20 attempts")

    def test_spawn_boundary_lower(self):
        realm = TestRealm()
    
        self.spawner.do_spawn(realm, realm.spawn_chance - 0.01)

        self.assertEqual(self.countmobs(), self.roomcount + 1, "There should be 1 and only 1 new creature.")

    def test_spawn_boundary_equals(self):
        realm = TestRealm()
        self.spawner.do_spawn(realm, realm.spawn_chance)

        self.assertEqual(self.countmobs(), self.roomcount + 1, "There should be 1 and only 1 new creature.")

    def test_spawn_boundary_higher(self):
        realm = TestRealm()
        self.spawner.do_spawn(realm, realm.spawn_chance + 0.01)

        self.assertEqual(self.countmobs(), self.roomcount, "There should be no difference in the creature count.")