#!/usr/bin/env python

import os
import time

from slackclient import SlackClient

from game import Game

RTM_READ_DELAY = 0.8  # delay between readings from RTM


class MessagesHandler:
    def __init__(self, client):
        self.game = Game()
        self.slack_client = client

    #
    # def start(self):
    #     self.thread = threading.Thread(target=wizard.run)
    #     self.thread.daemon = True
    #     self.thread.start()

    def send(self, to, msg):
        self.slack_client.rtm_send_message(to, msg)

    def handle_bot_command(self, command, argument, channel, from_slack_id, msg):
        if command == "!join":
            (status, out) = self.game.join(from_slack_id, argument)
            self.send(channel, "<@" + from_slack_id + ">, " + out)
            return

        if command == "!leave":
            (status, out) = self.game.leave(from_slack_id)
            self.send(channel, "<@" + from_slack_id + ">, " + out)
            return

        if command == "!add":
            (status, out) = self.game.add_task(from_slack_id, argument)
            self.send(channel, "<@" + from_slack_id + ">, " + out)
            return

        if command == "!take":
            (status, out) = self.game.take_task(from_slack_id, argument)
            self.send(channel, "<@" + from_slack_id + ">, " + out)
            return

        if command == "!roulette":
            (status, out) = self.game.assign_with_weighted_random(argument)
            self.send(channel, out)
            return

        if command == "!drop":
            (status, out) = self.game.drop_task(from_slack_id, argument)
            self.send(channel, "<@" + from_slack_id + ">, " + out)
            return

        if command == "!close":
            (status, out) = self.game.close_task(from_slack_id, argument)
            self.send(channel, "<@" + from_slack_id + ">, " + out)
            return

        if command == "!tasks":
            (status, out) = self.game.list_tasks()
            self.send(channel, out)
            return

        if command == "!score" or command == "!scores":
            (status, out) = self.game.list_high_scores()
            self.send(channel, out)
            return

        if command == "!help":
            out = self.game.help()
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
        except Exception:
            import traceback
            print "Exception occurred while handling message: " + msg
            traceback.print_exc()


if __name__ == "__main__":

    # instantiate Slack client
    slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

    if slack_client.rtm_connect(with_team_state=False, parse="full"):
        print("GamifyBot connected and running!")

        handler = MessagesHandler(slack_client)
        while True:
            events = slack_client.rtm_read()

            for event in events:
                if "type" in event and event["type"] == "message" and \
                        "user" in event and "text" in event and "channel" in event:
                    handler.on_message(event["channel"], event["user"], event["text"])
                else:
                    print "Received event " + str(event)

            time.sleep(RTM_READ_DELAY)
    else:
        print "Connection to Slack failed."
