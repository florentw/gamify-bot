import os
import time
import re
import threading

from slackclient import SlackClient

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
TASK_ASSIGNEMENT_PERIOD = 900 # Assignement period: after this timeout, tasks will be automatically assigned to someone

#########################################################

class Task:

    def __init__(self, description, points = 1):
        self.timestamp = time.time()
        self.description = description
        self.points = points

    def __str__(self):
        #insertion_time = time.strftime("%Y-%m-%d %H:%M:%S")
        return "Task '"+self.description+"' inserted at "+str(self.timestamp)

    def has_expired(self):
        # Expires after 15min
        return (time.time() - self.timestamp) > TASK_TIMEOUT

class TaskRepository:
    """
    This class is responsible for the storage and querying of tasks.
    """

    def __init__(self):
        self.uid = 1
        self.tasks = {} # UID -> Task

    def __str__(self):
        if len(self.tasks) == 0:
            return "No pending tasks."

        out = "Opened tasks:\n"
        for task_id, task in self.tasks.items():
            out += "-> "+str(task_id)+": "+str(task)+"\n"

        return out

    def get(self, uid):
        return self.tasks.get(uid)

    def insert(self, task):
        current_uid = self.uid
        print "Inserting a new task:'"+str(task)+"' "+str(current_uid)
        self.tasks[self.uid] = task
        self.uid += 1
        return current_uid

    def pending(self):
        return self.tasks

    def remove(self, uid):
        return self.tasks.pop(uid)

class AssignementRepository:
    """
    This class is reponsible for the storage and querying of assignements.
    """

    def __init__(self):
        self.assignements = {} # task_id -> user

    def __str__(self):
        if len(self.assignements) == 0:
            return "No assignements."

        out = "Current assignements:\n"
        for task_id, user in self.assignements.items():
            out += "-> "+str(task_id)+" is assigned to "+user+"\n"

        return out

    def assign(self, task_id, user):
        assigned_user = self.assignements.get(task_id)
        if assigned_user != None:
            return False

        self.assignements[task_id] = user
        return True

    def remove(self, task_id):
        self.assignements.pop(task_id)

    def user_of_task(self, task_id):
        return self.assignements.get(task_id)

    def list(self):
        return self.assignements

class GamifyBot:
    """
    A bot that gamifies routine development tasks that are shared among team members:
    - Analyze and answer support issues
    - Merge developments from one branch to another
    - Analyze CI failures, and fix them
    - Fixing Sonar issues
    - Etc.

    When a new routine task is entered, a team member can then assign it to him,
    and will earn an amount of points that is defined in the configuration file:
    -> task-types.yml
    """

    def __init__(self):
        self.high_scores = {}   # User -> Score
        self.tasks = TaskRepository()
        self.assignements = AssignementRepository()

    def insert(self, description):
        return self.tasks.insert(Task(description))

    def take_task(self, task_id, user):
        task = self.tasks.get(task_id)
        if task == None:
            return False, "This task does not exist."

        if self.assignements.assign(task_id, user) is False:
            return False, "A user is already assigned to this task."

        if self.high_scores.get(user) == None:
            self.high_scores[user] = task.points
        else:
            self.high_scores[user] += task.points

        return True, "You are taking ownership of *"+task.description+"* for "+str(task.points)+" points.\nYour new score is *"+str(self.high_scores[user])+"* points."

    def close_task(self, task_id, user):
        task = self.tasks.get(task_id)
        if task == None:
            return False, "This task does not exist."

        self.tasks.remove(task_id)
        return True, "The task *"+str(task_id)+"*, *"+task.description+"* has been closed by "+user+"."

    def drop_task(self, task_id, user):
        task = self.tasks.get(task_id)
        if task == None:
            return False, "This task does not exist."

        assignee = self.assignements.user_of_task(task_id)
        if assignee != user:
            return False, "You are not assigned to this task."

        self.assignements.remove(task_id)
        self.high_scores[user] -= task.points
        return True, "You are not assigned to this task anymore, your new score is *"+str(self.high_scores[user])+"* point(s)."

    def list_scores(self):
        return sorted(self.high_scores.items(), key=lambda x: (-x[1], x[0]))

    def list_tasks(self):
        return self.tasks.pending()

    def list_assignements(self):
        return self.assignements.list()

#########################################################

class User:
    def __init__(self, slack_id, name, ignored = False):
        self.slack_id = slack_id
        self.name = name
        self.ignored = ignored

    def __str__(self):
        return self.name if self.name else self.slack_id

