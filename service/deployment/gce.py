import base64
import re
import requests
import pprint

from functools import singledispatch
from config_finder import cfg

from db import get_cursor

pp = pprint.PrettyPrinter(indent=2)

@singledispatch
def b64(*args, **kwargs):
    print(args, kwargs)
    raise TypeError(
        "b64 cannot accept types {}, {}\n".format(
            tuple([type(a) for a in args]),
            dict([(p[0], type(p[1])) for p in kwargs.items()])
        )
    )

b64.register(bytes)(lambda bs: base64.b64encode(bs))
b64.register(str)  (lambda  s: base64.b64encode(s.encode()).decode())

def run_params(release_id):
    """ return the paramaters needed for a run on gce """
    cursor = get_cursor()
    cursor.execute(
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
        (release_id, "gce"),
    )
    result = cursor.fetchall()
    cursor.close()
    return result

def k8s_service_description(service_name, branch_name, port):
    """ return the k8s service description """
    k8s_name_match = re.search(
        # get only the string that matches k8s restrictions
        '[a-z]([-a-z0-9]*[a-z0-9])?',
        # limit the length of the name to fit in k8s restrictions
        "{}-{}".format(service_name[:11], branch_name[:12]),
    )

    if k8s_name_match:
        k8s_name = k8s_name_match.group()
    else:
        # if that doesn't create a good name, just fail.
        raise NameError(
            'Counld not make a good k8s name from {} and {}'.format(
                service_name,
                branch_name,
            )
        )

    return {
        "kind": "Service",
        "apiVersion": "v1",
        "metadata": {
            "name": k8s_name,
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
    print("creating secret with pairs '{}'".format(key_value_pairs))
    data = {}
    for line in [l for l in key_value_pairs.strip().split('\n') if l]:
        key, value = line.split('=')
        # python3 is very strict about encoding!
        data[key] = b64(value)

    return {
        "kind": "Secret",
        "apiVersion": "v1",
        "metadata": {
            "name": "{}-{}-config-{}".format(
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
    rc_name = "{}-{}-{}-{}".format(
        branch_name, environment_name, commit_hash, config_id
    )
    service_identity = "{}-{}".format(service_name, branch_name)
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
                    "volumes": [
                        {
                            "name": "{}-secret".format(rc_name),
                            "secret": {
                                "secretName": "{}-config-{}".format(
                                    branch_name,
                                    config_id
                                ),
                            },
                        },
                    ],
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
                                    "name": "{}-secret".format(rc_name),
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
    endpoint = "http://{}/api/v1/namespaces/default/{}".format(
        cfg('kubeproxy'),
        resource,
    )
    print("posting {} request".format(endpoint))
    pp.pprint(description)
    response = requests.post(
        endpoint,
        json=description,
        verify="/secret/k8s.pem",
        auth=('admin', cfg("k8spassword")),
    )
    print("return:")
    pp.pprint(response.text)
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

    # k8s expects names to be valid urls so we need to replace '_' with '-'
    service_name = service_name.replace('_', '-')
    branch_name = branch_name.replace('_', '-')
    environment_name = str(environment_name).replace('_', '-')
    image_name = image_name.replace('_', '-')

    print("updating {}".format(param_set))

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
