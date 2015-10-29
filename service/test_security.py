import os
import unittest
from unittest.mock import patch

from security import restricted


def mock_handler(a, b, c):
    return a + b + c

class SecurityTestCase(unittest.TestCase):

    def setUp(self):
        headers_get_patcher = patch(
            'security.request.headers.get',
            return_value="mock@email.com",
        )
        self.mock_headers_get = headers_get_patcher.start()

    def tearDown(self):
        patch.stopall()

    def test_restricted_happy_path(self):
        # set up
        os.environ['whitelist'] = "some@email.com,mock@email.com"

        # run SUT
        result = restricted(mock_handler)(1, 2, 300)

        # handler should have been executed
        self.assertEqual(result, 303)

        # request headers should have been checked
        self.mock_headers_get.assert_called_once_with(
            'X-Authenticated-Email',
        )

        # tear down
        del os.environ['whitelist']

    def test_restricted_not_authorized_path(self):
        # set up
        class ThisError(Exception):
            pass
        os.environ['whitelist'] = "nottheemailyouarelooking@for.com"
        abort_patcher = patch(
            'security.abort',
            side_effect=ThisError,
        )
        mock_abort = abort_patcher.start()

        # run SUT
        with self.assertRaises(ThisError):
            restricted(mock_handler)(1, 2, 300)

        # abort should have been called with 401 "Not Authorized"
        mock_abort.assert_called_once_with(401, "Not Authorized")

        # tear down
        del os.environ['whitelist']

    def test_can_pass(self):
        self.assertTrue(True)
