import time
import sqlite3

TASK_ASSIGNEMENT_PERIOD = 900 # Assignement period: after this timeout, tasks will be automatically assigned to someone

class Task:

    def __init__(self, description, points = 1, timestamp = None, uid = None):
        if timestamp is None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp

        self.description = description
        self.points = points
        self.uid = uid

    def __str__(self):
        #insertion_time = time.strftime("%Y-%m-%d %H:%M:%S")
        return "Task["+str(self.uid)+"] '"+self.description+"' inserted at "+str(self.timestamp)

    def has_expired(self):
        # Expires after 15min
        return (time.time() - self.timestamp) > TASK_TIMEOUT

class TaskRepository:
    """
    This class is responsible for the storage and querying of tasks.
    """

    def __init__(self, con):
        self.con = con

        cursor = self.con.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS TASK (id INTEGER PRIMARY KEY ASC, inserted TEXT, points INTEGER, description TEXT)")
        self.con.commit()

    def __str__(self):
        pending = self.pending()
        if len(pending) == 0:
            return "No pending tasks."

        out = "Opened tasks:\n"
        for task in pending:
            out += "-> "+str(task.uid)+": "+str(task)+"\n"

        return out

    def get(self, uid):
        cursor = self.con.cursor()
        cursor.execute("SELECT * FROM TASK WHERE id=?", (uid,))
        row = cursor.fetchone()

        if row is None:
            return None

        return Task(row[3], row[2], row[1], row[0])

    def insert(self, task):
        cursor = self.con.cursor()
        cursor.execute("INSERT INTO TASK(inserted, points, description) VALUES (?,?,?)", (str(task.timestamp), task.points, task.description))
        task_id = cursor.lastrowid
        self.con.commit()
        return task_id

    def pending(self):
        cursor = self.con.cursor()
        cursor.execute("SELECT * FROM TASK")

        tasks = []
        while True:
            row = cursor.fetchone()
            if row == None:
                break

            tasks.append(Task(row[3], row[2], row[1], row[0]))

        return tasks

    def remove(self, uid):
        cursor = self.con.cursor()
        cursor.execute("DELETE FROM TASK WHERE id=?", (uid,))
        self.con.commit()

if __name__ == "__main__":
    con = sqlite3.connect(":memory:")
    tasks = TaskRepository(con)

    tasks.insert(Task("Hello world"))
    tasks.insert(Task("Bouh"))
    print tasks.get(1)
    print tasks.get(0)
    print tasks.get(2)
    for t in tasks.pending():
        print "-> "+str(t)

    tasks.remove(1)

    for t in tasks.pending():
        print "-> "+str(t)

    tasks.remove(0)

    con.close()
