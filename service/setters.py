from db import get_cursor

def set_iteration(iteration_id, updates):
    """ Make updates to an iteration """
    cursor = get_cursor()

    sql_set_strings = []
    sql_values = []
    for k, v in sorted(dict(updates).items()):
        sql_set_strings.append("{}=%s".format(k))
        sql_values.append(v)

    set_string = ','.join(sql_set_strings)
    sql_values.append(iteration_id)
    cursor.execute(
        "UPDATE iteration " + \
        "SET {} ".format(set_string) + \
        "WHERE iteration_id=%s",
        tuple(sql_values),
    )
    cursor.close()
