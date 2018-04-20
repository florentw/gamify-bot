#!/usr/bin/env python
# coding=utf-8

from builtins import object

import os.path
import yaml

DEFAULT_CONFIG_FILE = "bot-config.yml"


class Config(object):

    def __init__(self, config=DEFAULT_CONFIG_FILE, root_path=None):
        self.root_path = root_path

        with open(config, 'r') as stream:
            self.conf = yaml.load(stream)

        if self.conf is None or not isinstance(self.conf, dict):
            raise IOError("invalid YAML file format")

        self.validate_mandatory_fields()

    def validate_mandatory_fields(self):
        if self.db_file_name() is None:
            raise KeyError("missing config key: db.file_name")

        if self.max_task_points() is None:
            raise KeyError("missing config key: rules.max_task_points")

        db_file_name = self.db_file_name()
        if self.root_path is not None:
            db_file_name = os.path.join(self.root_path, db_file_name)

    def db_file_name(self):
        if 'db' in self.conf and \
                self.conf['db'] is not None and \
                "file_name" in self.conf['db']:
            return self.conf['db']['file_name']
        return None

    def admin_list(self):
        if 'admin' in self.conf and self.conf['admin'] is not None:
            return self.conf['admin']
        else:
            return []

    def max_task_points(self):
        if 'rules' in self.conf and \
                self.conf['rules'] is not None and \
                "max_task_points" in self.conf['rules']:
            return self.conf['rules']['max_task_points']
        return None
