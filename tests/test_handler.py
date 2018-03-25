# coding=utf-8

from unittest import TestCase

from game.game import Game
from gamifybot import MessagesHandler


class SlackClientMock:

    def __init__(self):
        self.invokes = []

    def rtm_send_message(self, channel, out):
        self.invokes.append((channel, out))


def rtm_send_message_failure(channel, out):
    raise ValueError("Provoked error")


class TestMessagesHandler(TestCase):

    def setUp(self):
        self.game = Game(None, ":memory:")
        self.client = SlackClientMock()
        self.msg_handler = MessagesHandler(self.client, self.game)

    def tearDown(self):
        self.game.close()

    def test_init_populates_command_list(self):
        self.assertEquals(len(self.msg_handler.commands), 12)

    def test_on_message_with_single_command(self):
        self.msg_handler.on_message("channel", "U1", "!tasks")

        self.assertEquals(len(self.client.invokes), 1)
        self.assertEquals(self.client.invokes[0], ('channel', 'No pending task.'))

    def test_on_message_with_no_command(self):
        self.msg_handler.on_message("channel", "U1", "")

        self.assertEquals(len(self.client.invokes), 0)

    def test_on_message_with_argument(self):
        self.msg_handler.on_message("channel", "U1", "!add 1 Hello task")

        self.assertEquals(len(self.client.invokes), 1)
        self.assertEquals(self.client.invokes[0],
                          ('channel', '<@U1>, you have to register first: `!join &lt;user name&gt;`'))

    def test_on_message_with_unknown_command(self):
        self.msg_handler.on_message("channel", "U1", "!unknown")

        self.assertEquals(len(self.client.invokes), 0)

    def test_on_message_with_game_failure(self):
        self.client.rtm_send_message = rtm_send_message_failure
        self.msg_handler.on_message("channel", "U1", "!help")

        self.assertEquals(len(self.client.invokes), 0)
