#!/usr/bin/env python
# coding=utf-8

"""
Main logic and game rules:
- User handling logic
- Tasks and assignments implementation
"""
from __future__ import absolute_import

__license__ = "MIT"
__author__ = "Florent Weber"
__maintainer__ = __author__
__email__ = "florent.weber@gmail.com"
__status__ = "Production"
__version__ = "${GAMIFY_BOT_VERSION}"

from builtins import object
from builtins import str

import collections
import sqlite3

from .assignment import AssignmentRepository
from .player import PlayerRepository, Player
from .task import Task, TaskRepository
from .upgrade import Upgrade


class Game(object):
    """
    A bot that gamifies routine development tasks that are shared among team members.

    When a new routine task is entered, a team member can then assign it to him,
    and will earn an amount of points that was defined when adding it.
    """

    def __init__(self, config, sqlite_con=None):
        if sqlite_con is not None:
            self.connection = sqlite_con
        else:
            self.connection = sqlite3.connect(config.db_file_name())

        self.perform_upgrade()

        self.config = config
        self.players = PlayerRepository(self.connection)
        self.tasks = TaskRepository(self.connection)
        self.assignments = AssignmentRepository(self.connection)
        self.commands_dict = self.commands()

    def perform_upgrade(self):
        upgrade = Upgrade(self.connection)
        upgrade.detect_initial_state()
        (status, msg) = upgrade.perform_upgrade()
        if status is False:
            raise ValueError("Error while performing data model upgrade: " + msg)

    def commands(self):
        """
        Each method listed in the below ordered dict must have the following arguments is that exact order:
        (self, player_id, argument)

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
        c["!admin:reset"] = (self.reset_all_scores, "Will reset all scores to 0! Can only be performed by an admin, "
                                                    "`!admin:reset`")
        c["!help"] = (self.help, "Prints the list of commands")
        return c

    def close(self):
        self.connection.close()

    def join(self, player_id, argument):
        """
        Inserts a new player.

        :param player_id: Unique id of the caller that will be registered.
        :param argument: Desired user name for the player.
        :return: A tuple, (success:boolean, msg:string)
        """

        header = self.header(player_id)

        if self.check_not_empty(argument) is False:
            return False, header + "you have to provide a user name: `!join &lt;user name&gt;`"

        if self.players.validate_name_format(argument) is False:
            return False, header + self.players.invalid_name_message()

        if self.players.get_by_id(player_id) is not None:
            return False, header + "you are already registered"

        if self.players.name_exists(argument):
            return False, header + "someone is already registered with that name"

        self.players.add(Player(player_id, argument))
        return True, header + "you are now registered as *" + argument + "*"

    def leave(self, player_id, argument=None):
        """
        Deletes a player and its assignments.

        :param player_id: Unique id of the caller that will be unregistered.
        :param argument: Ignored: Necessary to be able to use a dict of commands.
        :return: A tuple, (success:boolean, msg:string)
        """

        header = self.header(player_id)

        if self.players.get_by_id(player_id) is None:
            return False, "you have to register first: `!join &lt;user name&gt;`"

        self.players.remove(player_id)

        for task_id, assignee_id in list(self.assignments.list().items()):
            if assignee_id == player_id:
                self.assignments.remove(task_id)

        return True, header + "you are now unregistered."

    def add_task(self, player_id, argument):
        """
        Inserts a new task in the backlog.

        :param player_id: Unique id of the player inserting a new task in the backlog.
        :param argument: String containing parameters (points, description).
        :return: A tuple, (success:boolean, msg:string)
        """

        header = self.header(player_id)

        player, msg = self.check_registered(player_id)
        if player is None:
            return False, msg

        max_task_points = None
        if self.config is not None:
            max_task_points = self.config.max_task_points()

        (points, msg) = self.tasks.points_from(argument, max_task_points)
        if points is None:
            return False, header + msg + ", usage: `!add &lt;points&gt; &lt;description&gt;`"

        if len(argument.split(None, 1)) == 2:
            description = self.tasks.remove_trailing_quotes(argument.split(None, 1)[1])
        else:
            return False, header + "invalid arguments: `!add &lt;points&gt; &lt;description&gt;`"

        task_id = self.tasks.insert(Task(description, points))
        return True, header + "new task *'" + description + "'*, added with id *" + str(task_id) + "* for *" + str(
            points) + "* point(s)!\nYou can take it by saying: `!take " + str(task_id) + "`"

    def take_task(self, player_id, argument):
        """
        Assigns a task to the caller, and increase its score.

        :param player_id: Unique id of the caller.
        :param argument: The task id.
        :return: A tuple, (success:boolean, msg:string)
        """

        header = self.header(player_id)

        player, msg = self.check_registered(player_id)
        if player is None:
            return False, msg

        (task, msg) = self.tasks.validate_task(argument)
        if task is None:
            return False, header + msg

        return self.assign_and_update_score(player_id, task)

    def drop_task(self, player_id, argument):
        """
        Un-assigns a task owned by the caller.
        If the caller is admin, he can invoke this command for task he does not own.

        :param player_id: Unique id of the caller.
        :param argument: The task id.
        :return: A tuple, (success:boolean, msg:string)
        """

        header = self.header(player_id)

        player, msg = self.check_registered(player_id)
        if player is None:
            return False, msg

        (task, msg) = self.tasks.validate_task(argument)
        if task is None:
            return False, msg

        cause = ""
        assignee_id = self.assignments.user_of_task(task.uid)
        if assignee_id is None:
            return False, header + "no one is assigned to this task."

        header = self.header(assignee_id)
        if not player.is_admin(self.config.admin_list()):
            if assignee_id != player.player_id:
                return False, self.header(player.player_id) + "you are not assigned to this task."
        else:
            cause = "\nAdmin player <@" + player_id + "> cancelled your assignment."

        self.assignments.remove(task.uid)
        player = self.players.update_points(player_id, -task.points)
        return True, header + "you are not assigned to this task anymore, " \
                              "your new score is *" + str(player.points) + "* point(s)." + cause

    def assign_with_weighted_random(self, player_id, argument):
        """
        Randomly chose player and assigns the given task to him.
        A weighted random algorithm is used to increase the probability to pick a player with a low score.

        :param player_id: Unique id of the caller.
        :param argument: The task id to be randomly assigned.
        :return: A tuple, (success:boolean, msg:string)
        """

        player, msg = self.check_registered(player_id)
        if player is None:
            return False, msg

        (task, msg) = self.tasks.validate_task(argument)
        if task is None:
            return False, msg

        if self.assignments.user_of_task(task.uid) is not None:
            return False, "a player is already assigned to this task."

        assignee = self.players.pick_random_user()

        return self.assign_and_update_score(assignee.player_id, task,
                                            ":game_die: *The universe has spoken, "
                                            "congrats <@" + assignee.player_id + ">!*\n")

    def close_task(self, player_id, argument):
        """
        Removes a task from the backlog, scores are not updated.

        :param player_id: Unique id of the caller.
        :param argument: The task id.
        :return: A tuple, (success:boolean, msg:string)
        """

        header = self.header(player_id)

        player, msg = self.check_registered(player_id)
        if player is None:
            return False, msg

        (task, msg) = self.tasks.validate_task(argument)
        if task is None:
            return False, msg

        self.assignments.remove(task.uid)
        self.tasks.remove(task.uid)
        # @formatter:off
        return True, header + "the task *" + str(task.uid) + "*, *" + task.description + \
                              "* has been closed by *" + player.name + "*."
        # @formatter:on

    def list_tasks(self, player_id=None, argument=None):
        """
        Lists all tasks and assignments.

        :param player_id: Ignored: Necessary to be able to use a dict of commands.
        :param argument: Ignored: Necessary to be able to use a dict of commands.
        :return: A tuple, (success:boolean, msg:string)
        """

        pending = self.tasks.pending()
        assignments = self.assignments.list()

        if len(pending) is 0:
            return True, "No pending task."

        out = ":pushpin: *" + str(len(pending)) + " pending tasks*:\n"
        for task in pending:
            icon = ":white_square:"
            assigned = "`!take " + str(task.uid) + "`"

            player_id = assignments.get(task.uid)
            if player_id is not None:
                assigned = ":point_right: *" + self.players.get_by_id(player_id).name + "*"
                icon = ":heavy_check_mark:"

            out += "> " + icon + " [*" + str(task.uid) + "*] *" + task.description + "* [*" + str(
                task.points) + "* points] " + assigned + "\n"

        return True, out

    def list_high_scores(self, player_id=None, argument=None):
        """
        Lists all scores.

        :param player_id: Ignored: Necessary to be able to use a dict of commands.
        :param argument: Ignored: Necessary to be able to use a dict of commands.
        :return: A tuple, (success:boolean, msg:string)
        """

        scores = self.players.scores()

        if len(scores) is 0:
            return True, "No scores yet."

        out = ":checkered_flag: *High scores* (" + str(len(scores)) + " players):\n"
        place = 1
        previous_score = None
        for index, player in enumerate(scores):
            place, previous_score = self.place_for_score(place, player, previous_score)

            out += "> " + str(index + 1) + ". " + self.medal_from_place(place) + " *" + player.name + \
                   "* (<@" + player.player_id + ">) with *" + str(player.points) + "* point(s)\n"

        return True, out

    def reset_all_scores(self, player_id, argument=None):
        """
        Reset the scores of everyone to 0. player_id must be an admin to do that.

        :param player_id: Unique id of the caller.
        :param argument: Ignored: Necessary to be able to use a dict of commands.
        :return: A tuple, (success:boolean, msg:string)
        """

        header = self.header(player_id)

        player, msg = self.check_registered(player_id)
        if player is None:
            return False, msg

        if not player.is_admin(self.config.admin_list()):
            return False, header + "this action can only be performed by an admin."

        # Reset all scores to 0
        self.players.reset_points(0)
        return "True", header + " you successfully reset all player scores to 0, hope you meant to do that ¯\_(ツ)_/¯"

    def help(self, player_id=None, argument=None):
        """
        Displays the list of commands.

        :param player_id: Ignored: Necessary to be able to use a dict of commands.
        :param argument: Ignored: Necessary to be able to use a dict of commands.
        :return: A tuple, (success:boolean, msg:string)
        """

        out = ":robot_face: *Commands*:\n"

        for command, (function, description) in list(self.commands_dict.items()):
            out += "> *" + command + "*: " + description + "\n"

        out += "\n_ GamifyBot v%s - github.com/florentw/gamify-bot _\n" % __version__
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

    def check_registered(self, player_id):
        player = self.players.get_by_id(player_id)

        if player is None:
            return None, self.header(player_id) + "you have to register first: `!join &lt;user name&gt;`"

        return player, ""

    @staticmethod
    def header(player_id):
        return "<@" + player_id + ">, "

    def assign_and_update_score(self, player_id, task, additional_msg=""):
        header = self.header(player_id)

        assignee = self.assignments.user_of_task(task.uid)
        if assignee == player_id:
            return False, header + "you are already assigned to this task."

        if self.assignments.assign(task.uid, player_id) is False:
            return False, header + "a player is already assigned to this task."

        player = self.players.update_points(player_id, task.points)
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
