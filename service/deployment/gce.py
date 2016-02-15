import base64
import hashlib
import re
import requests
import pprint
import json
import time

from functools import singledispatch
from config_finder import cfg

from db import get_cursor

pp = pprint.PrettyPrinter(indent=2)

"""
Python3 is very strict about encoding so I wanted to encapsulate
some of the encode/decode bytes->string and back boiler plate
into a single function that would return the type that it was given
but base64 encoded.

This works on bytes and strings and anything else is a TypeError

bytes is the base64.b64encode library function
str   encodes the string to bytes, base64s it then decodes it back
      to a string

"""

@singledispatch
def b64(*args, **kwargs):
    print(args, kwargs)
    raise TypeError(
        "b64 cannot accept types {}, {}\n".format(
            tuple([type(a) for a in args]),
            dict([(p[0], type(p[1])) for p in kwargs.items()])
        )
    )

# register the library funciton for bytes
b64.register(bytes)(base64.b64encode)

# register one that encodes and decodes for strings
@b64.register(str)
def _(s):
    return base64.b64encode(s.encode()).decode()

"""
Let's also make some helper functions for hashing that do
someting similar. I always want a hexdigest, but it should
accept strings or bytes

"""

@singledispatch
def digest(data):
    raise TypeError("expecting str or bytes, got {}, {}".format(
        data, type(data)))

@digest.register(str)
def _(s):
    return hashlib.sha256(s.encode()).hexdigest()

@digest.register(bytes)
def _(b):
    return hashlib.sha256(b).hexdigest()

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


def service_identity(service_name, branch_name):
    return "{}-{}".format(service_name, branch_name)


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
            "selector": {
                "service": service_identity(service_name, branch_name)
            },
            "ports": [
                {
                    "port": 8000,
                },
            ],
        },
    }


def k8s_secret_description(key_value_pairs, config_id):
    """ return the k8s secret description """
    print("creating secret with pairs '{}'".format(key_value_pairs))
    data = {}
    for line in [l for l in key_value_pairs.strip().split('\n') if l]:
        try:
            key, value = line.split('=')
        except Exception as e:
            print("Could not parse line {} in config {}".format(
                line,
                key_value_pairs,
            ))
            raise e
        data[key] = b64(value)

    return {
        "kind": "Secret",
        "apiVersion": "v1",
        "metadata": {
            "name": "{}-config-{}".format(digest(key_value_pairs), config_id)
        },
        "data": data,
    }


def make_rc_name(branch_name, environment_name, commit_hash, config_id):
    """
    make a replication controller name suitable for k8s labels
    must have at most 63 characters,
    must match regex '([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9])?'

    """

    # limit the string to 63 characters
    name = "{}-{}-{}-{}".format(    #  4 dashes
        branch_name[:27],           # 27 branch name
        environment_name[:20],      # 20 environment name
        commit_hash[:7],            #  7 commit hash
        config_id,                  #  5 left for config id
    )

    # check that it matches the required regex
    name_match = re.search(
        '(([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9])?',
        name,
    )
    if not name_match:
        raise NameError(
            "cannot make good k8s name from {}".format([
                branch_name,
                environment_name,
                commit_hash,
                config_id,
            ])
        )

    return name_match.group()


def k8s_repcon_description(service_name,
                           branch_name,
                           config_id,
                           environment_name,
                           commit_hash,
                           image_name,
                           settings,
                           key_value_pairs,
):
    """ return the k8s replication controller description """
    rc_name = make_rc_name(
        branch_name,
        environment_name,
        commit_hash,
        config_id
    )

    service_label = service_identity(service_name, branch_name)

    return {
        "kind": "ReplicationController",
        "apiVersion": "v1",
        "metadata": {
            "name": rc_name,
            "labels": {
                "name": rc_name,
                "service": service_label,
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
                                    digest(key_value_pairs),
                                    config_id,
                                ),
                            },
                        },
                    ],
                    "containers": [
                        {
                            "name": service_label,
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
                                    "mountPath": "/secret",
                                }
                            ]
                        },
                    ]
                },
            },
        },
    }


def k8s_endpoint(resource):
    """ return the endpoint for the given resource type """
    endpoint = "http://{}/api/v1/namespaces/default/{}".format(
        cfg('kubeproxy'),
        resource,
    )
    return endpoint


def idem_post(resource, description):
    """ idempotently post a resource to k8s """
    endpoint = k8s_endpoint(resource)
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


def watch_uri(uri):
    """ return a watch uri for a given k8s resource uri """
    updated = uri.replace("/api/v1/", "/api/v1/watch/")
    if updated == uri:
        raise TypeError("uri ({}) doesn't look like a k8s resource".format(uri))
    return updated

def sync_scale(uri, scale_to, timeout=30):
    """ scale an rc and wait til it's done """
    resp = requests.patch(
        uri,
        data=json.dumps({"spec": {"replicas": scale_to}}),
        headers={"Content-Type": "application/merge-patch+json"},
    )
    print(resp.json())

    # wait for the rc to scale to zero
    for s in range(5):
        resp = requests.get(uri).json()
        if resp['status']['replicas'] == scale_to:
            break
        else:
            time.sleep(s)

def gc_repcons(service_name,
               branch_name,
               environment_name,
               commit_hash,
               config_id):
    """ delete all other repcons for this branch of this service """
    # get all repcons creating pods labeled for this service
    # the repcon should be labeled with service=this_service_label
    rc_name = make_rc_name(
        branch_name,
        environment_name,
        commit_hash,
        config_id,
    )
    selector = "service={}".format(service_identity(service_name, branch_name))
    response = requests.get(
        k8s_endpoint("replicationcontrollers"),
        params={
            "labelSelector": selector,
        },
    )
    delete_repcon_uris = []

    # normally we would exclude the current repcon name, except that
    # we want to start fresh and update in case there is new config.

    # we are deleting all repcons for this branch in order to get settings updates
    # until we refactor to the simpler data model.
#    for item in response.json()['items']:
#        if item['metadata']['name'] != rc_name:
#            delete_repcon_uris.append(
#                "http://{}{}".format(
#                    cfg("kubeproxy"),
#                    item['metadata']['selfLink']
#                )
#            )

    # scale to zero and delete the remaining repcons
    for uri in delete_repcon_uris:
        print("Scaling repcon at {} to zero".format(uri))
        sync_scale(uri, 0)
        print("Delete request to {}".format(uri))
        requests.delete(uri)


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

    print("updating {}".format(param_set))

    idem_post(
        "services",
        k8s_service_description(service_name, branch_name, 8000),
    )

    idem_post("secrets", k8s_secret_description(key_value_pairs, config_id))

    # here we delete all repcons for this branch so that we will get config
    # changes even if the build did not change. This will be refactored when
    # we move to a simpler data model. In fact this is the impotus to move to
    # the simpler data model.

    gc_repcons(
        service_name,
        branch_name,
        environment_name,
        commit_hash,
        config_id,
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
            settings,
            key_value_pairs,
        )
    )




actions = {
    "UPDATE": update,
}


def runner(run_request):
    """ carry out the run request """
    for param_set in run_params(run_request['release_id']):
        actions[run_request['action']](param_set)

    return True
