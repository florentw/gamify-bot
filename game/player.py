#!/usr/bin/env python


class Player:
    def __init__(self, slack_id, name, points=0):
        self.slack_id = slack_id
        self.name = name
        self.points = points

    def __str__(self):
        return self.name + "(" + self.slack_id + "), " + str(self.points) + " point(s)"


class PlayerRepository:
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
        slack_id, name, points = row
        return Player(slack_id, name, points)

    def get_by_id(self, slack_id):
        cursor = self.con.cursor()
        cursor.execute("SELECT * FROM PLAYER WHERE id=?", (slack_id,))
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
        if self.get_by_id(player.slack_id) is not None:
            return False

        cursor = self.con.cursor()
        cursor.execute("INSERT INTO PLAYER(id, name, points) VALUES (?,?,?)",
                       (player.slack_id, player.name, player.points))
        self.con.commit()
        return True

    def remove(self, slack_id):
        if self.get_by_id(slack_id) is None:
            return False

        cursor = self.con.cursor()
        cursor.execute("DELETE FROM PLAYER WHERE id=?", (slack_id,))
        self.con.commit()
        return True

    def update_points(self, slack_id, points_earned):
        player = self.get_by_id(slack_id)
        if player is None:
            return None

        player.points = max(player.points + points_earned, 0)

        cursor = self.con.cursor()
        cursor.execute("UPDATE PLAYER SET points=? WHERE id=?", (player.points, slack_id))
        self.con.commit()
        return player

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
