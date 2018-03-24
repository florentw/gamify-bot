#!/usr/bin/env python

import os
import time

from slackclient import SlackClient

from game import Game

RTM_READ_DELAY = 1  # delay between readings from RTM
DATABASE_FILE_NAME = "gamifybot.db"


class MessagesHandler:

    def __init__(self, client):
        self.game = Game(DATABASE_FILE_NAME)
        self.commands = self.game.commands()
        self.slack_client = client

    def handle_bot_command(self, command, argument, channel, slack_id):
        # Here we pass the arguments from the current method to the registered function in the commands dict
        args = locals()
        del args["self"]
        del args["command"]
        del args["channel"]

        if command not in self.commands:
            return

        (command_func, desc) = self.commands[command]
        (status, out) = command_func(**args)
        self.slack_client.rtm_send_message(channel, out)

    def on_message(self, channel, from_slack_id, msg):
        try:
            split = msg.split(None, 1)
            command = split[0].lower()

            if len(split) == 2:
                argument = split[1]
            else:
                argument = ""

            self.handle_bot_command(command, argument, channel, from_slack_id)
        except Exception:
            import traceback
            print "Exception occurred while handling message: '" + msg + "'"
            traceback.print_exc()


def is_message(received_event):
    return "type" in received_event and received_event["type"] == "message"


def has_right_params(received_event):
    return "user" in received_event and "text" in received_event and "channel" in received_event


if __name__ == "__main__":

    # instantiate Slack client
    slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

    if slack_client.rtm_connect(with_team_state=False):
        print("GamifyBot connected and running!")

        handler = MessagesHandler(slack_client)
        while True:
            events = slack_client.rtm_read()

            for event in events:
                if is_message(event) and has_right_params(event):
                    handler.on_message(event["channel"], event["user"], event["text"])
                else:
                    print "Received event " + str(event)

            time.sleep(RTM_READ_DELAY)
    else:
        print "Connection to Slack failed."
