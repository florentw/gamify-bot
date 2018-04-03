#!/usr/bin/env python
# coding=utf-8

import sqlite3


class AssignmentRepository:
    """
    This class is responsible for the storage and querying of assignments.
    """

    def __init__(self, connection):
        self.con = connection

        cursor = self.con.cursor()
        self.create_assignment_table(cursor)
        self.con.commit()

    def __str__(self):
        assignments = self.list()
        if len(assignments) == 0:
            return "No assignments."

        out = "Current assignments:\n"
        for task_id, player_id in assignments.items():
            out += "-> " + str(task_id) + " is assigned to " + player_id + "\n"

        return out

    def assign(self, task_id, player_id):
        cursor = self.con.cursor()
        try:
            cursor.execute("INSERT INTO ASSIGNMENT(task_id, player_id) VALUES (?,?)",
                           (task_id, player_id))
        except sqlite3.IntegrityError:
            return False

        return True

    def remove(self, task_id):
        cursor = self.con.cursor()
        cursor.execute("DELETE FROM ASSIGNMENT WHERE task_id=?", (task_id,))
        self.con.commit()

    def user_of_task(self, task_id):
        cursor = self.con.cursor()
        cursor.execute("SELECT player_id FROM ASSIGNMENT WHERE task_id=?", (task_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return row[0]

    def list(self):
        cursor = self.con.cursor()
        cursor.execute("SELECT task_id, player_id FROM ASSIGNMENT")

        assign_dict = {}
        while True:
            row = cursor.fetchone()
            if row is None:
                break

            task_id, player_id = row
            assign_dict[task_id] = player_id

        return assign_dict

    @staticmethod
    def upgrade_from_0_to_1(con):
        cursor = con.cursor()

        cursor.execute("ALTER TABLE ASSIGNMENT RENAME TO TMP_ASSIGNMENT")
        AssignmentRepository.create_assignment_table(cursor)
        cursor.execute("INSERT INTO ASSIGNMENT(task_id, player_id) SELECT task_id, slack_id FROM TMP_ASSIGNMENT")
        cursor.execute("DROP TABLE TMP_ASSIGNMENT")

        con.commit()

    @staticmethod
    def create_assignment_table(cursor):
        cursor.execute("CREATE TABLE IF NOT EXISTS ASSIGNMENT "
                       "(task_id INTEGER NOT NULL UNIQUE, player_id TEXT NOT NULL, UNIQUE(task_id, player_id))")
