# coding=utf-8

from unittest import TestCase

from game.game import Game

TEST_ADMIN_LIST = ["U1"]


class MockConf:

    def __init__(self, admins):
        self.admins = admins

    def admin_list(self):
        return self.admins

    @staticmethod
    def max_task_points():
        return 42


class TestGame(TestCase):

    def setUp(self):
        self.game = Game(MockConf(TEST_ADMIN_LIST), ":memory:")

    def tearDown(self):
        self.game.close()

    def test_join_inserts_a_new_user(self):
        (inserted, msg) = self.game.join("U1", "User1")

        self.assert_success(inserted, msg, "you are now registered")
        (status, scores) = self.game.list_high_scores("", "")
        self.assertTrue("U1" in scores)

    def test_join_same_user_twice_returns_false(self):
        self.game.join("U1", "User1")

        (inserted, msg) = self.game.join("U1", "User1")

        self.assert_error(inserted, msg, "you are already registered")

    def test_join_with_invalid_username_returns_false(self):
        (inserted, msg) = self.game.join("U1", "")

        self.assert_error(inserted, msg, "you have to provide a valid user name")

    def test_join_with_same_name_as_another_player_returns_false(self):
        self.game.join("U1", "User1")

        (inserted, msg) = self.game.join("U2", "User1")

        self.assert_error(inserted, msg, "someone is already registered with that name")

    def test_leave_removes_previously_registered_player(self):
        self.game.join("U1", "User1")

        (removed, msg) = self.game.leave("U1")

        self.assert_success(removed, msg, "you are now unregistered")

    def test_leave_returns_false_for_unknown_player(self):
        (removed, msg) = self.game.leave("U1")

        self.assert_error(removed, msg, "register first")

    def test_commands_returns_commands_dict(self):
        commands = self.game.commands()

        self.assertEquals(len(commands), 12)
        self.assertEquals(commands.get("!help")[1], "Prints the list of commands")
        self.assertEquals(commands.get("!help")[0], self.game.help)
        self.assertEquals(commands.get("!score"), commands.get("!scores"))

    def test_add_task_returns_false_if_player_not_registered(self):
        (inserted, msg) = self.game.add_task("unknown", "1 task")

        self.assert_have_to_register(msg, inserted)

    def test_add_task_returns_false_if_wrong_format_for_points(self):
        self.game.join("U1", "User1")

        (inserted, msg) = self.game.add_task("U1", "points task")

        self.assert_error(inserted, msg, "invalid format for points")

    def test_add_task_returns_false_if_empty_argument(self):
        self.game.join("U1", "User1")

        (inserted, msg) = self.game.add_task("U1", "")

        self.assert_error(inserted, msg, "invalid arguments")

    def test_take_added_task_returns_false_when_negative_points(self):
        self.game.join("U1", "User1")

        (inserted, msg) = self.game.add_task("U1", "-12 task")

        self.assert_error(inserted, msg, "points must be between 1 and 42 included")

    def test_take_added_task_returns_false_when_points_too_high(self):
        self.game.join("U1", "User1")

        (inserted, msg) = self.game.add_task("U1", "1337 task")

        self.assert_error(inserted, msg, "points must be between 1 and 42 included")

    def test_add_task_returns_task_id_when_inserted(self):
        self.game.join("U1", "User1")

        (inserted, msg) = self.game.add_task("U1", "3 New task")

        self.assert_success(inserted, msg, "added with id *1* for *3* point(s)")

    def test_take_added_task_returns_true(self):
        self.join_and_add_task()

        (status, msg) = self.game.take_task("U1", "1")

        self.assert_success(status, msg, "you are taking ownership of *New task* for 3 point(s)")

    def test_take_unknown_task_id_returns_false(self):
        self.join_and_add_task()

        (status, msg) = self.game.take_task("U1", "2")

        self.assert_task_does_not_exist(msg, status)

    def test_take_task_returns_false_if_player_not_registered(self):
        self.join_and_add_task()

        (status, msg) = self.game.take_task("U2", "1")

        self.assert_have_to_register(msg, status)

    def test_take_invalid_task_id_returns_false(self):
        self.game.join("U1", "User1")

        (status, msg) = self.game.take_task("U1", "")

        self.assert_error(status, msg, "invalid task id")

    def test_drop_task_returns_false_if_player_not_registered(self):
        self.join_and_add_task()

        (status, msg) = self.game.drop_task("U2", "1")

        self.assert_have_to_register(msg, status)

    def test_drop_task_with_invalid_task_id_returns_false(self):
        self.join_and_add_task()

        (status, msg) = self.game.drop_task("U1", "")

        self.assert_error(status, msg, "invalid task id")

    def test_drop_task_with_unknown_task_id_returns_false(self):
        self.join_and_add_task()

        (status, msg) = self.game.drop_task("U1", "2")

        self.assert_task_does_not_exist(msg, status)

    def test_drop_task_not_assigned_to_player_returns_false(self):
        self.join_and_add_task()

        (status, msg) = self.game.drop_task("U1", "1")

        self.assert_error(status, msg, "you are not assigned to this task")

    def test_drop_task_returns_true_when_successful(self):
        self.join_and_add_task()
        self.game.take_task("U1", "1")

        (status, msg) = self.game.drop_task("U1", "1")

        self.assertTrue(status)
        self.assertTrue("you are not assigned to this task anymore, your new score is *0* point(s)" in msg)
        (status, msg) = self.game.drop_task("U1", "1")
        self.assertFalse(status)

    def test_close_task_returns_false_if_player_not_registered(self):
        self.join_and_add_task()

        (status, msg) = self.game.close_task("U2", "1")

        self.assert_have_to_register(msg, status)

    def test_close_task_with_invalid_task_id_returns_false(self):
        self.join_and_add_task()

        (status, msg) = self.game.close_task("U1", "")

        self.assert_error(status, msg, "invalid task id")

    def test_close_task_with_unknown_task_id_returns_false(self):
        self.join_and_add_task()

        (status, msg) = self.game.close_task("U1", "2")

        self.assert_task_does_not_exist(msg, status)

    def test_drop_task_not_assigned_to_player_returns_true(self):
        self.join_and_add_task()

        (status, msg) = self.game.close_task("U1", "1")

        self.assert_success(status, msg, "the task *1*, *New task* has been closed by *User1*")

    def test_drop_task_assigned_to_player_returns_true(self):
        self.join_and_add_task()
        self.game.take_task("U1", "1")

        (status, msg) = self.game.close_task("U1", "1")

        self.assert_success(status, msg, "the task *1*, *New task* has been closed by *User1*")

    def test_list_tasks_returns_true_when_no_task(self):
        (status, msg) = self.game.list_tasks()

        self.assertTrue(status)
        self.assertTrue("No pending task." in msg)

    def test_list_tasks_returns_current_task_list(self):
        self.populate_tasks_list_and_assignments()

        (status, msg) = self.game.list_tasks()

        self.assertTrue(status)
        expected = "*5 pending tasks*:\n" + \
                   "> :heavy_check_mark: [*1*] *First task* [*3* points] :point_right: *User2*\n" + \
                   "> :heavy_check_mark: [*2*] *Second task* [*4* points] :point_right: *User1*\n" + \
                   "> :white_square: [*3*] *Third task'* [*1* points] `!take 3`\n" + \
                   "> :heavy_check_mark: [*4*] *Fourth task* [*10* points] :point_right: *User4*\n" + \
                   "> :heavy_check_mark: [*5*] *Fifth task* [*10* points] :point_right: *User5*\n"
        self.assertTrue(expected in msg)

    def test_list_high_scores_returns_true_when_no_score(self):
        (status, msg) = self.game.list_high_scores()

        self.assertTrue(status)
        self.assertTrue("No scores yet." in msg)

    def test_list_high_scores_returns_ordered_players_list(self):
        self.populate_tasks_list_and_assignments()

        (status, msg) = self.game.list_high_scores()

        self.assertTrue(status)
        expected = ":checkered_flag: *High scores* (5 players):\n" + \
                   "> 1. :first_place_medal: *User4* (<@U4>) with *10* point(s)\n" + \
                   "> 2. :first_place_medal: *User5* (<@U5>) with *10* point(s)\n" + \
                   "> 3. :second_place_medal: *User1* (<@U1>) with *4* point(s)\n" + \
                   "> 4. :third_place_medal: *User2* (<@U2>) with *3* point(s)\n" + \
                   "> 5. :white_small_square: *User3* (<@U3>) with *0* point(s)\n"
        self.assertTrue(expected in msg)

    def test_assign_with_weighted_random_return_false_when_user_not_registered(self):
        self.join_and_add_task()

        (status, msg) = self.game.assign_with_weighted_random("U2", "1")

        self.assert_have_to_register(msg, status)

    def test_assign_with_weighted_random_return_false_when_task_id_does_not_exist(self):
        self.join_and_add_task()

        (status, msg) = self.game.assign_with_weighted_random("U1", "2")

        self.assert_task_does_not_exist(msg, status)

    def test_assign_with_weighted_random_return_false_when_task_id_invalid(self):
        self.join_and_add_task()

        (status, msg) = self.game.assign_with_weighted_random("U1", "garbage")

        self.assert_error(status, msg, "invalid task id")

    def test_assign_with_weighted_random_an_already_assigned_task_returns_false(self):
        self.join_and_add_task()
        self.game.take_task("U1", "1")

        (status, msg) = self.game.assign_with_weighted_random("U1", "1")

        self.assert_error(status, msg, "a player is already assigned to this task")

    def test_assign_with_weighted_random_assigns_task_to_unique_player(self):
        self.join_and_add_task()

        (status, msg) = self.game.assign_with_weighted_random("U1", "1")

        self.assert_success(status, msg, "The universe has spoken, congrats <@U1>")

    def test_assign_with_weighted_random_assigns_task_to_of_two_players(self):
        self.game.join("U1", "User1")
        self.game.join("U2", "User2")
        self.game.add_task("U1", "3 New task")
        self.game.add_task("U2", "15 A task")
        self.game.take_task("U2", "2")

        (status, msg) = self.game.assign_with_weighted_random("U1", "1")

        self.assertTrue(status)
        self.assertTrue("congrats <@U1>" in msg or "congrats <@U2>" in msg)

    def test_help_returns_list_of_commands(self):
        (status, help_output) = self.game.help()

        self.assertTrue(status)
        for command, (function, description) in self.game.commands().items():
            self.assertTrue(command in help_output)
            self.assertTrue(description in help_output)

    def test_reset_all_scores_returns_false_if_not_registered(self):
        self.join_and_add_task()

        (status, msg) = self.game.reset_all_scores("U2")

        self.assert_have_to_register(msg, status)

    def test_reset_all_scores_returns_false_if_not_admin(self):
        self.game.join("U3", "User3")

        (status, msg) = self.game.reset_all_scores("U3")

        self.assertFalse(status)
        self.assertTrue("this action can only be performed by an admin" in msg)

    def test_reset_all_scores_returns_true_if_admin(self):
        self.join_and_add_task()
        self.game.take_task("U1", "1")

        (status, msg) = self.game.reset_all_scores("U1")

        self.assertTrue(status)
        self.assertTrue("you successfully reset all player scores to 0" in msg)

    def assert_error(self, status, msg, expected_msg):
        self.assertFalse(status)
        self.assertTrue(expected_msg in msg)

    def assert_success(self, status, msg, expected_msg):
        self.assertTrue(status)
        self.assertTrue(expected_msg in msg)

    def assert_have_to_register(self, msg, status):
        self.assertFalse(status)
        self.assertTrue("you have to register first" in msg)

    def join_and_add_task(self):
        self.game.join("U1", "User1")
        self.game.add_task("U1", "3 New task")

    def assert_task_does_not_exist(self, msg, status):
        self.assertFalse(status)
        self.assertTrue("this task does not exist" in msg)

    def populate_tasks_list_and_assignments(self):
        self.game.join("U1", "User1")
        self.game.join("U2", "User2")
        self.game.join("U3", "User3")
        self.game.join("U4", "User4")
        self.game.join("U5", "User5")

        self.game.add_task("U1", "3 \"First task\"")
        self.game.add_task("U1", "4 'Second task'")
        self.game.add_task("U1", "1 Third task'")
        self.game.add_task("U1", "10 Fourth task")
        self.game.add_task("U1", "10 Fifth task")

        self.game.take_task("U1", "2")
        self.game.take_task("U2", "1")
        self.game.take_task("U4", "4")
        self.game.take_task("U5", "5")
