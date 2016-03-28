from db import m2_get_cursor as get_cursor
from uuid import uuid4

default = str(uuid4())

def save(cursor, table, columns, values, returning=default):
    """ Save some values to a table if they don't conflict. """
    if returning == default:
        returning = '{}_id'.format(table)
    column_str = ', '.join(columns)
    value_placeholders = ', '.join(['%s' for x in values])
    cursor.execute(
        "INSERT INTO {} ({})\n" + \
        "     VALUES ({})\n" + \
        "ON CONFLICT DO NOTHING\n" + \
        "  RETURNING {}".format(
            table,
            columns_str,
            value_placeholders,
            on_conflict,
            returning,
        )
        row_dict.values(),
    )
    return_value = cursor.fetchone()[0]
    return return_value


def handle_build(service_name, branch_name, commit_hash, image_name):
    """
    Save the data going into this build, then deploy the build

    Service, branch, commit and image are idempotently saved to the
    database.

    """
    cursor = get_cursor()
    service_id = save(
        cursor,
        'serivce', 
        ['service_name'],
        [ service_name ],
    )
    branch_id = save(
        cursor,
        'branch',
        ['branch_name', 'service_id'],
        [ branch_name ,  service_id ],
    )
    iteration_id = save(
        cursor,
        'iteration',
        ['commit_hash', 'branch_id', 'image_name'],
        [ commit_hash ,  branch_id ,  image_name ],
    )
    cursor.close()
    
