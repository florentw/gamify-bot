#!/usr/bin/env python

import sqlite3
from random import randint

from assignment import AssignmentRepository
from player import PlayerRepository, Player
from task import Task, TaskRepository

MAX_TASK_POINTS = 42
DATABASE_FILE_NAME = "gamifybot.db"


class Game:
    """
    A bot that gamifies routine development tasks that are shared among team members.

    When a new routine task is entered, a team member can then assign it to him,
    and will earn an amount of points that was defined when adding it.
    """

    def __init__(self):
        self.connection = sqlite3.connect(DATABASE_FILE_NAME)
        self.high_scores = {}  # User -> Score
        self.players = PlayerRepository(self.connection)
        self.tasks = TaskRepository(self.connection)
        self.assignments = AssignmentRepository(self.connection)

    def close(self):
        self.connection.close()

    def add_task(self, slack_id, argument):
        if self.players.get_by_id(slack_id) is None:
            return False, "you have to register first: `!join &lt;user name&gt;`"

        (points, msg) = self.points_from(argument)
        if points is None:
            return False, msg + ", usage: `!add &lt;points&gt; &lt;description&gt;`"

        if len(argument.split(None, 1)) == 2:
            description = self.remove_trailing_quotes(argument.split(None, 1)[1])

        else:
            return False, "invalid arguments: `!add &lt;points&gt; &lt;description&gt;`"

        task_id = self.tasks.insert(Task(description, points))
        return True,\
               "new task *'" + description + "'*, added with id *" + str(task_id) + "* for *" + str(points) + \
               "* point(s)!\nYou can take it by saying: `!take " + str(task_id) + "`"

    def take_task(self, slack_id, argument):
        player = self.players.get_by_id(slack_id)
        if player is None:
            return False, "you have to register first: `!join &lt;user name&gt;`"

        (task, msg) = self.validate_task(argument)
        if task is None:
            return False, msg

        return self.assign_and_update_score(slack_id, task)

    def close_task(self, slack_id, argument):
        player = self.players.get_by_id(slack_id)
        if player is None:
            return False, "you have to register first: `!join &lt;user name&gt;`"

        (task, msg) = self.validate_task(argument)
        if task is None:
            return False, msg

        self.assignments.remove(task.uid)
        self.tasks.remove(task.uid)
        return True, "The task *" + str(task.uid) + "*, *" + task.description + \
               "* has been closed by *" + player.name + "*."

    def drop_task(self, slack_id, argument):
        player = self.players.get_by_id(slack_id)
        if player is None:
            return False, "you have to register first: `!join &lt;user name&gt;`"

        (task, msg) = self.validate_task(argument)
        if task is None:
            return False, msg

        assignee = self.assignments.user_of_task(task.uid)
        if assignee != player.slack_id:
            return False, "You are not assigned to this task."

        self.assignments.remove(task.uid)
        player = self.players.update_points(slack_id, -task.points)
        return True, "You are not assigned to this task anymore, your new score is *" + str(
            player.points) + "* point(s)."

    def list_tasks(self):
        pending = self.tasks.pending()
        assignments = self.assignments.list()

        if len(pending) is 0:
            return True, "No pending task."

        out = ":pushpin: *" + str(len(pending)) + " pending tasks*:\n"
        for task in pending:
            icon = ":white_square:"
            assigned = "`!take " + str(task.uid) + "`"

            slack_id = assignments.get(task.uid)
            if slack_id is not None:
                assigned = ":point_right: *" + self.players.get_by_id(slack_id).name + "*"
                icon = ":heavy_check_mark:"

            out += "> " + icon + " [*" + str(task.uid) + "*] *" + task.description + "* [*" + str(
                task.points) + "* points] " + assigned + "\n"

        return True, out

    def list_high_scores(self):
        scores = self.players.scores()

        if len(scores) is 0:
            return True, "No scores yet."

        out = ":checkered_flag: *High scores* (" + str(len(scores)) + " players):\n"
        place = 1
        previous_score = None
        for index, player in enumerate(scores):
            if previous_score is None:
                previous_score = player.points
            elif player.points < previous_score:  # Do we have ex-aequo?
                previous_score = player.points
                place += 1

            medal = ":white_small_square:"
            if place == 1:
                medal = ":first_place_medal:"
            if place == 2:
                medal = ":second_place_medal:"
            if place == 3:
                medal = ":third_place_medal:"

            out += "> " + str(index + 1) + ". " + medal + " *" + player.name + \
                   "* (<@" + player.slack_id + ">) with *" + str(player.points) + "* point(s)\n"

        return True, out

    def list_scores(self):
        return sorted(self.high_scores.items(), key=lambda x: (-x[1], x[0]))

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
        return True, "you are now registered as *" + name + "*"

    def assign_with_weighted_random(self, argument):
        (task, msg) = self.validate_task(argument)
        if task is None:
            return False, msg

        if self.assignments.user_of_task(task.uid) is not None:
            return False, "a player is already assigned to this task."

        # Preparing the weighted list of players (weights are the inverse of the high scores)
        scores = self.players.scores()
        total = sum(player.points for player in scores)
        weighted_list = []
        for player in scores:
            if player.points is 0:
                weight = 150  # Skew the distribution to assign more tasks to players with 0 points
            else:
                weight = 100 - int(((float(player.points)) / total) * 100)

            weighted_list.append((weight, player))

        # Random pick
        player = self.weighted_random(weighted_list)

        return self.assign_and_update_score(player.slack_id, task,
                                            ":game_die: *The universe has spoken, "
                                            "congrats <@" + player.slack_id + ">!*\n")

    def assign_and_update_score(self, slack_id, task, additional_msg=""):
        assignee = self.assignments.user_of_task(task.uid)
        if assignee == slack_id:
            return False, "you are already assigned to this task."

        if self.assignments.assign(task.uid, slack_id) is False:
            return False, "a player is already assigned to this task."

        player = self.players.update_points(slack_id, task.points)
        message = self.ownership_message(player, task)
        return True, additional_msg + message

    def validate_task(self, argument):
        task_id = self.check_task_id(argument)
        if task_id is None:
            return None, "invalid task id"

        task = self.tasks.get(task_id)
        if task is None:
            return None, "this task does not exist."

        return task, ""

    @staticmethod
    def ownership_message(player, task):
        return "You are taking ownership of *" + task.description + "* for " + str(task.points) + \
               " point(s).\nYour new score is *" + str(player.points) + \
               "* point(s).\nIf you want to drop it, say: `!drop " + str(task.uid) + "`"

    @staticmethod
    def weighted_random(pairs):
        total = sum(pair[0] for pair in pairs)
        r = randint(1, total)
        for (weight, value) in pairs:
            r -= weight
            if r <= 0:
                return value

    @staticmethod
    def check_not_empty(argument):
        if len(argument) is 0:
            return False

        return True

    @staticmethod
    def check_task_id(argument):
        try:
            task_id = int(argument)
            return task_id
        except ValueError:
            return None

    @staticmethod
    def remove_trailing_quotes(description):
        if (description.startswith('"') and description.endswith('"')) or \
                (description.startswith('\'') and description.endswith('\'')):
            description = description[1:-1]

        return description

    @staticmethod
    def points_from(argument):
        try:
            points = int(argument.split(None, 1)[0])
            if points < 0 or points > MAX_TASK_POINTS:
                return None, "points must be between 1 and " + str(MAX_TASK_POINTS) + " included"
            else:
                return points, ""

        except ValueError:
            return None, "invalid format for points"

    @staticmethod
    def help():
        out = ":robot_face: *Commands*:\n"
        out += "> *!join*: To register your username as a player in da game, `!join &lt;user name&gt;`\n"
        out += "> *!leave*: To leave the game, `!leave`\n"
        out += "> *!score*: Will print the high scores, `!score` or `!scores`\n"
        out += "> *!tasks*: Will print the pending tasks, `!tasks`\n"
        out += "> *!add*: Will add a new task to the backlog to earn points, which can then be taken " \
               "by a player, `!add &lt;points&gt; &lt;description&gt;`\n"
        out += "> *!close*: This removes the task from the backlog, no effect on scores, `!close &lt;task id&gt;`\n"
        out += "> *!take*: You are taking this task, your score will increase, `!take &lt;task id&gt;`\n"
        out += "> *!drop*: You are dropping this task, your score will decrease, `!drop &lt;task id&gt;`\n"
        out += "> *!roulette*: The universe will assign this task to someone (weighted random)! " \
               "`!roulette &lt;task id&gt;`\n"
        out += "> *!help*: Prints the list of commands\n"
        out += "\n_ GamifyBot v0.2 - github.com/florentw/gamify-bot _\n"
        return out
