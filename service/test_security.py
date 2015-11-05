import os
import unittest
from unittest.mock import patch

from security import restricted


def mock_handler(a, b, c):
    return a + b + c

class SecurityTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        patch.stopall()

    def test_restricted_happy_path(self):
        # set up
        headers_get_patcher = patch(
            'security.request.headers.get',
            return_value="CI",
        )
        mock_headers_get = headers_get_patcher.start()

        # run SUT
        result = restricted(mock_handler)(1, 2, 300)

        # handler should have been executed
        self.assertEqual(result, 303)

        # request headers should have been checked
        mock_headers_get.assert_called_once_with(
            'X-Authenticated-Token',
        )

    def test_restricted_not_authorized_path(self):
        # set up
        class ThisError(Exception):
            pass
        abort_patcher = patch(
            'security.abort',
            side_effect=ThisError,
        )
        mock_abort = abort_patcher.start()

        headers_get_patcher = patch(
            'security.request.headers.get',
            side_effect=KeyError,
        )
        mock_headers_get = headers_get_patcher.start()

        # run SUT
        with self.assertRaises(ThisError):
            restricted(mock_handler)(1, 2, 300)

        # abort should have been called with 401 "Not Authorized"
        mock_abort.assert_called_once_with(401, "Not Authorized")

    def test_can_pass(self):
        self.assertTrue(True)
