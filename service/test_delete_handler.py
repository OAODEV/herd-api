import unittest

class DeleteHandlerTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


    @unittest.skip("bring this back when working on delete handler")
    def test_github_delete_interface(self):
        """ accept github's webhook delete message format """
        self.assertTrue(False)

    @unittest.skip("bring this back when working on delete handler")
    def test_delete_branch_updates_model(self):
        """ should update the correct branch with a deleted datetime """
        self.assertTrue(False)

    @unittest.skip("bring this back when working on delete handler")
    def test_delete_branch_stops_the_correct_release(self):
        """ should stop the running releases for that branch """
        self.assertTrue(False)

