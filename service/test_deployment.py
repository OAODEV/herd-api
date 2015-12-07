import os
import unittest
from unittest.mock import (
    patch,
    MagicMock,
)
import base64

from deployment.gce import runner as gce_runner
from deployment.gce import k8s_secret_description
from deployment import (
    actions,
    run,
)


class RunTests(unittest.TestCase):

    def setUp(self):

        os.environ['kubeproxy'] = "mock8s-host"
        os.environ['k8spassword'] = "mock8s-admin-pass"

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
             "mock_env_name",
             "mockcommithash",
             "mock_image_name",
             "mock_settings",)]
        )

    def tearDown(self):
        patch.stopall()

    def test_secret_description_handles_empty_string(self):
        """ creating a service with no key value pairs should not fail """
        # run SUT
        secret = k8s_secret_description('', 'sname', 'bname', 123)

        # confirm
        self.assertEqual(secret, {
            'kind': 'Secret',
            'apiVersion': 'v1',
            'metadata': {
                'name': 'sname-bname-config-123',
            },
            'data': {},
        })

    @unittest.skip('skipping until settings are included in rc')
    def test_rc_description_handles_empty_env_settings_string(self):
        """
        creating an rc with an environment witn no settings should not fail

        """

        # run SUT
        rc = k8s_repcon_description('s', 'b', 123, 'e', 'c', 'i', '')

        # confirm

    def test_gce_runner_infrastructure_match(self):
        """
        gce_runner should create k8s resources for the release

        It should also delete all other RepCons for that branch

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
            "      ,environment_name\n" + \
            "      ,commit_hash\n" + \
            "      ,image_name\n" + \
            "      ,settings\n" + \
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

        # should have created a service in k8s
        self.mock_requests.post.assert_any_call(
            "http://mock8s-host/api/v1/namespaces/default/services",
            data={
                "kind": "Service",
                "apiVersion": "v1",
                "metadata": {
                    "name": "mock-service-name-mock-branch-name",
                },
                "spec": {
                    "ports": [
                        {
                            "port": 8000,
                        }
                    ],
                },
            },
            verify="/secret/k8s.pem",
            auth=('admin', 'mock8s-admin-pass'),
        )

        # should have created a secret in k8s
        self.mock_requests.post.assert_any_call(
            "http://mock8s-host/api/v1/namespaces/default/secrets",
            data={
                "kind": "Secret",
                "apiVersion": "v1",
                "metadata": {
                    "name": "mock-service-name-mock-branch-name-config-789",
                },
                "data": {
                    "mock-key": base64.b64encode(b'mock-value'),
                    "mk": base64.b64encode(b'mv'),
                }
            },
            verify="/secret/k8s.pem",
            auth=('admin', 'mock8s-admin-pass'),
        )

        # should have created a replication controller in k8s
        repcon_name = "mock-branch-name-mock-env-name-mockcommithash-789"
        service_identity = "mock-service-name-mock-branch-name"

        self.mock_requests.post.assert_any_call(
            "http://mock8s-host/api/v1/namespaces/default/" + \
                "replicationcontrollers",
            data={
                "kind": "ReplicationController",
                "apiVersion": "v1",
                "metadata": {
                    "name": repcon_name,
                    "labels": {
                        "name": repcon_name,
                        "service": service_identity,
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
                            },
                        },
                        "spec": {
                            "volumes": {
                                "name": repcon_name + "-secret",
                                "secret": {
                                    "secretName": "mock-branch-name-config-789",
                                },
                            },
                            "containers": [
                                {
                                    "name": service_identity,
                                    "image": "mock-image-name",
                                    "ports": [
                                        {
                                            "containerPort": 8000,
                                        }
                                    ],
                                    "volumeMounts": [
                                        {
                                            "name": repcon_name + "-secret",
                                            "readOnly": True,
                                            "mountPath": "/var/secret/env"
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
