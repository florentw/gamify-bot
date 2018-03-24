import sqlite3
from unittest import TestCase

from game.player import PlayerRepository, Player

SLACK_ID_1 = "U1"
USER_1 = "user1"
PLAYER_1 = Player("U1", USER_1)


class TestPlayerRepository(TestCase):

    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.players = PlayerRepository(self.con)

    def tearDown(self):
        self.con.close()

    def test_get_by_id_unknown_player_is_none(self):
        actual_player = self.players.get_by_id("unknown")

        self.assertIsNone(actual_player)

    def test_add_players_and_get_by_id(self):
        self.assertTrue(self.players.add(PLAYER_1))
        self.assertTrue(self.players.add(Player("U2", "user2")))

        actual_player = self.players.get_by_id(SLACK_ID_1)

        self.assertEqual(actual_player.name, USER_1)
        self.assertEqual(actual_player.points, 0)
        self.assertEqual(actual_player.slack_id, SLACK_ID_1)
        self.assertEqual(actual_player.__str__(), "user1(U1), 0 point(s)")

    def test_add_same_player_twice_returns_false(self):
        self.players.add(PLAYER_1)

        insertion = self.players.add(PLAYER_1)
        self.assertFalse(insertion)

    def test_name_exists_is_true_for_added_user(self):
        self.players.add(PLAYER_1)

        self.assertTrue(self.players.name_exists(USER_1))

    def test_name_exists_is_false_for_unknown_user(self):
        self.players.add(PLAYER_1)

        self.assertFalse(self.players.name_exists("unknown"))

    def test_remove_returns_false_when_user_unknown(self):
        self.players.add(PLAYER_1)

        self.assertFalse(self.players.remove("U2"))

    def test_remove_returns_true_and_removes_known_player(self):
        self.players.add(PLAYER_1)

        self.assertTrue(self.players.remove(SLACK_ID_1))
        self.assertFalse(self.players.name_exists(USER_1))

    def test_update_points_of_known_user(self):
        self.players.add(PLAYER_1)

        player = self.players.update_points(SLACK_ID_1, 10)

        self.assertEquals(player.points, 10)
        self.assertEquals(self.players.get_by_id(SLACK_ID_1).points, 10)

    def test_update_points_of_unknown_user_is_none(self):
        self.players.add(PLAYER_1)

        self.assertIsNone(self.players.update_points("U2", 10))

        player = self.players.get_by_id(SLACK_ID_1)
        self.assertEquals(player.points, 0)

    def test_update_points_twice_works(self):
        self.players.add(PLAYER_1)

        self.players.update_points(SLACK_ID_1, 1000)
        player = self.players.update_points(SLACK_ID_1, 337)

        self.assertEquals(player.points, 1337)
        self.assertEquals(self.players.get_by_id(SLACK_ID_1).points, 1337)

    def test_scores_returns_ordered_list_of_players(self):
        self.players.add(PLAYER_1)
        self.players.add(Player("U2", "user2"))
        self.players.add(Player("U3", "user3"))
        self.players.update_points(SLACK_ID_1, 42)
        self.players.update_points("U2", 1337)
        self.players.update_points("U3", 7)

        scores = self.players.scores()

        self.assertEquals(len(scores), 3)
        self.assertEquals(scores[0].name, "user2")
        self.assertEquals(scores[1].name, USER_1)
        self.assertEquals(scores[2].name, "user3")

    def test_scores_returns_empty_list_of_players(self):
        scores = self.players.scores()

        self.assertEquals(len(scores), 0)