"""
Handlers will be doing all the SQL for saving objects to the database
for the herd 2.x model.

No need for the indirection inserted by the "factories" idea.

"""

from db import m2_get_cursor as get_cursor
from uuid import uuid4


default = str(uuid4())

def save(cursor, table, unique_columns, columns, values, returning=default):
    """
    Save some values to a table if they don't conflict.

    return the id of the new row or the row that is already there. 

    """

    if returning == default:
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

    insert_fmt = "insert into {} ({})\n" + \
                 "     values ({})\n" + \
                 "{}" + \  # may or may not have an on conflict do update clause
                 "  returning {}"
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


def handle_build(service_name, branch_name, commit_hash, image_name):
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
        ['service_name'],  # all columns
        ( service_name,),  # values to insert
    )
    branch_id = save(
        cursor,
        'branch',                         # table name
        ['branch_name', 'service_id'],    # unique columns
        ['branch_name', 'service_id'],    # all columns
        ( branch_name ,  service_id ),    # values to insert
    )
    iteration_id = save(
        cursor,
        'iteration',                                  # table name
        ['commit_hash', 'branch_id'],                 # unique columns
        ['commit_hash', 'branch_id', 'image_name'],   # all columns
        ( commit_hash ,  branch_id ,  image_name ),   # values to insert
    )
    cursor.close()
