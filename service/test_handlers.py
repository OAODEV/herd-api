import unittest
from unittest.mock import patch

from handlers import (
    handle_branch_commit,
    handle_build,
)


class HandlersTestCase(unittest.TestCase):
    """ test the web handlers """

    def test_release_in_automatic_pipelines(self):
        """
        Ensure that all automatic pipelines for an iteration's branch is found
        and that a release is created for each of them. Ensure that a release
        is not created for non-automatic pipelines in the branch or for
        any pipeline in another branch

        """

        # set up
        # two branches
        # a built iteration in one of the branches
        # two automatic pipelines associated with the same branch
        # a non-automatic pipeline associated with the same branch
        # an automatic pipeline associated with the other branch

        # run SUT
        result = release_in_automatic_pipelines(123)

        # Confirm that:
        # both automatic pipelines in the same branch have releases
        # the non-automatic pipeline does not have a release
        # the autoatic pipeline for the other branch doesn't have a release

    def test_handle_branch_commit(self):
        """
        ensure that the branch handler generates all objects and
        and relationshapes that it should from scratch

        """

        # set up (mock all the idem make functions)
        make_service_patcher = patch(
            "handlers.idem_make_service",
            return_value="mock-service-id",
        )
        make_feature_patcher = patch(
            "handlers.idem_make_feature",
            return_value="mock-feature-id",
        )
        make_branch_patcher = patch(
            "handlers.idem_make_branch",
            return_value="mock-branch-id",
        )
        make_iteration_patcher = patch(
            "handlers.idem_make_iteration",
            return_value="mock-iteration-id",
        )
        mock_make_service = make_service_patcher.start()
        mock_make_feature = make_feature_patcher.start()
        mock_make_branch = make_branch_patcher.start()
        mock_make_iteration = make_iteration_patcher.start()

        # run SUT
        iteration_id = handle_branch_commit(
            'repo-x',
            'feature-x',
            'branch-x',
            'aabbccdd11-x'
        )

        # handler should have used idem_make_xyz functions to create everything
        mock_make_service.assert_called_with('repo-x')
        mock_make_feature.assert_called_with('feature-x', 'mock-service-id')
        mock_make_branch.assert_called_with('branch-x', 'mock-feature-id')
        mock_make_iteration.assert_called_with('aabbccdd11-x', 'mock-branch-id')

        # handler should have returned the iteration id
        self.assertEqual(iteration_id, {'iteration_id': 'mock-iteration-id'})

        # tear down
        patch.stopall()

    def test_handle_build(self):
        """ ensure that the build handler updates the iteration """
        # set up
        get_iteration_patcher = patch(
            'handlers.get_iteration',
            return_value = {'iteration_id': 'mock-iteration-id'},
        )
        set_iteration_patcher = patch(
            'handlers.set_iteration',
            return_value = {'iteration_id': 'mock-iteration-id'},
        )
        mock_get_iteration = get_iteration_patcher.start()
        mock_set_iteration = set_iteration_patcher.start()

        # run SUT
        result = handle_build('mock-commit-hash', 'mock-image-name')

        # confirm assumptions
        mock_get_iteration.assert_called_once_with(
            commit_hash="mock-commit-hash",
        )
        mock_set_iteration.assert_called_once_with(
            'mock-iteration-id',
            {'image_name': 'mock-image-name'}
        )

        # tear down
        mock_get_iteration.stop()
        mock_set_iteration.stop()

    def test_can_pass(self):
        self.assertTrue(True)
