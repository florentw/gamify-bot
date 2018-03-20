
import sqlite3

from task import Task,TaskRepository
from assignement import AssignementRepository
from player import PlayerRepository, Player

class Game:
    """
    A bot that gamifies routine development tasks that are shared among team members.

    When a new routine task is entered, a team member can then assign it to him,
    and will earn an amount of points that was defined when adding it.
    """

    def __init__(self):
        self.connection = sqlite3.connect("gamifybot.db")
        self.high_scores = {}   # User -> Score
        self.players = PlayerRepository(self.connection)
        self.tasks = TaskRepository(self.connection)
        self.assignements = AssignementRepository()

    def close(self):
        self.connection.close()

    def add_task(self, slack_id, description):
        if self.players.get_by_id(slack_id) is None:
            return False, "you have to register first: `!join &lt;user name&gt;`"

        task_id = self.tasks.insert(Task(description))
        return True, "new task *'"+description+"'*, added with id *"+str(task_id)+"*!\nYou can take it by saying: `!take "+str(task_id)+"`"

    def take_task(self, slack_id, argument):
        player = self.players.get_by_id(slack_id)
        if player is None:
            return False, "you have to register first: `!join &lt;user name&gt;`"

        task_id = self.check_task_id(argument)
        if task_id is None:
            return False, "invalid task id"

        task = self.tasks.get(task_id)
        if task == None:
            return False, "this task does not exist."

        if self.assignements.assign(task_id, slack_id) is False:
            return False, "a player is already assigned to this task."

        player = self.players.update_points(slack_id, task.points)

        return True, "You are taking ownership of *"+task.description+"* for "+str(task.points)+" point(s).\nYour new score is *"+str(player.points)+"* point(s).\nIf you want to drop it, say: `!drop "+str(task_id)+"`"

    def close_task(self, slack_id, argument):
        player = self.players.get_by_id(slack_id)
        if player is None:
            return False, "you have to register first: `!join &lt;user name&gt;`"

        task_id = self.check_task_id(argument)
        if task_id is None:
            return False, "invalid task id"

        task = self.tasks.get(task_id)
        if task == None:
            return False, "This task does not exist."

        self.assignements.remove(task_id)
        self.tasks.remove(task_id)
        return True, "The task *"+str(task_id)+"*, *"+task.description+"* has been closed by *"+player.name+"*."

    def drop_task(self, slack_id, argument):
        player = self.players.get_by_id(slack_id)
        if player is None:
            return False, "you have to register first: `!join &lt;user name&gt;`"

        task_id = self.check_task_id(argument)
        if task_id is None:
            return False, "invalid task id"

        task = self.tasks.get(task_id)
        if task == None:
            return False, "This task does not exist."

        assignee = self.assignements.user_of_task(task_id)
        if assignee != player.slack_id:
            return False, "You are not assigned to this task."

        self.assignements.remove(task_id)
        player = self.players.update_points(slack_id, -task.points)
        return True, "You are not assigned to this task anymore, your new score is *"+str(player.points)+"* point(s)."

    def list_tasks(self):
        pending = self.tasks.pending()
        assignements = self.assignements.list()

        if len(pending) is 0:
            return True, "No pending task."

        out = ":pushpin: *"+str(len(pending))+" pending tasks*:\n"
        for task in pending:
            icon = ":white_square:"
            assigned = "`!take "+str(task.uid)+"`"

            if task.uid in assignements:
                assigned = ":point_right: *"+self.players.get_by_id(assignements[task.uid]).name+"*"
                icon = ":heavy_check_mark:"

            out += "> "+icon+" [*"+str(task.uid)+"*] *"+task.description+"* [*"+str(task.points)+"* points] "+assigned+"\n"

        return True, out

    def list_high_scores(self):
        scores = self.players.scores()

        if len(scores) is 0:
            return True, "No scores yet."

        out = ":checkered_flag: *High scores* ("+str(len(scores))+" players):\n"
        place = 1
        previous_score = None
        for index, player in enumerate(scores):
            if previous_score is None:
                previous_score = player.points
            elif player.points < previous_score: # Do we have ex-aequo?
                previous_score = player.points
                place += 1

            medal = ":white_small_square:"
            if place == 1:
                medal = ":first_place_medal:"
            if place == 2:
                medal = ":second_place_medal:"
            if place == 3:
                medal = ":third_place_medal:"

            out += "> "+str(index + 1)+". "+medal+" *"+player.name+"* (<@"+player.slack_id+">) with *"+str(player.points)+"* point(s)\n"

        return True, out

    def list_scores(self):
        return sorted(self.high_scores.items(), key=lambda x: (-x[1], x[0]))

    def check_not_empty(self, argument):
        if len(argument) is 0:
            return False

        return True

    def check_task_id(self, argument):
        task_id = None
        try:
            task_id = int(argument)
            return task_id
        except ValueError:
            return None

    def leave(self, slack_id):
        if self.players.get_by_id(slack_id) is None:
            return False, "you have to register first: `!join &lt;user name&gt;`"

        self.players.remove(slack_id)
        return True, "you are now unregistered."

    def join(self, slack_id, name):
        if self.check_not_empty(name) is False:
            return False, "you have to provide a valid user name: `!join &lt;user name&gt;`"

        if self.players.get_by_id(slack_id) is not None:
            return False, "you are already registered"

        if self.players.name_exists(name):
            return False, "someone is already registered with that name"

        self.players.add(Player(slack_id, name))
        return True, "you are now registered as *"+name+"*"
