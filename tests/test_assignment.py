# coding=utf-8

import sqlite3
from unittest import TestCase

from game.assignment import AssignmentRepository

TASK_ID = 1337
OTHER_TASK_ID = 1334
USER = "user"
OTHER_USER = "other"


class TestAssignmentRepository(TestCase):

    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.repo = AssignmentRepository(self.con)

    def tearDown(self):
        self.con.close()

    def test_assign_to_player_returns_true(self):
        status = self.repo.assign(TASK_ID, USER)

        self.assertTrue(status)

    def test_assign_to_player_twice_returns_false(self):
        self.repo.assign(TASK_ID, USER)
        status = self.repo.assign(TASK_ID, USER)

        self.assertFalse(status)

    def test_assign_to_other_player_returns_false(self):
        self.repo.assign(TASK_ID, USER)
        status = self.repo.assign(TASK_ID, OTHER_USER)

        self.assertFalse(status)

    def test_assign_player_to_two_tasks_works(self):
        self.repo.assign(TASK_ID, USER)
        status = self.repo.assign(OTHER_TASK_ID, USER)

        self.assertTrue(status)

    def test_user_of_task_returns_user(self):
        self.repo.assign(TASK_ID, USER)

        user = self.repo.user_of_task(TASK_ID)

        self.assertEqual(user, USER)

    def test_user_of_unknown_task_returns_none(self):
        self.repo.assign(TASK_ID, USER)

        user = self.repo.user_of_task(OTHER_TASK_ID)

        self.assertIsNone(user)

    def test_remove_deletes_task(self):
        self.repo.assign(TASK_ID, USER)

        self.repo.remove(TASK_ID)

        self.assertIsNone(self.repo.user_of_task(TASK_ID))

    def test_remove_twice_does_not_throw(self):
        self.repo.assign(TASK_ID, USER)

        self.repo.remove(TASK_ID)
        self.repo.remove(TASK_ID)

        self.assertIsNone(self.repo.user_of_task(TASK_ID))

    def test_list_returns_assignments(self):
        self.repo.assign(TASK_ID, USER)
        self.repo.assign(OTHER_TASK_ID, OTHER_USER)

        assignments = self.repo.list()

        self.assertDictEqual(assignments, dict([(TASK_ID, USER), (OTHER_TASK_ID, OTHER_USER)]))

    def test_list_returns_empty_dict_when_no_assignments(self):
        assignments = self.repo.list()

        self.assertEqual(len(assignments), 0)

    def test_str_returns_assignments(self):
        self.repo.assign(TASK_ID, USER)
        self.repo.assign(OTHER_TASK_ID, OTHER_USER)

        out = self.repo.__str__()

        self.assertEquals(out, "Current assignments:\n"
                               "-> 1337 is assigned to user\n"
                               "-> 1334 is assigned to other\n")
