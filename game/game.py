#!/usr/bin/env python

import collections
import sqlite3

from assignment import AssignmentRepository
from player import PlayerRepository, Player
from task import Task, TaskRepository


class Game:
    """
    A bot that gamifies routine development tasks that are shared among team members.

    When a new routine task is entered, a team member can then assign it to him,
    and will earn an amount of points that was defined when adding it.
    """

    def __init__(self, sqlite_database):
        self.connection = sqlite3.connect(sqlite_database)
        self.players = PlayerRepository(self.connection)
        self.tasks = TaskRepository(self.connection)
        self.assignments = AssignmentRepository(self.connection)
        self.commands_dict = self.commands()

    def commands(self):
        """
        Each method listed in the below ordered dict must have the following arguments is that exact order:
        (self, slack_id, argument)

        :return: A dict of commands and their associated method and description.
        """

        c = collections.OrderedDict()
        c["!join"] = (self.join, "To register your username as a player in da game, `!join &lt;user name&gt;`")
        c["!leave"] = (self.leave, "To leave the game, `!leave`")
        c["!add"] = (self.add_task, "Will add a new task to the backlog to earn points, which can then be taken "
                                    "by a player, `!add &lt;points&gt; &lt;description&gt;`")
        c["!take"] = (self.take_task, "You are taking this task, your score will increase, `!take &lt;task id&gt;`")
        c["!roulette"] = (self.assign_with_weighted_random, "The universe will assign this task to someone "
                                                            "(weighted random)! `!roulette &lt;task id&gt;`")
        c["!drop"] = (self.drop_task, "You are dropping this task, your score will decrease, `!drop &lt;task id&gt;`")
        c["!close"] = (self.close_task, "This removes the task from the backlog, no effect on scores, "
                                        "`!close &lt;task id&gt;`")
        c["!score"] = (self.list_high_scores, "Will print the high scores, `!score` or `!scores`")
        c["!scores"] = c["!score"]
        c["!tasks"] = (self.list_tasks, "Will print the opened tasks, `!tasks`")
        c["!help"] = (self.help, "Prints the list of commands")
        return c

    def close(self):
        self.connection.close()

    def add_task(self, slack_id, argument):
        header = self.header(slack_id)

        player, msg = self.check_registered(slack_id)
        if player is None:
            return False, msg

        (points, msg) = self.players.points_from(argument)
        if points is None:
            return False, header + msg + ", usage: `!add &lt;points&gt; &lt;description&gt;`"

        if len(argument.split(None, 1)) == 2:
            description = self.remove_trailing_quotes(argument.split(None, 1)[1])
        else:
            return False, header + "invalid arguments: `!add &lt;points&gt; &lt;description&gt;`"

        task_id = self.tasks.insert(Task(description, points))
        return True, header + "new task *'" + description + "'*, added with id *" + str(task_id) + "* for *" + str(
            points) + "* point(s)!\nYou can take it by saying: `!take " + str(task_id) + "`"

    def take_task(self, slack_id, argument):
        header = self.header(slack_id)

        player, msg = self.check_registered(slack_id)
        if player is None:
            return False, msg

        (task, msg) = self.tasks.validate_task(argument)
        if task is None:
            return False, header + msg

        return self.assign_and_update_score(slack_id, task)

    def close_task(self, slack_id, argument):
        header = self.header(slack_id)

        player, msg = self.check_registered(slack_id)
        if player is None:
            return False, msg

        (task, msg) = self.tasks.validate_task(argument)
        if task is None:
            return False, msg

        self.assignments.remove(task.uid)
        self.tasks.remove(task.uid)
        return True, header + "the task *" + str(task.uid) + "*, *" + task.description + \
               "* has been closed by *" + player.name + "*."

    def drop_task(self, slack_id, argument):
        header = self.header(slack_id)

        player, msg = self.check_registered(slack_id)
        if player is None:
            return False, msg

        (task, msg) = self.tasks.validate_task(argument)
        if task is None:
            return False, msg

        assignee = self.assignments.user_of_task(task.uid)
        if assignee != player.slack_id:
            return False, header + "you are not assigned to this task."

        self.assignments.remove(task.uid)
        player = self.players.update_points(slack_id, -task.points)
        return True, header + "you are not assigned to this task anymore, " \
                              "your new score is *" + str(player.points) + "* point(s)."

    def list_tasks(self, slack_id=None, argument=None):
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

    def list_high_scores(self, slack_id=None, argument=None):
        scores = self.players.scores()

        if len(scores) is 0:
            return True, "No scores yet."

        out = ":checkered_flag: *High scores* (" + str(len(scores)) + " players):\n"
        place = 1
        previous_score = None
        for index, player in enumerate(scores):
            place, previous_score = self.place_for_score(place, player, previous_score)

            out += "> " + str(index + 1) + ". " + self.medal_from_place(place) + " *" + player.name + \
                   "* (<@" + player.slack_id + ">) with *" + str(player.points) + "* point(s)\n"

        return True, out

    @staticmethod
    def place_for_score(place, player, previous_score):
        if previous_score is None:
            previous_score = player.points
        elif player.points < previous_score:  # Do we have ex-aequo?
            previous_score = player.points
            place += 1
        return place, previous_score

    @staticmethod
    def medal_from_place(place):
        if place == 1:
            return ":first_place_medal:"
        if place == 2:
            return ":second_place_medal:"
        if place == 3:
            return ":third_place_medal:"

        return ":white_small_square:"

    def leave(self, slack_id, argument=None):
        header = self.header(slack_id)

        if self.players.get_by_id(slack_id) is None:
            return False, "you have to register first: `!join &lt;user name&gt;`"

        self.players.remove(slack_id)
        return True, header + "you are now unregistered."

    def join(self, slack_id, argument):
        header = self.header(slack_id)

        if self.check_not_empty(argument) is False:
            return False, header + "you have to provide a valid user name: `!join &lt;user name&gt;`"

        if self.players.get_by_id(slack_id) is not None:
            return False, header + "you are already registered"

        if self.players.name_exists(argument):
            return False, header + "someone is already registered with that name"

        self.players.add(Player(slack_id, argument))
        return True, header + "you are now registered as *" + argument + "*"

    def assign_with_weighted_random(self, slack_id, argument):
        player, msg = self.check_registered(slack_id)
        if player is None:
            return False, msg

        (task, msg) = self.tasks.validate_task(argument)
        if task is None:
            return False, msg

        if self.assignments.user_of_task(task.uid) is not None:
            return False, "a player is already assigned to this task."

        assignee = self.players.pick_random_user()

        return self.assign_and_update_score(assignee.slack_id, task,
                                            ":game_die: *The universe has spoken, "
                                            "congrats <@" + assignee.slack_id + ">!*\n")

    def help(self, slack_id=None, argument=None):
        out = ":robot_face: *Commands*:\n"

        for command, (function, description) in self.commands_dict.items():
            out += "> *" + command + "*: " + description + "\n"

        out += "\n_ GamifyBot v0.2 - github.com/florentw/gamify-bot _\n"
        return True, out

    def check_registered(self, slack_id):
        player = self.players.get_by_id(slack_id)

        if player is None:
            return None, self.header(slack_id) + "you have to register first: `!join &lt;user name&gt;`"

        return player, ""

    @staticmethod
    def header(slack_id):
        return "<@" + slack_id + ">, "

    def assign_and_update_score(self, slack_id, task, additional_msg=""):
        header = self.header(slack_id)

        assignee = self.assignments.user_of_task(task.uid)
        if assignee == slack_id:
            return False, header + "you are already assigned to this task."

        if self.assignments.assign(task.uid, slack_id) is False:
            return False, header + "a player is already assigned to this task."

        player = self.players.update_points(slack_id, task.points)
        message = self.ownership_message(player, task)
        return True, header + additional_msg + message

    @staticmethod
    def ownership_message(player, task):
        return "you are taking ownership of *" + task.description + "* for " + str(task.points) + \
               " point(s).\nYour new score is *" + str(player.points) + \
               "* point(s).\nIf you want to drop it, say: `!drop " + str(task.uid) + "`"

    @staticmethod
    def check_not_empty(argument):
        if len(argument) is 0:
            return False

        return True

    @staticmethod
    def remove_trailing_quotes(description):
        if (description.startswith('"') and description.endswith('"')) or \
                (description.startswith('\'') and description.endswith('\'')):
            description = description[1:-1]

        return description
