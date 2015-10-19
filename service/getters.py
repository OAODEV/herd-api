from service.db import get_cursor


def get_iteration(iteration_id=None, commit_hash=None):
    """ Return an iteration """
    cursor = get_cursor()
    if iteration_id:
        cursor.execute(
            "SELECT * FROM iteration WHERE iteration_id={}".format(
                iteration_id,
            ),
        )
    elif commit_hash:
        cursor.execute(
            "SELECT * FROM iteration WHERE commit_hash={}".format(
                commit_hash,
            ),
        )
    else:
        raise LookupError(
            "Please provide either an iteration_id or commit_hash")

    row = cursor.fetchone()
    cursor.close()

    return {
        "iteration_id": row[0],
        "commit_uri": row[1],
        "branch_id": row[2],
        "commit_hash": row[3],
        "image_name": row[4],
        "image_uri": row[5],
        "time_committed": row[6],
    }
