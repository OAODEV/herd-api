import datetime
import unittest
from unittest.mock import patch

from service.getters import get_iteration

class GettersTestCase(unittest.TestCase):
    """ functions that get objects """

    def setUp(self):
        self.patchers = []
        get_cursor_patcher = patch('service.getters.get_cursor')
        self.patchers.append(get_cursor_patcher)
        self.mock_get_cur = get_cursor_patcher.start()

    def tearDown(self):
        del self.mock_get_cur
        for patcher in self.patchers:
            patcher.stop()

    def test_get_iteration_by_id(self):
        """ should return an iteration given an id """

        # set up
        now = datetime.datetime.now().ctime(),

        self.mock_get_cur.return_value.fetchone.return_value = (
            123,
            "mock-commit-uri",
            0,
            "abc123",
            "mock-image-name",
            "mock-image-uri",
            now,
        )

        # run SUT
        iteration = get_iteration(123)

        # confirm that the cursor executed reasonable sql
        self.mock_get_cur.return_value.execute.assert_called_once_with(
            "SELECT * FROM iteration WHERE iteration_id=123",
        )

        self.assertEqual(iteration, {
            "iteration_id": 123,
            "commit_uri": "mock-commit-uri",
            "branch_id": 0,
            "commit_hash": "abc123",
            "image_name": "mock-image-name",
            "image_uri": "mock-image-uri",
            "time_committed": now,
        })

    def test_get_iteration_by_commit_hash(self):
        """ shoule return an iteration when given a commit hash """
        # set up
        now = datetime.datetime.now().ctime(),

        self.mock_get_cur.return_value.fetchone.return_value = (
            123,
            "mock-commit-uri",
            0,
            "abc123",
            "mock-image-name",
            "mock-image-uri",
            now,
        )

        # run SUT
        iteration = get_iteration(commit_hash='abc123')

        # confirm that the cursor executed reasonable sql
        self.mock_get_cur.return_value.execute.assert_called_once_with(
            "SELECT * FROM iteration WHERE commit_hash=abc123",
        )

        # confirm that the iteration returned is correct
        self.assertEqual(iteration, {
            "iteration_id": 123,
            "commit_uri": "mock-commit-uri",
            "branch_id": 0,
            "commit_hash": "abc123",
            "image_name": "mock-image-name",
            "image_uri": "mock-image-uri",
            "time_committed": now,
        })


    def test_can_pass(self):
        self.assertTrue(True)