class MessagesHandler:
    def __init__(self, slack_client, game):
        self.users = {}
        self.game = game
        self.slack_client = slack_client
    #
    # def start(self):
    #     self.thread = threading.Thread(target=wizard.run)
    #     self.thread.daemon = True
    #     self.thread.start()

    def send(self, to, msg):
        self.slack_client.rtm_send_message(to, msg)

    def player_by_id(self, slack_id):
        player = self.users.get(slack_id)
        if player != None and not player.ignored:
            return player
        else:
            return None

    def check_registered(self, slack_id, channel):
        player = self.users.get(slack_id)
        if player is None:
            self.send(channel, "<@"+slack_id+">, you are not registered, register using: `!join &lt;user name&gt;`")
            return None

        return player

    def check_not_empty(self, argument, message, channel):
        if len(argument) is 0:
            self.send(channel, message)
            return False

        return True

    def check_task_id(self, argument, slack_id, channel):
        task_id = None
        try:
            task_id = int(argument)
            return task_id
        except ValueError:
            self.send(channel, "<@"+slack_id+">, invalid task id.")
            return None

    def handle_bot_command(self, command, argument, channel, from_slack_id, msg):
        if command == "!join":
            if self.check_not_empty(argument, "<@"+from_slack_id+">, you have to provide a valid user name: `!join &lt;user name&gt;`", channel) is False:
                return

            if self.users.get(from_slack_id) is not None:
                self.send(channel, "<@"+from_slack_id+">, you are already registered.")
                return

            # TODO: Check that no one is already registered with the name argument

            self.users[from_slack_id] = User(from_slack_id, argument)
            self.send(channel, "<@"+from_slack_id+">, you are now registered as *"+argument+"*!")
            return

        if command == "!leave":
            if self.check_registered(from_slack_id, channel) is None:
                return

            self.users.pop(from_slack_id)
            self.send(channel, "<@"+from_slack_id+">, you are now unregistered.")
            return

        if command == "!add":
            player = self.check_registered(from_slack_id, channel)
            if player is None:
                return

            task_id = self.game.insert(argument)
            self.send(channel, "<@"+from_slack_id+">, new task *'"+argument+"'*, added with id *"+str(task_id)+"*!\nYou can take it by saying: `!take "+str(task_id)+"`")
            return

        if command == "!take":
            player = self.check_registered(from_slack_id, channel)
            if player is None:
                return

            task_id = self.check_task_id(argument, from_slack_id, channel)
            if task_id is None:
                return

            (status, message) = game.take_task(task_id, player.name)

            self.send(channel, "<@"+from_slack_id+">, "+message+"\nIf you want to drop it, say: `!drop "+str(task_id)+"`")
            return

        if command == "!drop":
            player = self.check_registered(from_slack_id, channel)
            if player is None:
                return

            task_id = self.check_task_id(argument, from_slack_id, channel)
            if task_id is None:
                return

            (status, message) = game.drop_task(int(argument), player.name)
            self.send(channel, "<@"+from_slack_id+">, "+message)
            return

        if command == "!close":
            player = self.check_registered(from_slack_id, channel)
            if player is None:
                return

            task_id = self.check_task_id(argument, from_slack_id, channel)
            if task_id is None:
                return

            (status, message) = game.close_task(int(argument), player.name)
            self.send(channel, "<@"+from_slack_id+">, "+message)

        if command == "!tasks":
            pending = self.game.list_tasks()
            assignements = self.game.list_assignements()

            if len(pending) is 0:
                self.send(channel, "No pending task.")
                return

            out = "*Pending tasks* ("+str(len(pending))+"):\n"
            for task_id, task in pending.items():
                assigned = "*Not* assigned"
                if task_id in assignements:
                    assigned = "Assigned to *"+assignements[task_id]+"*"

                out += "> [*"+str(task_id)+"*] *"+task.description+"* for "+str(task.points)+" point(s): "+assigned+".\n"

            self.send(channel, out)
            return

        if command == "!score" or command == "!scores":
            scores = self.game.list_scores()

            if len(scores) is 0:
                self.send(channel, "No scores yet.")
                return

            out = "*High scores* ("+str(len(scores))+" players):\n"
            place = 1
            for player,score in scores:
                out += "> "+str(place)+". *<@"+player+">* with *"+str(score)+"* point(s)\n"
                place += 1

            self.send(channel, out)
            return

        if command == "!help":
            out = "*Commands*:\n"
            out += "> *!join*: To register your username as a player in da game, `!join &lt;user name&gt;`\n"
            out += "> *!leave*: To leave the game, `!leave`\n"
            out += "> *!score*: Will print the high scores, `!score` or `!scores`\n"
            out += "> *!tasks*: Will print the pending tasks, `!tasks`\n"
            out += "> *!add*: Will add a new task to the backlog, which can then be taken by a player, `!add &lt;task description&gt;`\n"
            out += "> *!close*: This removes the task from the backlog, no effect on scores, `!close &lt;task id&gt;`\n"
            out += "> *!take*: You are taking this task, your score will increase, `!take &lt;task id&gt;`\n"
            out += "> *!drop*: You are dropping this task, your score will decrease, `!drop &lt;task id&gt;`\n"
            out += "> *!help*: Prints the list of commands\n"
            self.send(channel, out)
            return

    def on_message(self, channel, from_slack_id, msg):
        try:
            command = msg.split(None, 1)[0].lower()

            if len(msg.split(None, 1)) == 2:
                argument = msg.split(None, 1)[1]
            else:
                argument = ""

            self.handle_bot_command(command, argument, channel, from_slack_id, msg)
        except Exception as e:
            print "Exception occured while handling message: "+msg
            print e

if __name__ == "__main__":

    # instantiate Slack client
    slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

    game = GamifyBot()

    if slack_client.rtm_connect(with_team_state=False, parse="full"):
        print("Gamify Bot connected and running!")

        handler = MessagesHandler(slack_client, game)
        while True:
            events = slack_client.rtm_read()

            for event in events:
                if "type" in event and event["type"] == "message":
                    handler.on_message(event["channel"], event["user"], event["text"])
                else:
                    print "Received event "+str(event)

            time.sleep(RTM_READ_DELAY)
    else:
        print "Connection to Slack failed."
