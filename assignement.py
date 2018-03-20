
class AssignementRepository:
    """
    This class is responsible for the storage and querying of assignements.
    """

    def __init__(self):
        self.assignements = {} # task_id -> slack_id

    def __str__(self):
        if len(self.assignements) == 0:
            return "No assignements."

        out = "Current assignements:\n"
        for task_id, slack_id in self.assignements.items():
            out += "-> "+str(task_id)+" is assigned to "+slack_id+"\n"

        return out

    def assign(self, task_id, slack_id):
        assigned_user = self.assignements.get(task_id)
        if assigned_user != None:
            return False

        self.assignements[task_id] = slack_id
        return True

    def remove(self, task_id):
        self.assignements.pop(task_id)

    def user_of_task(self, task_id):
        return self.assignements.get(task_id)

    def list(self):
        return self.assignements
