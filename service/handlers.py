from service.factories import (
    idem_make_service,
    idem_make_feature,
    idem_make_branch,
    idem_make_iteration,
)

from service.getters import get_iteration
from service.setters import set_iteration


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

    service_id = idem_make_service(repo_name)
    feature_id = idem_make_feature(feature_name, service_id)
    branch_id = idem_make_branch(branch_name, feature_id)
    iteration_id = idem_make_iteration(commit_hash, branch_id)

    return iteration_id

def handle_build(commit_hash, image_name):
    """ ensure the api represents that the image was built from the commit """
    iteration = get_iteration(commit_hash=commit_hash)
    set_iteration(iteration['iteration_id'], {'image_name': image_name})
    return iteration
