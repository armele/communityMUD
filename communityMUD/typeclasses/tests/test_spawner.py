from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from typeclasses.creatures.spawn import RealmSpawner
from realms.realmdef import TestRealm

# https://www.evennia.com/docs/latest/Coding/Unit-Testing.html

class TestRealmSpawner(EvenniaTest):

    def setUp(self):
        print(f"Running test: {self._testMethodName}")
        super().setUp()
        """Set up a test room and attach the spawner script."""
        self.room = create.create_object("evennia.objects.objects.DefaultRoom", key="TestRoom", nohome=True)
        self.room.db.realm = "realm_test"
        self.spawner = self.room.scripts.add(RealmSpawner)

    def tearDown(self):
        """Clean up any spawned mobs after each test."""
        for obj in self.room.contents[:]:  # Copy the list to avoid modification issues
            if obj.is_typeclass("typeclasses.creatures.basecreature.Mob"):
                obj.delete()
        super().tearDown()  # Ensure any parent tearDown logic runs as well

    def test_spawner_attaches(self):
        """Ensure the spawner script is correctly attached to the room."""
        self.assertIsNotNone(self.spawner, "Spawner script failed to attach")
        self.assertEqual(self.spawner.db.spawn_location, self.room, "Spawner spawn location mismatch")

    def test_spawner_creature_selection(self):
        """Test that the spawner selects a valid creature within 10 attempts.
            I recognize this will improperly fail a small percentage of the time,
            but it's a good enough test for now."""
        for _ in range(10):  # Attempt up to 10 times
            self.spawner.at_repeat()  # Manually trigger a spawn
            spawned_creatures = [
                obj for obj in self.room.contents 
                if obj.is_typeclass("typeclasses.creatures.basecreature.Mob")
            ]
            if spawned_creatures:  # Stop early if a creature was spawned
                break  

        self.assertGreater(len(spawned_creatures), 0, "No creature was spawned after 10 attempts")

    def test_spawn_boundary_lower(self):
        realm = TestRealm()
    
        self.spawner.do_spawn(realm, realm.spawn_chance - 0.01)

        spawned_creatures = [
            obj for obj in self.room.contents 
            if obj.is_typeclass("typeclasses.creatures.basecreature.Mob")
        ]

        self.assertEqual(len(spawned_creatures), 1, "No creature was spawned.")

    def test_spawn_boundary_equals(self):
        realm = TestRealm()
        self.spawner.do_spawn(realm, realm.spawn_chance)

        spawned_creatures = [
            obj for obj in self.room.contents 
            if obj.is_typeclass("typeclasses.creatures.basecreature.Mob")
        ]

        self.assertEqual(len(spawned_creatures), 1, "No creature was spawned.")

    def test_spawn_boundary_higher(self):
        realm = TestRealm()
        self.spawner.do_spawn(realm, realm.spawn_chance + 0.01)

        spawned_creatures = [
            obj for obj in self.room.contents 
            if obj.is_typeclass("typeclasses.creatures.basecreature.Mob")
        ]

        self.assertEqual(len(spawned_creatures), 0, "A creature was spawned, but should not have been")