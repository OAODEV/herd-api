import base64
import requests
import pprint

from config_finder import cfg

from db import get_cursor

pp = pprint.PrettyPrinter(indent=2)

def run_params(release_id):
    """ return the paramaters needed for a run on gce """
    cursor = get_cursor()
    cursor.execute(
            "SELECT (service_name\n" + \
            "       ,branch_name\n" + \
            "       ,config_id\n" + \
            "       ,key_value_pairs\n" + \
            "       ,environment_name\n" + \
            "       ,commit_hash\n" + \
            "       ,image_name\n" + \
            "       ,settings\n" + \
            "       )\n" + \
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
            "   AND infrastructure = gce",
        (release_id,),
    )
    result = cursor.fetchall()
    cursor.close()
    return result

def k8s_service_description(service_name, branch_name, port):
    """ return the k8s service description """
    return {
        "kind": "Service",
        "apiVersion": "v1",
        "metadata": {
            "name": "{}_{}".format(service_name, branch_name),
        },
        "spec": {
            "ports": [
                {
                    "port": 8000,
                },
            ],
        },
    }

def k8s_secret_description(key_value_pairs,
                           service_name,
                           branch_name,
                           config_id):
    """ return the k8s secret description """
    data = {}
    for line in key_value_pairs.strip().split('\n'):
        key, value = line.split('=')
        # python3 is very strict about encoding!
        data[key] = base64.b64encode(value.encode('ascii'))

    return {
        "kind": "Secret",
        "apiVersion": "v1",
        "metadata": {
            "name": "{}_{}_config_{}".format(
                service_name,
                branch_name,
                config_id,
            )
        },
        "data": data,
    }

def k8s_repcon_description(service_name,
                           branch_name,
                           config_id,
                           environment_name,
                           commit_hash,
                           image_name,
                           settings):
    """ return the k8s replication controller description """
    rc_name = "{}_{}_{}_{}".format(
        branch_name, environment_name, commit_hash, config_id
    )
    service_identity = "{}_{}".format(service_name, branch_name)
    return {
        "kind": "ReplicationController",
        "apiVersion": "v1",
        "metadata": {
            "name": rc_name,
            "labels": {
                "name": rc_name,
                "service": service_identity,
            },
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "name": rc_name,
            },
            "template": {
                "metadata": {
                    "labels": {
                        "name": rc_name,
                    },
                },
                "spec": {
                    "volumes": {
                        "name": "{}_secret".format(rc_name),
                        "secret": {
                            "secretName": "{}_config_{}".format(
                                branch_name,
                                config_id
                            ),
                        },
                    },
                    "containers": [
                        {
                            "name": service_identity,
                            "image": image_name,
                            "ports": [
                                {
                                    "containerPort": 8000,
                                },
                            ],
                            "volumeMounts": [
                                {
                                    "name": "{}_secret".format(rc_name),
                                    "readOnly": True,
                                    "mountPath": "/var/secret/env",
                                }
                            ]
                        },
                    ]
                },
            },
        },
    }

def idem_post(resource, description):
    """ idempotently post a resource to k8s """
    print()
    print("posting {} request".format(resource))
    pp.pprint(description)
    print()
    response = requests.post(
        "https://{}/api/v1/default/{}".format(
            cfg('kubernetes_master_host'),
            resource,
        ),
        data=description,
        verify="/secret/k8s.pem",
        auth=('admin', cfg("kubernetes_admin_password")),
    )
    return response

def gc_repcons(service_name,
               branch_name,
               environment_name,
               commit_hash,
               config_id):
    """ delete all other repcons for this branch of this service """
    pass

def update(param_set):
    """ create service, secret and repcon, then garbage collect old repcons """
    (service_name,
     branch_name,
     config_id,
     key_value_pairs,
     environment_name,
     commit_hash,
     image_name,
     settings) = param_set

    idem_post(
        "services",
        k8s_service_description(service_name, branch_name, 8000),
    )

    idem_post(
        "secrets",
        k8s_secret_description(
            key_value_pairs,
            service_name,
            branch_name,
            config_id
        ),
    )

    idem_post(
        "replicationcontrollers",
        k8s_repcon_description(
            service_name,
            branch_name,
            config_id,
            environment_name,
            commit_hash,
            image_name,
            settings
        )
    )

    gc_repcons(
        service_name,
        branch_name,
        environment_name,
        commit_hash,
        config_id
    )

actions = {
    "UPDATE": update,
}

def runner(run_request):
    """ carry out the run request """
    for param_set in run_params(run_request['release_id']):
        actions[run_request['action']](param_set)

    return True
