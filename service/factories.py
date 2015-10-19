def idem_make_service(repo_name):
    """ Idempotently create a service """

def idem_make_feature(feature_name, service_id):
    """ Idempotently create a feature """
    pass

def idem_make_branch(branch_name, feature_id):
    """ Idempotently create a branch """
    pass

def idem_make_iteration(branch_id, commit_hash):
    """ Idempotently Make create an iteration """
    pass

def new_deployment_pipeline(branch_id, copy_config_id=None, copy_env_id=None):
    """
    Make a new deployment pipeline from a branch

    Will create new config and environments as copies of the given config
    and environments, or use a unit config and environment.

    """

    pass

