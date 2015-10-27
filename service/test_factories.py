import datetime
import unittest
from unittest.mock import (
    patch,
    PropertyMock,
)

from getters import (
    get_config,
    get_env,
)
from factories import (
    idem_make_service,
    idem_make_feature,
    idem_make_branch,
    idem_make_iteration,
    new_deployment_pipeline,
    new_config,
    new_env,
)

class FactoryTestCase(unittest.TestCase):
    """ factories might create objects and relationships based on new info """

    def setUp(self):
        get_cursor_patcher = patch('factories.get_cursor')
        self.mock_get_cur = get_cursor_patcher.start()
        self.mock_rowcount = PropertyMock(return_value=0)
        type(self.mock_get_cur.return_value).rowcount = self.mock_rowcount

    def tearDown(self):
        del type(self.mock_get_cur.return_value).rowcount
        del self.mock_get_cur
        patch.stopall()

    def test_idem_make_service_new_case(self):
        """ Should make a service if it doesnt already exist """
        # set up
        mock_rowcount = PropertyMock(return_value=0)
        type(self.mock_get_cur.return_value).rowcount = mock_rowcount
        self.mock_get_cur.return_value.fetchone.return_value = (1,)

        # run SUT
        service_id = idem_make_service('mock-service-name')

        # confirm that reasonable sql was executed only once
        self.mock_get_cur.return_value.execute.assert_any_call(
            "INSERT INTO service (service_name) VALUES (%s) RETURNING service_id",
            ('mock-service-name',),
        )

        # confirm that we got an id back
        self.assertEqual(type(service_id), type(0))
        self.assertEqual(self.mock_get_cur.return_value.execute.call_count, 2)

        # make sure we closed the cursor
        self.mock_get_cur.return_value.close.assert_called_once_with()

    def test_idem_make_service_existing_case(self):
        """ Should return the existing id if it already exists """
        # set up
        mock_rowcount = PropertyMock(return_value=1)
        type(self.mock_get_cur.return_value).rowcount = mock_rowcount
        self.mock_get_cur.return_value.fetchone.return_value = (10,)

        # run SUT
        service_id = idem_make_service('mock-service-name')

        # confirm we only called execute once (to get existing)
        self.assertEqual(self.mock_get_cur.return_value.execute.call_count, 1)
        # and ended up with the corect id
        self.assertEqual(service_id, 10)

        # make sure we closed the cursor
        self.mock_get_cur.return_value.close.assert_called_once_with()

    def test_idem_make_feature_new_case(self):
        """ Should make a feature """
        # set up
        mock_rowcount = PropertyMock(return_value=0)
        type(self.mock_get_cur.return_value).rowcount = mock_rowcount
        self.mock_get_cur.return_value.fetchone.return_value = (1,)

        # run SUT
        feature_id_first = idem_make_feature('mock-feature-name', 1)

        # confirm that reasonable sql was executed only once
        self.mock_get_cur.return_value.execute.assert_any_call(
            "INSERT INTO feature (feature_name, service_id) " + \
            "VALUES (%s, %s) " + \
            "RETURNING feature_id",
            ('mock-feature-name', 1)
        )

        # confirm that we got back a good id
        self.assertEqual(type(feature_id_first), type(0))

        # make sure we closed the cursor
        self.mock_get_cur.return_value.close.assert_called_once_with()

    def test_idem_make_feature_existing_case(self):
        """ Should return the existing feature id """
        # set up
        mock_rowcount = PropertyMock(return_value=1)
        type(self.mock_get_cur.return_value).rowcount = mock_rowcount
        self.mock_get_cur.return_value.fetchone.return_value = (10,)

        # run SUT
        feature_id = idem_make_feature('mock-feature-name', 1)

        # confirm we only called execute once (to get existing)
        self.assertEqual(self.mock_get_cur.return_value.execute.call_count, 1)
        # and ended up with the corect id
        self.assertEqual(feature_id, 10)

        # make sure we closed the cursor
        self.mock_get_cur.return_value.close.assert_called_once_with()

    def test_idem_make_branch_new_case(self):
        """ Should make a branch with a pipeline if it doesn't already exist """
        # set up
        new_deployment_pipeline_patcher = patch(
            'factories.new_deployment_pipeline')
        mock_new_deployment_pipeline = new_deployment_pipeline_patcher.start()
        mock_rowcount = PropertyMock(return_value=0)
        type(self.mock_get_cur.return_value).rowcount = mock_rowcount
        self.mock_get_cur.return_value.fetchone.return_value = (199,)

        # run SUT
        branch_id = idem_make_branch('mock-branch-name', 1)

        # confirm that reasonable sql was executed
        self.mock_get_cur.return_value.execute.assert_any_call(
            "SELECT branch_id FROM branch WHERE branch_name=%s AND feature_id=%s",
            ('mock-branch-name', 1),
        )
        self.mock_get_cur.return_value.execute.assert_any_call(
            "INSERT INTO branch (branch_name, feature_id) " + \
            "VALUES (%s, %s) " + \
            "RETURNING branch_id",
            ('mock-branch-name', 1),
        )

        self.mock_get_cur.return_value.execute.assert_any_call(
            "INSERT INTO config (key_value_pairs) VALUES (%s) RETURNING config_id",
            ('',),
        )
        self.mock_get_cur.return_value.execute.assert_any_call(
            "INSERT INTO environment (settings) VALUES (%s) RETURNING environment_id",
            ('',),
        )
        self.mock_get_cur.return_value.execute.assert_any_call(
            "INSERT INTO deployment_pipeline " + \
            "(branch_id, config_id, environment_id) " \
            "VALUES (%s, %s, %s) " + \
            "RETURNING deployment_pipeline_id",
            (199, 199, 199),
        )

        # confirm that we got back a good id
        self.assertEqual(type(branch_id), type(0))

        # make sure we closed the cursor
        self.assertEqual(self.mock_get_cur.return_value.close.call_count, 4)

    def test_idem_make_branch_existing_case(self):
        """ Should return the existing iteration  id """
        # set up
        mock_rowcount = PropertyMock(return_value=1)
        type(self.mock_get_cur.return_value).rowcount = mock_rowcount
        self.mock_get_cur.return_value.fetchone.return_value = (10,)

        # run SUT
        branch_id = idem_make_branch('mock-branch-name', 1)

        # confirm we only called execute once (to get existing)
        self.assertEqual(self.mock_get_cur.return_value.execute.call_count, 1)
        # and ended up with the corect id
        self.assertEqual(branch_id, 10)

        # make sure we closed the cursor
        self.mock_get_cur.return_value.close.assert_called_once_with()

    def test_idem_make_iteration_new_case(self):
        """ Should make a iteration """
        # set up
        mock_rowcount = PropertyMock(return_value=0)
        type(self.mock_get_cur.return_value).rowcount = mock_rowcount
        self.mock_get_cur.return_value.fetchone.return_value = (1,)

        # run SUT
        iteration_id = idem_make_iteration('abc123', 3)

        # confirm that reasonable sql was executed only once
        self.mock_get_cur.return_value.execute.assert_any_call(
            # branch_id appears first because we need to stort the keys to get
            # the orderig to be consistant.
            "INSERT INTO iteration (branch_id, commit_hash) " + \
            "VALUES (%s, %s) " + \
            "RETURNING iteration_id",
            (3, 'abc123')
        )

        # confirm that we got back a good id
        self.assertEqual(type(iteration_id), type(0))

        # make sure we closed the cursor
        self.mock_get_cur.return_value.close.assert_called_once_with()

    def test_idem_make_iteration_existing_case(self):
        """ Should return the existing iteration id """
        # set up
        mock_rowcount = PropertyMock(return_value=1)
        type(self.mock_get_cur.return_value).rowcount = mock_rowcount
        self.mock_get_cur.return_value.fetchone.return_value = (10,)

        # run SUT
        iteration_id = idem_make_iteration(1, 'abc123')

        # confirm we only called execute once (to get existing)
        self.assertEqual(self.mock_get_cur.return_value.execute.call_count, 1)
        # and ended up with the corect id
        self.assertEqual(iteration_id, 10)

        # make sure we closed the cursor
        self.mock_get_cur.return_value.close.assert_called_once_with()

    def test_new_deployment_pipeline(self):
        """ Should make a new deployment pipeline """
        # set up
        new_config_patcher = patch(
            'factories.new_config',
            return_value=5,
        )
        mock_new_config = new_config_patcher.start()

        new_env_patcher = patch('factories.new_env', return_value=9)
        mock_new_env = new_env_patcher.start()

        # run SUT passing branch_id: 1, copy_config_id: 6, copy_env_id: None
        pipeline_id = new_deployment_pipeline(1, 6)

        # confirm that new config was based on config 6
        mock_new_config.assert_called_once_with(6)

        # confirm that new env was not based on anything
        mock_new_env.assert_called_once_with(None)

        # confirm reasonable sql was executed to make a pipeline
        self.mock_get_cur.return_value.execute.assert_called_once_with(
            "INSERT INTO deployment_pipeline " + \
            "(branch_id, config_id, environment_id) " + \
            "VALUES (%s, %s, %s) " + \
            "RETURNING deployment_pipeline_id",
            (1, 5, 9),
        )

        # make sure we closed the cursor
        self.mock_get_cur.return_value.close.assert_called_once_with()

    def test_new_empty_config(self):
        """ Should make a new empty config """
        # set up
        mock_rowcount = PropertyMock(return_value=0)
        type(self.mock_get_cur.return_value).rowcount = mock_rowcount
        self.mock_get_cur.return_value.fetchone.return_value = (1,)

        # run SUT
        new_config_id = new_config()

        # confirm appropriate sql was executed for an empty config
        self.mock_get_cur.return_value.execute.assert_called_once_with(
            "INSERT INTO config (key_value_pairs) VALUES (%s) RETURNING config_id",
            ('',),
        )

        # confirm we have a reasonable id
        self.assertEqual(type(new_config_id), type(0))

    def test_new_config_based_on_old_config(self):
        """ Should make a new config based on an old one """
        # set up
        get_config_patcher = patch(
            'factories.get_config',
            return_value = {
                'config_id': 101,
                'key_value_pairs': "mockKey=mockVal",
            }
        )
        mock_get_config = get_config_patcher.start()

        # run SUT
        new_config_id = new_config(101)

        # confirm correct sql was executed once
        self.mock_get_cur.return_value.execute.assert_called_once_with(
            "INSERT INTO config (key_value_pairs) VALUES (%s) RETURNING config_id",
            ('mockKey=mockVal',)
        )

        # confirm that we got config 101
        mock_get_config.assert_called_once_with(101)

    def test_new_empty_env(self):
        """ Should make a new environment """
        # set up
        mock_rowcount = PropertyMock(return_value=0)
        type(self.mock_get_cur.return_value).rowcount = mock_rowcount
        self.mock_get_cur.return_value.fetchone.return_value = (1,)

        # run SUT
        new_env_id = new_env()

        # confirm correct sql
        self.mock_get_cur.return_value.execute.assert_called_once_with(
            "INSERT INTO environment (settings) VALUES (%s) RETURNING environment_id",
            ('',),
        )

        # confirm that we got a reasonable id
        self.assertEqual(type(new_env_id), type(0))

    def test_new_env_based_on_old_env(self):
        """ Should make a new env based on an old one """
        # set up
        get_env_patcher = patch(
            'factories.get_env',
            return_value = {
                'environment_id': 101,
                'settings': "mockKey=mockVal",
            }
        )
        mock_get_env = get_env_patcher.start()

        # run SUT
        new_env_id = new_env(57)

        # confirm correct sql was executed once
        self.mock_get_cur.return_value.execute.assert_called_once_with(
            "INSERT INTO environment (settings) VALUES (%s) RETURNING environment_id",
            ('mockKey=mockVal',)
        )

        # confirm that we got environment 57
        mock_get_env.assert_called_once_with(57)

    def test_can_pass(self):
        self.assertTrue(True)
