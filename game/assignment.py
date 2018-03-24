#!/usr/bin/env python
import sqlite3


class AssignmentRepository:
    """
    This class is responsible for the storage and querying of assignments.
    """

    def __init__(self, connection):
        self.con = connection

        cursor = self.con.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS ASSIGNMENT "
                       "(task_id INTEGER NOT NULL UNIQUE, slack_id TEXT NOT NULL, UNIQUE(task_id, slack_id))")
        self.con.commit()

    def __str__(self):
        assignments = self.list()
        if len(assignments) == 0:
            return "No assignments."

        out = "Current assignments:\n"
        for task_id, slack_id in assignments.items():
            out += "-> " + str(task_id) + " is assigned to " + slack_id + "\n"

        return out

    def assign(self, task_id, slack_id):
        cursor = self.con.cursor()
        try:
            cursor.execute("INSERT INTO ASSIGNMENT(task_id, slack_id) VALUES (?,?)",
                           (task_id, slack_id))
        except sqlite3.IntegrityError:
            return False

        return True

    def remove(self, task_id):
        cursor = self.con.cursor()
        cursor.execute("DELETE FROM ASSIGNMENT WHERE task_id=?", (task_id,))
        self.con.commit()

    def user_of_task(self, task_id):
        cursor = self.con.cursor()
        cursor.execute("SELECT slack_id FROM ASSIGNMENT WHERE task_id=?", (task_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return row[0]

    def list(self):
        cursor = self.con.cursor()
        cursor.execute("SELECT task_id, slack_id FROM ASSIGNMENT")

        assign_dict = {}
        while True:
            row = cursor.fetchone()
            if row is None:
                break

            task_id, slack_id = row
            assign_dict[task_id] = slack_id

        return assign_dict
