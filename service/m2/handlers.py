from lenses import (
    Iteration,
    Service,
)


def handle_commit(repo_name, branch_name, commit_hash):
    return = Service(repo_name).branch(branch_name).iteration(commit_hash)


def handle_build(branch_name, commit_hash, image_name):
    deployment =  Iteration(
        branch_name,
        commit_hash,
        image_name=image_name
    ).release().deployment()

    return deploy(deployment)
