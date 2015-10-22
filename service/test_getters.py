import datetime
import unittest
from unittest.mock import patch

from service.getters import (
    get_iteration,
    make_getter,
    get_config,
    get_env,
)

class GettersTestCase(unittest.TestCase):
    """ functions that get objects """

    def setUp(self):
        get_cursor_patcher = patch('service.getters.get_cursor')
        self.mock_get_cur = get_cursor_patcher.start()

    def tearDown(self):
        del self.mock_get_cur
        patch.stopall()

    def test_get_iteration_by_id(self):
        """ should return an iteration given an id """

        # set up
        now = datetime.datetime.now().ctime(),
        self.mock_get_cur.return_value.description.return_value = (
            "iteration_id",
        )
        self.mock_get_cur.return_value.fetchone.return_value = (122,)

        # run SUT
        iteration = get_iteration(122)

        # confirm that the cursor executed reasonable sql
        self.mock_get_cur.return_value.execute.assert_called_once_with(
            "SELECT * FROM iteration WHERE iteration_id=%s",
            (122),
        )

        self.assertEqual(iteration, {"iteration_id": 122})

        # confirm we closed the cursor
        self.mock_get_cur.return_value.close.assert_called_once_with()

    def test_get_iteration_by_commit_hash(self):
        """ shoule return an iteration when given a commit hash """
        # set up
        now = datetime.datetime.now().ctime(),
        self.mock_get_cur.return_value.description.return_value = (
            "iteration_id",
        )
        self.mock_get_cur.return_value.fetchone.return_value = (123,)

        # run SUT
        iteration = get_iteration(commit_hash='abc123')

        # confirm that the cursor executed reasonable sql
        self.mock_get_cur.return_value.execute.assert_called_once_with(
            "SELECT * FROM iteration WHERE commit_hash=%s",
            ('abc123'),
        )

        # confirm that the iteration returned is correct
        self.assertEqual(iteration, {"iteration_id": 123})


        # confirm we closed the cursor
        self.mock_get_cur.return_value.close.assert_called_once_with()

    def test_get_config(self):
        """ Should return a config given an id """
        # set up
        self.mock_get_cur.return_value.description.return_value = (
            'config_id',
            'config_name',
            'key_value_pairs',
        )
        self.mock_get_cur.return_value.fetchone.return_value = (
            1,
            'mock-config-name',
            'a=b\nc=d',
        )

        # run SUT
        test_config = get_config(1)

        # confirm we selected the given config
        self.mock_get_cur.return_value.execute.assert_called_once_with(
            "SELECT * FROM config WHERE config_id=%s",
            1,
        )

        # confirm the return is correct
        self.assertEqual(test_config, {
                "config_id": 1,
                "config_name": "mock-config-name",
                "key_value_pairs": "a=b\nc=d",
            })

        # confirm we closed the cursor
        self.mock_get_cur.return_value.close.assert_called_once_with()

    def test_get_env(self):
        """ Should return an environment given and id """
        # set up
        self.mock_get_cur.return_value.description.return_value = (
            "environment_id",
            "environment_name",
            "settings",
        )
        self.mock_get_cur.return_value.fetchone.return_value = (
            2,
            'mock-env-name',
            'setting=something\nwhatever=foobar',
        )

        # run SUT
        test_env = get_env(2)

        # confirm we selected the given environment
        self.mock_get_cur.return_value.execute.assert_called_once_with(
            "SELECT * FROM environment WHERE environment_id=%s",
            2,
        )

        # confirm the return is correct
        self.assertEqual(test_env, {
                "environment_id": 2,
                "environment_name": "mock-env-name",
                "settings": 'setting=something\nwhatever=foobar',
            })

        # confirm we closed the cursor
        self.mock_get_cur.return_value.close.assert_called_once_with()

    def test_make_getter(self):
        """ Should make a well behaving getter """
        # set up
        self.mock_get_cur.return_value.fetchone.return_value = (
            0,
            1,
            2,
        )
        self.mock_get_cur.return_value.description.return_value = (
            "zero",
            "one",
            "two",
        )

        # run SUT
        getter = make_getter("mock_table", "mock_key", "(mock, values)")
        result = getter("mock val")

        # cursor should have been called with the correct sql
        self.mock_get_cur.return_value.execute.assert_called_once_with(
            "SELECT (mock, values) FROM mock_table WHERE mock_key=%s",
            ("mock val"),
        )

        # result should be built from fetchone and description
        self.assertEqual(result, {'one': 1, 'two': 2, 'zero': 0})

        # confirm we closed the cursor
        self.mock_get_cur.return_value.close.assert_called_once_with()

        # if we specify an alternate key
        getter(alternate_key="some other value")

        # that should be reflected in the sql
        self.mock_get_cur.return_value.execute.assert_called_with(
            "SELECT (mock, values) FROM mock_table WHERE alternate_key=%s",
            ("some other value"),
        )

        # confirm that we closed the cursor whenever we got one
        self.assertEqual(
            self.mock_get_cur.call_count,
            self.mock_get_cur.return_value.close.call_count,
        )

    def test_can_pass(self):
        self.assertTrue(True)
