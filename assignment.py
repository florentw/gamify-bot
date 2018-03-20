#!/usr/bin/env python


class AssignmentRepository:
    """
    This class is responsible for the storage and querying of assignments.
    """

    def __init__(self):
        self.assignments = {}  # task_id -> slack_id

    def __str__(self):
        if len(self.assignments) == 0:
            return "No assignments."

        out = "Current assignments:\n"
        for task_id, slack_id in self.assignments.items():
            out += "-> " + str(task_id) + " is assigned to " + slack_id + "\n"

        return out

    def assign(self, task_id, slack_id):
        assigned_user = self.assignments.get(task_id)
        if assigned_user is not None:
            return False

        self.assignments[task_id] = slack_id
        return True

    def remove(self, task_id):
        self.assignments.pop(task_id)

    def user_of_task(self, task_id):
        return self.assignments.get(task_id)

    def list(self):
        return self.assignments
