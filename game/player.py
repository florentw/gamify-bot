#!/usr/bin/env python
# coding=utf-8
from __future__ import division
from builtins import str
from past.utils import old_div
from builtins import object
import re
from random import randint

MIN_USER_NAME_LEN = 2

MAX_USER_NAME_LEN = 32

VALID_NAME_REGEX = "^[a-zA-Z0-9]+([_-]?[a-zA-Z0-9])*$"


class Player(object):
    def __init__(self, player_id, name, points=0):
        self.player_id = player_id
        self.name = name
        self.points = points

    def __str__(self):
        return self.name + "(" + self.player_id + "), " + str(self.points) + " point(s)"

    def is_admin(self, admin_list):
        return self.player_id in admin_list


class PlayerRepository(object):
    """
    This class is responsible for the storage and querying of players.
    """

    def __init__(self, connection):
        self.con = connection

        cursor = self.con.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS PLAYER ("
                       "id TEXT PRIMARY KEY NOT NULL, "
                       "name TEXT NOT NULL UNIQUE, "
                       "points INTEGER NOT NULL)")
        self.con.commit()

    @staticmethod
    def player_from_row(row):
        player_id, name, points = row
        return Player(player_id, name, points)

    def get_by_id(self, player_id):
        cursor = self.con.cursor()
        cursor.execute("SELECT * FROM PLAYER WHERE id=?", (player_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return self.player_from_row(row)

    def name_exists(self, name):
        cursor = self.con.cursor()
        cursor.execute("SELECT * FROM PLAYER WHERE name LIKE ?", (name,))
        row = cursor.fetchone()

        if row is None:
            return None

        return self.player_from_row(row)

    def add(self, player):
        if self.get_by_id(player.player_id) is not None:
            return False

        cursor = self.con.cursor()
        cursor.execute("INSERT INTO PLAYER(id, name, points) VALUES (?,?,?)",
                       (player.player_id, player.name, player.points))
        self.con.commit()
        return True

    def remove(self, player_id):
        if self.get_by_id(player_id) is None:
            return False

        cursor = self.con.cursor()
        cursor.execute("DELETE FROM PLAYER WHERE id=?", (player_id,))
        self.con.commit()
        return True

    def reset_points(self, points, player_id=None):
        points = max(points, 0)
        if player_id is None:
            self.set_points_for_all(points)
            return True

        player = self.get_by_id(player_id)
        if player is None:
            return False

        self.set_points_for(player_id, points)
        return True

    def update_points(self, player_id, points_earned):
        player = self.get_by_id(player_id)
        if player is None:
            return None

        player.points = max(player.points + points_earned, 0)

        self.set_points_for(player_id, player.points)
        return player

    def set_points_for_all(self, points):
        cursor = self.con.cursor()
        cursor.execute("UPDATE PLAYER SET points=?", (points,))
        self.con.commit()

    def set_points_for(self, player_id, points):
        cursor = self.con.cursor()
        cursor.execute("UPDATE PLAYER SET points=? WHERE id=?", (points, player_id))
        self.con.commit()

    def scores(self):
        cursor = self.con.cursor()
        cursor.execute("SELECT * FROM PLAYER ORDER BY points DESC")

        high_scores = []
        while True:
            row = cursor.fetchone()
            if row is None:
                break

            high_scores.append(Player(row[0], row[1], row[2]))

        return high_scores

    def pick_random_user(self):
        # Preparing the weighted list of players (weights are the inverse of the high scores)
        scores = self.scores()
        total = sum(player.points for player in scores)
        weighted_list = []
        for player in scores:
            if player.points is 0:
                weight = 150  # Skew the distribution to assign more tasks to players with 0 points
            else:
                weight = 100 - int((old_div((float(player.points)), total)) * 100)

            weighted_list.append((weight, player))

        # Random pick
        return self.weighted_random(weighted_list)

    @staticmethod
    def weighted_random(pairs):
        total = sum(pair[0] for pair in pairs)
        r = randint(1, total)
        for (weight, value) in pairs:
            r -= weight
            if r <= 0:
                return value

    @staticmethod
    def validate_name_format(name):

        if len(name) < MIN_USER_NAME_LEN or len(name) > MAX_USER_NAME_LEN:
            return False

        valid_name_pattern = re.compile(VALID_NAME_REGEX)
        if valid_name_pattern.match(name) is not None:
            return True
        else:
            return False

    @staticmethod
    def invalid_name_message():

        return "User names can only contain alphanumeric and special characters: '_','-'." \
               "It always has to start with an alphanumeric character.\n" \
               "Special characters have to be followed by an alphanumeric character.\n" \
               "The last character has to be an alphanumeric character.\n" \
               "It must be between " + str(MIN_USER_NAME_LEN) + " and " + str(MAX_USER_NAME_LEN) + " characters long."
