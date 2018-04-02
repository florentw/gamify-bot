#!/usr/bin/env python
# coding=utf-8

"""
GamifyBot main entry point, this file will run with python 2.7, and takes no arguments.
Please refer to the README.md for details.

This file contains a handler that forwards Slack events as commands for the game engine.
"""

__license__ = "MIT"
__author__ = "Florent Weber"
__maintainer__ = __author__
__email__ = "florent.weber@gmail.com"
__status__ = "Production"
__version__ = "0.3"

import os
import time

from slackclient import SlackClient

from game import Game, Config

ENV_BOT_TOKEN = 'SLACK_BOT_TOKEN'

RTM_READ_DELAY = 1  # delay between readings from RTM


class MessagesHandler:

    def __init__(self, client, provided_game=None):

        if provided_game is None:
            self.conf = Config()
            self.game = Game(self.conf)
        else:
            self.game = provided_game

        self.commands = self.game.commands()
        self.slack_client = client

    def handle_bot_command(self, command, argument, channel, player_id):
        """
        Forwards commands to the game engine using a commands dict for the mapping.

        :param command: The first word of the intercepted message.
        :param argument: A string containing the rest of the intercepted message.
        :param channel: Channel id from witch the message was received.
        :param player_id: Id of the player that emitted the message.
        :return: void
        """

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

    def on_message(self, channel, from_player_id, msg):
        """
        Parses a message, to validate its format and extract a command + arguments from it.

        :param channel: Channel id from witch the message was received.
        :param from_player_id: Id of the player that emitted the message.
        :param msg: Received message contents.
        :return: void
        """

        # noinspection PyBroadException
        try:
            split = msg.split(None, 1)
            if len(split) is 0:
                return

            command = split[0].lower()

            if len(split) == 2:
                argument = split[1]
            else:
                argument = ""

            self.handle_bot_command(command, argument, channel, from_player_id)
        except Exception:
            import traceback
            print("Exception occurred while handling message: '" + msg + "'")
            traceback.print_exc()


def is_message(received_event):
    return "type" in received_event and received_event["type"] == "message"


def has_right_params(received_event):
    return "user" in received_event and "text" in received_event and "channel" in received_event


if __name__ == "__main__":

    # instantiate Slack client
    bot_token = os.environ.get(ENV_BOT_TOKEN)
    if bot_token is None or bot_token.strip() == "":
        print("Please set the environment variable: " + ENV_BOT_TOKEN)
        exit(1)

    slack_client = SlackClient(bot_token)

    if not slack_client.rtm_connect(with_team_state=False):
        print("Connection to Slack failed.")
        exit(1)

    print("GamifyBot v" + __version__ + " connected and running!")

    handler = MessagesHandler(slack_client)
    while True:
        events = slack_client.rtm_read()

        for event in events:
            if is_message(event) and has_right_params(event):
                handler.on_message(event["channel"], event["user"], event["text"])

        time.sleep(RTM_READ_DELAY)
