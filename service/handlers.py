from factories import (
    idem_make_service,
    idem_make_feature,
    idem_make_branch,
    idem_make_iteration,
    idem_release_in_automatic_pipelines,
)

from getters import get_iteration
from setters import set_iteration

from deployment import run

from bottle import (
    request,
    abort,
)


################################################################################
###################### Handlers ################################################
################################################################################


def handle_branch_commit(repo_name,
                         feature_name,
                         branch_name,
                         commit_hash):
    """
    Ensure the api represents an associates the appropriate objects

    repo_name represented as a service and associated with,
    feature_name represented as a feature and associated with,
    branch_name represented as a branch and associated with,
    commit_hash represented as a integration

    """

    print(
        "handling branch commit ({}, {}, {}, {})".format(
            repo_name,
            feature_name,
            branch_name,
            commit_hash,
        )
    )

    service_id = idem_make_service(repo_name)
    feature_id = idem_make_feature(feature_name, service_id)
    branch_id = idem_make_branch(branch_name, feature_id)
    iteration_id = idem_make_iteration(commit_hash, branch_id)
    return {'iteration_id': iteration_id}

def handle_build(commit_hash, image_name):
    """
    ensure the api represents that the image was built from the commit

    The iteration gets it's build name updated and releases are created
    for the branch's automatic pipelines. The branch's automatic pipelines
    are run.

    """

    print("handling build ({}, {})".format(commit_hash, image_name,))
    iteration = get_iteration(commit_hash=commit_hash)
    set_iteration(iteration['iteration_id'], {'image_name': image_name})

    # TODO this should return the releases that were created not the pipelines
    # released to. Then releases are what are run.
    releases = idem_release_in_automatic_pipelines(iteration['iteration_id'])
    run(releases)
    return {'iteration_id': iteration['iteration_id']}

################################################################################
################ Supporting Functions ##########################################
################################################################################

def release_in_automatic_pipelines(iteration_id):
    """ Release this iteration in all it's branches automatic pipelines """
    pass
