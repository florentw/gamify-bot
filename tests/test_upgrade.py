import sqlite3
from unittest import TestCase

from game.upgrade import Upgrade

CURRENT_VERSION = "0.7"


class TestUpgrade(TestCase):

    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.upgrade = Upgrade(self.con)
        self.called_1 = False
        self.called_2 = False

    def tearDown(self):
        self.con.close()

    def test_fetch_data_model_version_returns_None_after_init(self):
        model_version = self.upgrade.fetch_data_model_version()

        self.assertIsNone(model_version)

    def test_fetch_data_model_version_returns_codebase_version_after_init(self):
        initial_version = self.upgrade.detect_initial_state(CURRENT_VERSION)

        model_version = self.upgrade.fetch_data_model_version()

        self.assertIsNone(initial_version)
        self.assertEquals(model_version, CURRENT_VERSION)

    def test_select_or_insert_version_returns_existing_version(self):
        self.upgrade.detect_initial_state(CURRENT_VERSION)

        detected_version = self.upgrade.select_or_insert_version("1.0")
        self.assertEquals(detected_version, CURRENT_VERSION)

    def test_perform_upgrade_does_nothing_when_target_is_same(self):
        self.upgrade.detect_initial_state(CURRENT_VERSION)

        (status, msg) = self.upgrade.perform_upgrade(CURRENT_VERSION)

        self.assertTrue(status)
        self.assertEquals(msg, "Data model is up to date.")

    def test_perform_upgrade_returns_false_if_downgrade(self):
        self.upgrade.select_or_insert_version(CURRENT_VERSION)

        (status, msg) = self.upgrade.perform_upgrade("-1.0")

        self.assertFalse(status)
        self.assertEquals(msg, "Trying to downgrade the data model from 0.0 to -1.0, this is not supported.")

    def test_perform_upgrade_returns_true_if_upgrade_and_updates_version(self):
        self.upgrade = Upgrade(self.con, [self.upgrade_call_1, self.upgrade_call_2])
        self.upgrade.select_or_insert_version("0.0")

        (status, msg) = self.upgrade.perform_upgrade("2.0")

        self.assertTrue(status)
        self.assertEquals(msg, "Successfully upgraded from 0.0 to 2.0.")
        detected_version = self.upgrade.fetch_data_model_version()
        self.assertEquals(detected_version, "2.0")
        self.assertTrue(self.called_1)
        self.assertTrue(self.called_2)

    def upgrade_call_1(self):
        self.called_1 = True

    def upgrade_call_2(self):
        self.called_2 = True
