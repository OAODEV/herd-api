import unittest
from unittest.mock import patch

from setters import (
    set_iteration,
    release_in_automatic_pipelines,
)


class SettersTestCase(unittest.TestCase):
    """ Setters set fields on objects (in the database) """

    def setUp(self):
        self.patchers = []
        get_cursor_patcher = patch('setters.get_cursor')
        self.patchers.append(get_cursor_patcher)
        self.mock_get_cur = get_cursor_patcher.start()

    def tearDown(self):
        del self.mock_get_cur
        for patcher in self.patchers:
            patcher.stop()

    def test_release_automatic_pipelines(self):
        """
        When an image is built, it's released in relevant automatic pipelines

        When an iteration's image is built, herd-service releases that image in
        all of that iteration's branch's automatic pipelines.

        branch -> iteration ----------> release
          |-----> deployment pipeline <----|

        """

        # run SUT
        result = release_in_automatic_pipelines(123)

        # confirm that the insert sql was executed once
        # SQL can do this whole operation so we should have it handle it.
        self.mock_get_cur.return_value.execute.asert_called_once_with(
            "INSERT INTO release (iteration_id, deployment_pipeline_id)\n" + \
            "SELECT iteration_id, deployment_pipeline_id\n" + \
            "  FROM iteration\n" + \
            "  JOIN branch USING (branch_id)\n" + \
            "  JOIN deployment_pipeline USING (branch_id)\n" + \
            "where iteration_id = %s",
            (123,),
        )

        # confirm we closed the cursor
        self.mock_get_cur.return_value.close.assert_called_once_with()

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
