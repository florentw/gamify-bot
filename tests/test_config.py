# coding=utf-8

import os
from unittest import TestCase

from game.config import Config


class TestConfig(TestCase):

    @staticmethod
    def config_from(config_file):
        root_path = os.path.join(os.path.dirname(__file__))
        path = os.path.join(os.path.dirname(__file__),
                            'resources',
                            config_file)
        return Config(path, root_path)

    def test_init_config_with_valid_file_does_not_throw_and_sets_values(self):
        config = self.config_from('valid-bot-conf.yml')

        self.assertIsNotNone(config)
        self.assertEquals(config.db_file_name(), "resources/valid.db")
        self.assertEquals(config.max_task_points(), 1337)
        self.assertEquals(len(config.admin_list()), 1)
        self.assertEquals(config.admin_list()[0], "SLACK_USER")

    def test_init_config_with_unknown_config_file_throws_IOError(self):
        with self.assertRaises(IOError) as context:
            self.config_from('unknown-bot-conf.yml')

        self.assertTrue('No such file or directory' in context.exception.strerror)

    def test_init_config_with_missing_db_file_throws_KeyError(self):
        with self.assertRaises(KeyError) as context:
            self.config_from('conf-missing-db.yml')

        self.assertTrue('missing config key: db.file_name' in context.exception.args[0])

    def test_init_config_with_missing_max_points_throws_KeyError(self):
        with self.assertRaises(KeyError) as context:
            self.config_from('conf-missing-rule.yml')

        self.assertTrue('missing config key: rules.max_task_points' in context.exception.args[0])

    def test_init_config_invalid_yml_throws_(self):
        with self.assertRaises(IOError) as context:
            self.config_from('conf-invalid-format.yml')

        self.assertTrue('invalid YAML file format' in context.exception.args[0])
