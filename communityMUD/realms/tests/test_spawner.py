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
        self.spawner.interval = 600 # For this test, set the interval high enough that slow tests won't proc it happening outside the test itself.

    def tearDown(self):
        super().tearDown()  # Ensure any parent tearDown logic runs as well

        if self.room:
            self.room.contents.clear()
            for script in self.room.scripts.all(): script.delete()
            self.room.delete()
            self.spawner = None

    def test_spawner_attaches(self):
        """Ensure the spawner script is correctly attached to the room."""
        self.assertIsNotNone(self.spawner, "Spawner script failed to attach")
        self.assertEqual(self.spawner.db.spawn_location, self.room, "Spawner spawn location mismatch") # type: ignore

    def test_spawn_boundary_lower(self):
        realm = TestRealm()
    
        mob = self.spawner.do_spawn(realm, realm.spawn_chance - 0.01) # type: ignore
        print(f"Spawned mob: {mob}")

        self.assertEqual(self.countmobs(), 1, "There should be 1 and only 1 new creature.")

    def test_spawn_boundary_equals(self):
        realm = TestRealm()
        mob = self.spawner.do_spawn(realm, realm.spawn_chance) # type: ignore
        print(f"Spawned mob: {mob}")

        self.assertEqual(self.countmobs(), 1, "There should be 1 and only 1 new creature.")

    def test_spawn_boundary_higher(self):
        realm = TestRealm()
        mob = self.spawner.do_spawn(realm, realm.spawn_chance + 0.01) # type: ignore
        print(f"Spawned mob: {mob}")

        self.assertEqual(self.countmobs(), 0, "There should be no difference in the creature count.")