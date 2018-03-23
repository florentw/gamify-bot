#!/usr/bin/env python

import sqlite3
import time

TASK_ASSIGNMENT_PERIOD = 900  # Assignment period: after this timeout, tasks will be automatically assigned to someone


class Task:

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
        # Expires after 15min
        return (time.time() - self.timestamp) > TASK_ASSIGNMENT_PERIOD


class TaskRepository:
    """
    This class is responsible for the storage and querying of tasks.
    """

    def __init__(self, connection):
        self.con = connection

        cursor = self.con.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS TASK "
                       "(id INTEGER PRIMARY KEY ASC, inserted TEXT, points INTEGER, description TEXT)")
        self.con.commit()

    @staticmethod
    def task_from_row(row):
        uid, inserted, points, description = row
        return Task(description, points, inserted, uid)

    def __str__(self):
        pending = self.pending()
        if len(pending) == 0:
            return "No pending tasks."

        out = "Opened tasks:\n"
        for task in pending:
            out += "-> " + str(task.uid) + ": " + str(task) + "\n"

        return out

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


if __name__ == "__main__":
    con = sqlite3.connect(":memory:")
    tasks = TaskRepository(con)

    tasks.insert(Task("Hello world"))
    tasks.insert(Task("Bouh"))
    print tasks.get(1)
    print tasks.get(0)
    print tasks.get(2)
    for t in tasks.pending():
        print "-> " + str(t)

    tasks.remove(1)

    for t in tasks.pending():
        print "-> " + str(t)

    tasks.remove(0)

    con.close()
