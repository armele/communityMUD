from evennia.utils.test_resources import EvenniaTest
from realms.realmdef import RealmFactory, Realm  # Adjust based on your actual path
import os
from typing import cast

class TestRealmFactory(EvenniaTest):
    
    def test_get_realm(self):
        """Test that RealmFactory correctly returns a realm instance."""
        print(f"Running test: {self._testMethodName}")        
        realm = cast(Realm, RealmFactory.get_realm("realm_test"))
        self.assertIsNotNone(realm, "Expected a realm instance, got None")
        self.assertEqual(realm.realm_name, "Test Realm", "Realm name mismatch") # type: ignore
        self.assertIn("scorpion", realm.get_creature_pool(), "Expected 'scorpion' in creature pool")

    def test_gather_lore(self):
        """Test that RealmFactory correctly gathers lore from realms."""
        print(f"Running test: {self._testMethodName}")        
        lore = RealmFactory.gatherLore()
        self.assertGreater(len(lore), 0, "Expected non-empty lore list")        
        self.assertIn("In Test Realm: The mystery of the realm is difficult to discern.", lore)

    def test_embed_lore(self):
        """Test that RealmFactory correctly embeds lore in rooms."""
        print(f"Running test: {self._testMethodName}")        
        lore = RealmFactory.embedLore()
        self.assertTrue(os.path.exists("severed_realms_embeddings.json"), "Expected 'severed_realms_embeddings.json' to be created")