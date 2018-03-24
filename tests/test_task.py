import sqlite3
from unittest import TestCase

from game.task import TaskRepository, Task


class TestTaskRepository(TestCase):

    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.tasks = TaskRepository(self.con)

    def tearDown(self):
        self.con.close()

    def test_insert_tasks_returns_a_new_id(self):
        task_id_1 = self.tasks.insert(Task("Hello world", 3))
        task_id_2 = self.tasks.insert(Task("Hello world", 9))

        self.assertEquals(task_id_1, 1)
        self.assertEquals(task_id_2, 2)

    def test_insert_tasks_adds_it_and_can_be_read(self):
        task_id = self.tasks.insert(Task("Hello world", 3))

        task = self.tasks.get(task_id)
        self.assertEquals(task.description, "Hello world")
        self.assertEquals(task.points, 3)
        self.assertEquals(task.uid, 1)
        self.assertTrue(task.timestamp > 0)

    def test_get_unknown_task_returns_none(self):
        self.tasks.insert(Task("Hello world", 3))

        task = self.tasks.get(2)
        self.assertIsNone(task)

    def test_pending_returns_tasks_list(self):
        task_id_1 = self.tasks.insert(Task("Task1", 3))
        task_id_2 = self.tasks.insert(Task("Task2", 9))

        tasks_pending = self.tasks.pending()

        self.assertEquals(len(tasks_pending), 2)
        self.assertEquals(tasks_pending[0].description, "Task1")
        self.assertEquals(tasks_pending[0].uid, task_id_1)
        self.assertEquals(tasks_pending[1].description, "Task2")
        self.assertEquals(tasks_pending[1].uid, task_id_2)

    def test_remove_unknown_task_does_nothing(self):
        self.tasks.insert(Task("Task1", 3))

        self.tasks.remove(2)

        self.assertEquals(len(self.tasks.pending()), 1)

    def test_remove_known_task_deletes_from_table(self):
        self.tasks.insert(Task("Task1", 3))

        self.tasks.remove(1)

        self.assertEquals(len(self.tasks.pending()), 0)

    def test_str_returns_valid_string(self):
        self.tasks.insert(Task("Task1", 3))
        task = self.tasks.get(1)

        self.assertTrue(task.__str__().startswith("Task[1] 'Task1' inserted at "))
