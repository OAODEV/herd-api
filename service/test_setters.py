import unittest
from unittest.mock import patch

from service.setters import set_iteration


class SettersTestCase(unittest.TestCase):
    """ Setters set fields on objects """

    def setUp(self):
        self.patchers = []
        get_cursor_patcher = patch('service.setters.get_cursor')
        self.patchers.append(get_cursor_patcher)
        self.mock_get_cur = get_cursor_patcher.start()

    def tearDown(self):
        del self.mock_get_cur
        for patcher in self.patchers:
            patcher.stop()

    def test_set_iteration(self):
        """ should set properties on iterations """
        # run SUT
        result = set_iteration(
            'mock-iteration-id',
            {"commit_hash": "new-commit-hash", "a": "b"},
        )

        # confirm reasonable sql was executed
        self.mock_get_cur.return_value.execute.assert_called_once_with(
            "UPDATE iteration " + \
            "SET a=%s,commit_hash=%s " + \
            "WHERE iteration_id=%s",
            ('b', 'new-commit-hash', 'mock-iteration-id'),
        )

    def test_can_pass(self):
        self.assertFalse(False)
