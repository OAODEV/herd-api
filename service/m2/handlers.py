"""
Handlers will be doing all the SQL for saving objects to the database
for the herd 2.x model.

No need for the indirection inserted by the "factories" idea.

"""

from db import m2_get_cursor as get_cursor
from psycopg2.extras import register_hstore
from uuid import uuid4


default = str(uuid4())

def save(cursor, table, unique_columns, columns, values, returning=default):
    """
    Save some values to a table if they don't conflict.

    return the id of the new row or the row that is already there.

    """

    assert type(table) == str
    assert type(unique_columns) == list
    assert type(columns) == list
    assert type(values) == tuple
    if returning is not default:
        assert type(returning) == str

    if returning == default:
        # by default save returns the id for the table
        # and assumes we are following OAO convention
        returning = '{}_id'.format(table)
    columns_str = ', '.join(columns)
    value_placeholders = ', '.join(['%s' for x in values])

    # if we are setting any columns that are under unique constraints
    unique_set_columns = [col for col in columns if col in unique_columns]
    if unique_set_columns:
        # we need to create an "on conflict (x) do update set (col = table.col)"
        # clause that performs a ghost update in order to 'activate' the
        # returning clause of the insert statement to get the id of the existing
        # row
        unique_set_column = unique_set_columns.pop()
        unique_column_str = ', '.join(unique_columns)
        set_str = "{} = {}.{}".format(
            unique_set_column,
            table,
            unique_set_column,
        )
        conflict_clause = "on conflict ({}) do update set {}\n".format(
            unique_column_str,
            set_str,
        )
    else:
        conflict_clause = ""

    insert_fmt = ("insert into {} ({})\n"
                  "     values ({})\n"
                  "{}"
                  "  returning {}")
    query = insert_fmt.format(
        table,
        columns_str,
        value_placeholders,
        conflict_clause,
        returning,
    )
    cursor.execute(query, values)
    return_value = cursor.fetchone()[0]
    return return_value


def correct_qa_config(cursor, branch_id, merge_base_commit_hash):
    """ Return the config_id to release a new commit to this build with """
    register_hstore(cursor)
    # if there are releases on this branch, use the config from the most recent
    # otherwise use the most recent release of the merge base commit
    cursor.execute(
        ("select config_id "
         "  from release "
         "  join iteration using (iteration_id) "
         " where branch_id=%s "
         "    or commit_hash=%s "
         " order by iteration.created_dt desc, release.created_dt desc "
         " limit 1 "),
        (branch_id, merge_base_commit_hash),
    )
    results = cursor.fetchall()
    if len(results) is 0:
        config_id = save(
            cursor,
            'config',               # table
            ['key_value_pairs'],    # unique columns
            ['key_value_pairs'],    # column
            ({},),                  # value
        )
    elif len(results) is 1:
        config_id = results[0][0]
    else:
        raise ValueError("There should only be one correct config")
    return config_id


def handle_build(service_name,
                 branch_name,
                 merge_base_commit_hash,
                 commit_hash,
                 image_name):
    """
    Save the data going into this build, then deploy the build

    Service, branch, commit and image are idempotently saved to the
    database.

    """

    cursor = get_cursor()
    service_id = save(
        cursor,
        'service',         # table name
        ['service_name'],  # unique columns
        ['service_name'],  # columns
        ( service_name,),  # values
    )
    branch_id = save(
        cursor,
        'branch',                                                # table
        ['branch_name', 'merge_base_commit_hash', 'deleted_dt'], # unique
        ['branch_name', 'merge_base_commit_hash', 'service_id'], # columns
        ( branch_name ,  merge_base_commit_hash ,  service_id ), # values
    )
    iteration_id = save(
        cursor,
        'iteration',                                  # table name
        ['commit_hash', 'branch_id'],                 # unique columns
        ['commit_hash', 'branch_id', 'image_name'],   # columns
        ( commit_hash ,  branch_id ,  image_name ),   # values
    )
    config_id = correct_qa_config(cursor, branch_id, merge_base_commit_hash)
    release_id = save(
        cursor,
        'release',                           # table name
        [],                                  # unique columns
        ['iteration_id', 'config_id'],       # columns
        ( iteration_id ,  config_id ),       # values
    )
    cursor.close()
