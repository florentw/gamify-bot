import sqlite3

class Player:
    def __init__(self, slack_id, name, points = 0):
        self.slack_id = slack_id
        self.name = name
        self.points = points

    def __str__(self):
        return self.name +"("+self.slack_id+"), "+str(self.points)+" point(s)"

class PlayerRepository:

    def __init__(self, con):
        self.con = con

        cursor = self.con.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS PLAYER (id TEXT PRIMARY KEY, name TEXT, points INTEGER)")
        self.con.commit()

    def get_by_id(self, slack_id):
        cursor = self.con.cursor()
        cursor.execute("SELECT * FROM PLAYER WHERE id=?", (slack_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return Player(row[0], row[1], row[2])

    def name_exists(self, name):
        cursor = self.con.cursor()
        cursor.execute("SELECT * FROM PLAYER WHERE name LIKE ?", (name,))
        row = cursor.fetchone()

        if row is None:
            return None

        return Player(row[0], row[1], row[2])

    def add(self, player):
        if self.get_by_id(player.slack_id) is not None:
            return False

        cursor = self.con.cursor()
        cursor.execute("INSERT INTO PLAYER(id, name, points) VALUES (?,?,?)", (player.slack_id, player.name, player.points))
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

        player.points = player.points + points_earned

        cursor = self.con.cursor()
        cursor.execute("UPDATE PLAYER SET points=? WHERE id=?", (player.points, slack_id))
        row = cursor.fetchone()
        return player

    def scores(self):
        cursor = self.con.cursor()
        cursor.execute("SELECT * FROM PLAYER ORDER BY points DESC")

        players = []
        while True:
            row = cursor.fetchone()
            if row == None:
                break

            players.append(Player(row[0], row[1], row[2]))

        return players

if __name__ == "__main__":
    con = sqlite3.connect(":memory:")
    players = PlayerRepository(con)
    print players.add(Player("U1","flo"))
    print players.add(Player("U2","necmi"))

    print players.get_by_id("U1")
    print players.get_by_id("0")

    print players.name_exists("flo")
    print players.name_exists("0")

    print players.add(Player("U1","flo"))
    print players.remove("U2")
    print players.get_by_id("U2")

    print players.update_points("U1", 10)
    print players.get_by_id("U1")
