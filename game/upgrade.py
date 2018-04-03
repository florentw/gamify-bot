#!/usr/bin/env python
# coding=utf-8

from game import __version__

NO_VERSION = "0.0"


class Upgrade:

    def __init__(self, connection, upgrade_procedures=None):
        self.con = connection
        self.create_table_if_not_exist()
        self.previous_version = NO_VERSION

        if upgrade_procedures is not None:
            self.upgrade_procedures = upgrade_procedures
        else:
            self.upgrade_procedures = [self.upgrade_from_0_to_1]

    # Put the upgrade methods in this section, there must be one method per upgrade from a major to another.
    def upgrade_from_0_to_1(self):
        print "upgrade_from_0_to_1"
        # AssignmentRepository.upgrade_from_0_to_1(self.con)

    def detect_initial_state(self, target_version=__version__):
        self.previous_version = self.select_or_insert_version(target_version)

    def create_table_if_not_exist(self):
        cursor = self.con.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS VERSION "
                       "(version TEXT NOT NULL UNIQUE)")
        self.con.commit()

    def select_or_insert_version(self, code_base_version):
        existing_db_version = self.fetch_data_model_version()
        if existing_db_version is not None:
            return existing_db_version

        cursor = self.con.cursor()
        cursor.execute("INSERT INTO VERSION(version) VALUES (?)",
                       (code_base_version,))
        self.con.commit()

        return NO_VERSION

    def fetch_data_model_version(self):

        cursor = self.con.cursor()
        cursor.execute("SELECT version FROM VERSION")
        row = cursor.fetchone()

        if row is None:
            return None

        return row[0]

    def perform_upgrade(self, target_version=__version__):

        major_from = self.major_from(self.previous_version)
        major_to = self.major_from(target_version)

        # No need to upgrade
        if major_from == major_to:
            return True, ""

        if major_from > major_to:
            return False, "Trying to downgrade the data model " \
                          "from " + self.previous_version + " to " + target_version + ", this is not supported."

        for next_major in xrange(major_to - major_from):
            self.upgrade_procedures[next_major]()

        cursor = self.con.cursor()
        cursor.execute("UPDATE VERSION SET version=?",
                       (target_version,))
        self.con.commit()

        return True, ""

    @staticmethod
    def major_from(version):
        return int(float(version))
