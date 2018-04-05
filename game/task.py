#!/usr/bin/env python
# coding=utf-8

from builtins import str
from builtins import object
import time

DEFAULT_MAX_TASK_POINTS = 42

TASK_ASSIGNMENT_PERIOD = 900  # Assignment period: after this timeout, tasks will be automatically assigned to someone


class Task(object):

    def __init__(self, description, points=1, timestamp=None, uid=None):
        if timestamp is None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp

        self.description = description
        self.points = points
        self.uid = uid

    def __str__(self):
        return "Task[" + str(self.uid) + "] '" + self.description + "' inserted at " + str(self.timestamp)

    def has_expired(self):
        return (time.time() - self.timestamp) > TASK_ASSIGNMENT_PERIOD


class TaskRepository(object):
    """
    This class is responsible for the storage and querying of tasks.
    """

    def __init__(self, connection):
        self.con = connection

        cursor = self.con.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS TASK ("
                       "id INTEGER PRIMARY KEY ASC NOT NULL, "
                       "inserted TEXT NOT NULL, "
                       "points INTEGER NOT NULL, "
                       "description TEXT NOT NULL)")
        self.con.commit()

    @staticmethod
    def task_from_row(row):
        uid, inserted, points, description = row
        return Task(description, points, inserted, uid)

    def get(self, uid):
        cursor = self.con.cursor()
        cursor.execute("SELECT * FROM TASK WHERE id=?", (uid,))
        row = cursor.fetchone()

        if row is None:
            return None

        return self.task_from_row(row)

    def insert(self, task):
        cursor = self.con.cursor()
        cursor.execute("INSERT INTO TASK(inserted, points, description) VALUES (?,?,?)",
                       (str(task.timestamp), task.points, task.description))
        task_id = cursor.lastrowid
        self.con.commit()
        return task_id

    def pending(self):
        cursor = self.con.cursor()
        cursor.execute("SELECT * FROM TASK")

        pending_tasks = []
        while True:
            row = cursor.fetchone()
            if row is None:
                break

            pending_tasks.append(self.task_from_row(row))

        return pending_tasks

    def remove(self, uid):
        cursor = self.con.cursor()
        cursor.execute("DELETE FROM TASK WHERE id=?", (uid,))
        self.con.commit()

    def validate_task(self, argument):
        task_id = self.check_task_id(argument)
        if task_id is None:
            return None, "invalid task id"

        task = self.get(task_id)
        if task is None:
            return None, "this task does not exist."

        return task, ""

    @staticmethod
    def check_task_id(argument):
        try:
            task_id = int(argument)
            return task_id
        except ValueError:
            return None

    @staticmethod
    def points_from(argument, max_task_points=None):

        if max_task_points is None:
            max_task_points = DEFAULT_MAX_TASK_POINTS

        try:
            split = argument.split(None, 1)
            if split is None or len(split) == 0:
                return None, "invalid arguments"

            points = int(split[0])
            if points < 0 or points > max_task_points:
                return None, "points must be between 1 and " + str(max_task_points) + " included"

            return points, ""

        except ValueError:
            return None, "invalid format for points"

    @staticmethod
    def remove_trailing_quotes(description):
        if (description.startswith('"') and description.endswith('"')) or \
                (description.startswith('\'') and description.endswith('\'')):
            description = description[1:-1]

        return description
