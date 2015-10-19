import unittest
from unittest.mock import patch


class FactoryTestCase(unittest.TestCase):
    """ factories might create objects and relationships based on new info """

    def test_idem_make_service(self):
        """ make a service if it doesnt already exist """
        pass

    def test_can_pass(self):
        self.assertTrue(True)
