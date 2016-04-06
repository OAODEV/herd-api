from db import m2_get_cursor as get_cursor
from handlers import (
    handle_branch_commit,
    handle_build as leg_handle_build,
)
from hypothesis import (
    example,
    given,
)
from hypothesis.strategies import (
    integers,
    text,
)
from m2.handlers import (
    handle_build,
    save,
)
import os
import psycopg2
import testing.postgresql
import unittest
from unittest.mock import patch


def pg_init(pg):
    conn = psycopg2.connect(**pg.dsn())
    cursor = conn.cursor()
    with open('service/schema.sql', 'r') as schema:
        cursor.execute(schema.read())
    conn.commit()
    cursor.close()
    conn.close()

# Generate Postgresql class which shares the generated database
Postgresql = testing.postgresql.PostgresqlFactory(
    cache_initialized_db=True,
    on_initialized=pg_init,
)


def tearDownModule():
    # clear cached database at end of tests
    Postgresql.clear_cache()


class M2HandlersIntegrationCase(unittest.TestCase):

    def setUp(self):
        self.pg = Postgresql()
        os.environ['pg-host'] = self.pg.dsn()['host']
        os.environ['pg-port'] = str(self.pg.dsn()['port'])
        os.environ['pg-database'] = self.pg.dsn()['database']
        os.environ['pg-user'] = self.pg.dsn()['user']

    def tearDown(self):
        self.pg.stop()

    def test_handle_build(self):
        """ handle branch should save the service, branch and iteration """
        # run SUT
        handle_build(
            'mock_service',
            'mock_branch',
            'mock_commitabc112',
            'us.gcr.io/mock-image:v0.1',
        )

        # confirm
        cursor = get_cursor()
        cursor.execute(
            "select service_name, branch_name, commit_hash, image_name\n" + \
            "  from service\n" + \
            "  join branch using (service_id)\n" + \
            "  join iteration using (branch_id)\n" + \
            " where image_name='us.gcr.io/mock-image:v0.1'"
        )
        results = cursor.fetchall()
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0],
            ('mock_service',
             'mock_branch',
             'mock_commitabc112',
             'us.gcr.io/mock-image:v0.1')
        )
        cursor.close()

    @given(
        commit_hash=text(max_size=99),
        image_name=text(max_size=99)
    )
    @example(
        commit_hash='anything',
        image_name='something\x00weird',
    )
    @example(
        commit_hash='\x0b\n\x05\U000beb17\x07',
        image_name='\x00',
    )
    def test_save_idempotent_by_uniqueness(
            self,
            commit_hash,
            image_name,
    ):
        """
        iterations should be idempotent, even though no all of their
        columns are included in uniqueness constraints

        anything with the null character will be truncated at the null character
        because this is what postgresql does.

        """

        # set up
        cursor = get_cursor()
        # save a service so we can have a branch
        service_id = save(
            cursor,
            'service',          # table name
            ['service_name'],   # unique columns
            ['service_name'],   # all columns
            ['mock_service'],   # values to insert
        )
        # save a branch so we have a stable branch id to save
        # iterations against
        branch_id = save(
            cursor,
            'branch',                        # table name
            ['service_id', 'branch_name'],   # unique columns
            ['service_id', 'branch_name'],   # all columns
            [ service_id , 'mock_branch'],   # values to insert
        )

        """
        If someone tries to save a build name to a branch, commit pair that
        exists the existing build name will be used and the new build name
        being saved will be ignored.
        """
        # because this test is run many times with random data we need
        # to handle two cases. One when we have a branch, commit pair
        # that we have not saved and one when we have saved that
        # branch, commit pair

        # check to see if we have this branch, commit pair saved
        cursor.execute(
            "select image_name\n" + \
            "  from iteration\n" + \
            " where commit_hash=%s and branch_id=%s",
            (commit_hash, branch_id),
        )
        result = cursor.fetchall()
        # if we have it,
        if result:
            # we should only have one
            self.assertEqual(len(result), 1)
            # and we expect it to stay the same
            expected_image_name = result[0][0]
        else:
            # otherwise we expect the new name (up to a null character) to be
            # saved
            expected_image_name = image_name.split('\x00')[0]

        # run SUT
        # save an iteration twice
        iteration_id = save(
            cursor,
            'iteration',                                  # table name
            ['commit_hash', 'branch_id'],                 # unique columns
            ['commit_hash', 'branch_id', 'image_name'],   # all columns
            ( commit_hash ,  branch_id ,  image_name ),   # values to insert
        )
        iteration_id = save(
            cursor,
            'iteration',                                  # table name
            ['commit_hash', 'branch_id'],                 # unique columns
            ['commit_hash', 'branch_id', 'image_name'],   # all columns
            ( commit_hash ,  branch_id ,  image_name ),   # values to insert
        )
        # also with a different image name
        iteration_id = save(
            cursor,
            'iteration',                                  # table name
            ['commit_hash', 'branch_id'],                 # unique columns
            ['commit_hash', 'branch_id', 'image_name'],   # all columns
            ( commit_hash ,  branch_id , 'different?'),   # values to insert
        )
        cursor.close()
        cursor = get_cursor()

        # confirm assumptions
        # dispite three saves and one having a different image name
        cursor.execute(
            "select commit_hash, branch_id, image_name\n" + \
            "  from iteration\n" + \
            " where commit_hash=%s and branch_id=%s",
            (commit_hash, branch_id),
        )
        results = cursor.fetchall()
        cursor.close()
        # we should only have one result for this commit_hash
        self.assertEqual(len(results), 1)
        # and it should be the image name we expect (not the most recent one)
        self.assertEqual(results[0][2], expected_image_name)

    @given(text())
    @example(text=';')
    @example(text='\'')
    def test_save_is_idempotent(self, text):
        """ when we save stuff more than once it should only get in once """
        # run SUT
        cursor = get_cursor()
        service_id = save(
            cursor,
            'service',                 # table name
            ['service_name'],          # unique columns
            ['service_name'],          # all columns
            (text,),                   # values to insert
        )
        cursor.execute(
            "SELECT service_id, service_name\n" + \
            "FROM service\n" + \
            "WHERE service_name=%s",
            (text,),
        )
        first_result = cursor.fetchall()
        cursor.close()

        cursor = get_cursor()
        service_id = save(
            cursor,
            'service',                 # table name
            ['service_name'],          # unique columns
            ['service_name'],          # all columns
            (text,),                   # values to insert
        )
        cursor.execute(
            "SELECT service_id, service_name\n" + \
            "FROM service\n" + \
            "WHERE service_name=%s",
            (text,),
        )
        second_result = cursor.fetchall()

        # confirm that the second save did not change the result
        self.assertEqual(first_result, second_result)

    def test_save_inserts_new_data(self):
        """ save should create rows for new data, and new data only"""
        # run SUT
        cursor = get_cursor()
        service_id = save(
            cursor,
            'service',                 # table name
            ['service_name'],          # unique columns
            ['service_name'],          # all columns
            ('mock_service_name',),    # values to insert
        )
        cursor.close()

        # save returns an integer id for the service table
        self.assertTrue(isinstance(service_id, int))

        # save creates one row per call with the saved data
        cursor = get_cursor()
        cursor.execute(
            "SELECT service_id, service_name\n" + \
            "FROM service\n" + \
            "WHERE service_name='mock_service_name'"
        )
        result = cursor.fetchall()
        cursor.close()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], 'mock_service_name')

    def test_can_pass(self):
        self.assertTrue(True)


class HandlersTestCase(unittest.TestCase):
    """ test the web handlers """

    def setUp(self):
        get_cursor_patcher = patch('factories.get_cursor')
        self.mock_get_cursor = get_cursor_patcher.start()

    def tearDown(self):
        patch.stopall()

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
        release_in_auto_pipes_patcher = patch(
            "handlers.idem_release_in_automatic_pipelines",
            return_value=12345,
        )
        run_patcher = patch("handlers.run")
        mock_get_iteration = get_iteration_patcher.start()
        mock_set_iteration = set_iteration_patcher.start()
        mock_release_in_auto_pipes = release_in_auto_pipes_patcher.start()
        mock_run = run_patcher.start()

        # run SUT
        result = leg_handle_build('mock-commit-hash', 'mock-image-name')

        # confirm assumptions
        mock_get_iteration.assert_called_once_with(
            commit_hash="mock-commit-hash",
        )
        mock_set_iteration.assert_called_once_with(
            'mock-iteration-id',
            {'image_name': 'mock-image-name'}
        )
        mock_release_in_auto_pipes.assert_called_once_with(
            'mock-iteration-id',
        )
        mock_run.assert_called_once_with(12345)

    def test_can_pass(self):
        self.assertTrue(True)
