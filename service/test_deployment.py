import hashlib
import os
import unittest
from unittest.mock import (
    patch,
    MagicMock,
)
import base64
from deployment.gce import runner as gce_runner
from deployment.gce import (
    gc_repcons,
    k8s_secret_description,
    make_rc_name,
    watch_uri
)
from deployment import (
    actions,
    run,
)


class RunTests(unittest.TestCase):

    def setUp(self):

        os.environ['kubeproxy'] = "mock8s-host"
        os.environ['k8spassword'] = "mock8s-admin-pass"

        os.environ['v2_model'] = 'run'

        requests_patcher = patch("deployment.gce.requests")
        self.mock_requests = requests_patcher.start()

        self.mock_runner = MagicMock()
        all_patcher = patch(
            'deployment.runners.runners.all',
            return_value=[self.mock_runner],
        )
        all_patcher.start()
        self.get_cursor_patcher = patch("deployment.gce.get_cursor")
        self.mock_get_cursor = self.get_cursor_patcher.start()
        self.mock_get_cursor.return_value.fetchall.return_value = (
            [("mock_service_name",
             "mock_branch_name",
             789, # mock config id
             "mock-key=mock-value\nmk=mv\n",
             "mockcommithash",
             "mock_image_name")]
        )

        # mock up m2 cursor to return the same as the m1 so we can confirm
        # they are doing the same thing.
        self.m2_get_cursor_patcher = patch("deployment.gce.m2_get_cursor")
        self.m2_mock_get_cursor = self.m2_get_cursor_patcher.start()
        self.m2_mock_get_cursor.return_value.fetchall.return_value = (
            [("m2mock_service_name",
              "m2mock_branch_name",
              234, # mock config id
              "m2mock-key=mock-value\nmk=mv\n",
              "m2mockcommithash",
              "m2mock_image_name")]
        )

    def tearDown(self):
        patch.stopall()

    def test_gc_repcons(self):
        """ Should delete all but the given repcon for the service """
        # set up
        mock_return = MagicMock()
        mock_return.json.return_value = {
            'items': [
                {
                    'metadata': {
                        'name': 'mockfirstname',
                        'selfLink': '/api/v1/mockfirstselflink',
                    }
                },
                {
                    'metadata': {
                        'name': 'mocksecondname',
                        'selfLink': '/api/v1/mocksecondselflink',
                    }
                },
                {
                    'metadata': {
                        'name': make_rc_name(
                            'mock_branch_name',
                            'mock_service_name',
                            'mock_commit_hash',
                            'mock_config_id'
                        ),
                        'selfLink': '/api/v1/mockmatchingselflink',
                    }
                },
            ],
            "status": {"replicas": 0},
        }
        self.mock_requests.get.return_value = mock_return

        # run SUT
        gc_repcons(
            'mock_service_name',
            'mock_branch_name',
            'mock_commit_hash',
            'mock_config_id',
        )

        # confirm asumptions
        # should have gotten the correctly labeled rcs
        self.mock_requests.get.assert_any_call(
            "http://mock8s-host/api/v1/namespaces/default/replicationcontrollers",
            params={
                "labelSelector": ("service=mock_service_name,"
                                  "branch=mock_branch_name"),
            },
        )

        # should have scaled down what came back to 0 other than the current one
        self.mock_requests.patch.assert_any_call(
            'http://mock8s-host/api/v1/mockfirstselflink',
            data='{"spec": {"replicas": 0}}',
            headers={"Content-Type": "application/merge-patch+json"},
        )
        self.mock_requests.patch.assert_any_call(
            'http://mock8s-host/api/v1/mocksecondselflink',
            data='{"spec": {"replicas": 0}}',
            headers={"Content-Type": "application/merge-patch+json"},
        )
        # actually now that we are just deleting all of the repcons (to get
        # updated config), we want to see 3 here.
        self.assertEqual(self.mock_requests.patch.call_count, 3)

        # should have deleted what came back other than the current one
        self.mock_requests.delete.assert_any_call(
            'http://mock8s-host/api/v1/mockfirstselflink')
        self.mock_requests.delete.assert_any_call(
            'http://mock8s-host/api/v1/mocksecondselflink')
        # actually now that we are just deleting all of the repcons (to get
        # updated config), we want to see 3 here.
        self.assertEqual(self.mock_requests.delete.call_count, 3)

    def test_secret_description_handles_empty_string(self):
        """ creating a service with no key value pairs should not fail """
        # run SUT
        secret = k8s_secret_description('', 123)

        # confirm
        self.assertEqual(secret, {
            'kind': 'Secret',
            'apiVersion': 'v1',
            'metadata': {
                'name': '{}-config-123'.format(hashlib.sha256(b'').hexdigest()),
            },
            'data': {},
        })

    def test_secret_description_handles_equals_sign_in_string(self):
        """ a value that has an equals sign in it should not fail"""
        # run SUT
        secret = k8s_secret_description('key=value=morevalue', 123)

        # confirm
        self.assertEqual(secret, {
            'kind': 'Secret',
            'apiVersion': 'v1',
            'metadata': {
                'name': '{}-config-123' \
                        .format(hashlib.sha256(b'key=value=morevalue')
                                       .hexdigest()),
            },
            'data': {'key': base64.b64encode(b'value=morevalue')
                                  .decode('utf-8')},
        })

    @unittest.skip('skipping until settings are included in rc')
    def test_rc_description_handles_empty_env_settings_string(self):
        """
        creating an rc with an environment witn no settings should not fail

        """

        # run SUT
        rc = k8s_repcon_description('s', 'b', 123, 'e', 'c', 'i', '')

        # confirm

    def test_watch_uri(self):
        """ given a k8s resource uri, return a watch uri for that resource """
        self.assertEqual(
            watch_uri("/api/v1/replicationcontrollers"),
            "/api/v1/watch/replicationcontrollers",
        )
        self.assertEqual(
            watch_uri("http://localhost:8001/api/v1/any/thing/else?a=b"),
            "http://localhost:8001/api/v1/watch/any/thing/else?a=b",
        )

        with self.assertRaises(TypeError):
            watch_uri("http://www.google.com")
        with self.assertRaises(TypeError):
            watch_uri("http://www.google.com/api/v2/anything")
        with self.assertRaises(TypeError):
            watch_uri("http://www.google.com/notapi/v1/anything")

    def test_gce_runner_infrastructure_match(self):
        """
        gce_runner should create k8s resources for the release

        It should also delete all other RepCons for that branch

        During the refactor it should also be calling the version two
        model's params

        """

        # run SUT
        gce_runner({'release_id': 123, 'action': actions.UPDATE})

        # we should have grabbed the info for a service, secret and repcon from
        # the database
        self.mock_get_cursor.return_value.execute.assert_called_with(
            "SELECT service_name\n" + \
            "      ,branch_name\n" + \
            "      ,c.config_id\n" + \
            "      ,key_value_pairs\n" + \
            "      ,commit_hash\n" + \
            "      ,image_name\n" + \
            "  FROM release r\n" + \
            "  JOIN iteration i\n" + \
            "    ON i.iteration_id = r.iteration_id\n" + \
            "  JOIN branch b\n" + \
            "    ON b.branch_id = i.branch_id\n" + \
            "  JOIN deployment_pipeline d\n" + \
            "    ON b.branch_id = d.branch_id\n" + \
            "   AND d.deployment_pipeline_id = r.deployment_pipeline_id\n" + \
            "  JOIN config c\n" + \
            "    ON c.config_id = d.config_id\n" + \
            "  JOIN environment e\n" + \
            "    ON e.environment_id = d.environment_id\n" + \
            "  JOIN feature f\n" + \
            "    ON f.feature_id = b.feature_id\n" + \
            "  JOIN service s\n" + \
            "    ON s.service_id = f.service_id\n" + \
            " WHERE release_id = %s\n" + \
            "   AND infrastructure_backend = %s",
            (123, "gce"),
        )

        self.m2_mock_get_cursor.return_value.execute.assert_called_with(
            ("select service_name\n"
             "      ,branch_name\n"
             "      ,c.config_id\n"
             "      ,key_value_pairs\n"
             "      ,commit_hash\n"
             "      ,image_name\n"
             "  from release r\n"
             "  join iteration i\n"
             "    on i.iteration_id = r.iteration_id\n"
             "  join branch b\n"
             "    on b.branch_id = i.branch_id\n"
             "  join config c\n"
             "    on c.config_id = r.config_id\n"
             "  join service s\n"
             "    on b.service_id\n"
             " where release_id=%s"),
            (123,),
        )

        # should have created a service in k8s
        self.mock_requests.post.assert_any_call(
            "http://mock8s-host/api/v1/namespaces/default/services",
            json={
                "kind": "Service",
                "apiVersion": "v1",
                "metadata": {
                    "name": "mock-servic-mock-branch",
                },
                "spec": {
                    "ports": [
                        {
                            "port": 8000,
                        }
                    ],
                    "selector":{
                        'service': 'mock-service-name-mock-branch-name',
                    },
                },
            },
            verify="/secret/k8s.pem",
            auth=('admin', 'mock8s-admin-pass'),
        )

        self.mock_requests.post.assert_any_call(
            "http://mock8s-host/api/v1/namespaces/default/services",
            json={
                "kind": "Service",
                "apiVersion": "v1",
                "metadata": {
                    "name": "m2mock-serv-m2mock-branc",
                },
                "spec": {
                    "ports": [
                    {
                        "port": 8000,
                    }
                    ],
                    "selector":{
                        'service': 'm2mock-service-name-m2mock-branch-name',
                    },
            },
            },
            verify="/secret/k8s.pem",
            auth=('admin', 'mock8s-admin-pass'),
        )

        secret_name = "{}-config-789".format(
            hashlib.sha256(b'mock-key=mock-value\nmk=mv\n').hexdigest()
        )

        m2_secret_name = "{}-config-234".format(
            hashlib.sha256(b'm2mock-key=mock-value\nmk=mv\n').hexdigest()
        )

        # should have created a secret in k8s
        self.mock_requests.post.assert_any_call(
            "http://mock8s-host/api/v1/namespaces/default/secrets",
            json={
                "kind": "Secret",
                "apiVersion": "v1",
                "metadata": {
                    "name": secret_name,
                },
                "data": {
                    "mock-key": base64.b64encode(b'mock-value').decode('utf-8'),
                    "mk": base64.b64encode(b'mv').decode('utf-8'),
                }
            },
            verify="/secret/k8s.pem",
            auth=('admin', 'mock8s-admin-pass'),
        )

        self.mock_requests.post.assert_any_call(
            "http://mock8s-host/api/v1/namespaces/default/secrets",
            json={
                "kind": "Secret",
                "apiVersion": "v1",
                "metadata": {
                    "name": m2_secret_name,
                },
                "data": {
                    "m2mock-key": base64.b64encode(b'mock-value').decode('utf-8'),
                    "mk": base64.b64encode(b'mv').decode('utf-8'),
                }
            },
            verify="/secret/k8s.pem",
            auth=('admin', 'mock8s-admin-pass'),
        )

        # should have created a replication controller in k8s
        repcon_name = "mock-branch-name-mock-service-name-mockcom-789"
        service_identity = "mock-service-name-mock-branch-name"

        m2_repcon_name = "m2mock-branch-name-m2mock-service-name-m2mockc-234"
        m2_service_identity = "m2mock-service-name-m2mock-branch-name"

        self.mock_requests.post.assert_any_call(
            "http://mock8s-host/api/v1/namespaces/default/" + \
                "replicationcontrollers",
            json={
                "kind": "ReplicationController",
                "apiVersion": "v1",
                "metadata": {
                    "name": repcon_name,
                    "labels": {
                        "name": repcon_name,
                        "service": 'mock-service-name',
                        "branch": 'mock-branch-name',
                    },
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "name": repcon_name,
                    },
                    "template": {
                        "metadata": {
                            "labels": {
                                "name": repcon_name,
                                "branch": "mock-branch-name",
                                "service": "mock-service-name",
                            },
                        },
                        "spec": {
                            "volumes": [{
                                "name": repcon_name + "-secret",
                                "secret": {
                                    "secretName": secret_name,
                                },
                            }],
                            "containers": [
                                {
                                    "name": service_identity,
                                    "image": "mock_image_name",
                                    "ports": [
                                        {
                                            "containerPort": 8000,
                                        }
                                    ],
                                    "volumeMounts": [
                                        {
                                            "name": repcon_name + "-secret",
                                            "readOnly": True,
                                            "mountPath": "/secret"
                                        }
                                    ],
                                },
                            ],
                        },
                    },
                },
            },
            verify="/secret/k8s.pem",
            auth=('admin', 'mock8s-admin-pass'),
        )

        self.mock_requests.post.assert_any_call(
            "http://mock8s-host/api/v1/namespaces/default/" + \
                "replicationcontrollers",
            json={
                "kind": "ReplicationController",
                "apiVersion": "v1",
                "metadata": {
                    "name": m2_repcon_name,
                    "labels": {
                        "name": m2_repcon_name,
                        "service": "m2mock-service-name",
                        "branch": "m2mock-branch-name",
                    },
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "name": m2_repcon_name,
                    },
                    "template": {
                        "metadata": {
                            "labels": {
                                "name": m2_repcon_name,
                                "branch": "m2mock-branch-name",
                                "service": "m2mock-service-name",
                            },
                        },
                        "spec": {
                            "volumes": [{
                                "name": m2_repcon_name + "-secret",
                                "secret": {
                                    "secretName": m2_secret_name,
                                },
                            }],
                            "containers": [
                                {
                                    "name": m2_service_identity,
                                    "image": "m2mock_image_name",
                                    "ports": [
                                        {
                                            "containerPort": 8000,
                                        }
                                    ],
                                    "volumeMounts": [
                                        {
                                            "name": m2_repcon_name + "-secret",
                                            "readOnly": True,
                                            "mountPath": "/secret"
                                        }
                                    ],
                                },
                            ],
                        },
                    },
                },
            },
            verify="/secret/k8s.pem",
            auth=('admin', 'mock8s-admin-pass'),
        )

        # make sure we closed the cursor
        self.mock_get_cursor.return_value.close.asert_called_once_with()

    def test_run(self):
        """
        Make a run request(s) from a pipeline(s), give it to a runner

        Each pipeline will specify an environment with an infrastructure.
        run shouild give the run request to the runnder for that infrastructure.

        """

        # run SUT
        run(123)

        # we should have passed a good run request to the runner
        self.mock_runner.assert_called_once_with(
            {'release_id': 123, 'action': actions.UPDATE}
        )

        # should fail on dictionaries
        with self.assertRaises(TypeError):
            run({'1', 2})

        # should work on lists
        run([456, 789])

        self.mock_runner.assert_any_call(
            {'release_id': 456, 'action': actions.UPDATE},
        )
        self.mock_runner.assert_any_call(
            {'release_id': 789, 'action': actions.UPDATE},
        )

        # whould work on tuples of lists of strings
        run((1, [2,3], ['4', '567']))

        self.mock_runner.assert_any_call(
            {'release_id': 1, 'action': actions.UPDATE},
        )
        self.mock_runner.assert_any_call(
            {'release_id': 2, 'action': actions.UPDATE},
        )
        self.mock_runner.assert_any_call(
            {'release_id': 3, 'action': actions.UPDATE},
        )
        self.mock_runner.assert_any_call(
            {'release_id': 4, 'action': actions.UPDATE},
        )
        self.mock_runner.assert_any_call(
            {'release_id': 567, 'action': actions.UPDATE},
        )


    def test_can_pass(self):
        self.assertTrue(True)
