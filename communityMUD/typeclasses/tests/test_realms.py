from evennia.utils.test_resources import EvenniaTest
from realms.realmdef import RealmFactory  # Adjust based on your actual path

class TestRealmFactory(EvenniaTest):
    
    def test_get_realm(self):
        """Test that RealmFactory correctly returns a realm instance."""
        realm = RealmFactory().get_realm("realm_test")
        self.assertIsNotNone(realm, "Expected a realm instance, got None")
        self.assertEqual(realm.realm_name, "Test Realm", "Realm name mismatch")
        self.assertIn("scorpion", realm.get_creature_pool(), "Expected 'scorpion' in creature pool")
