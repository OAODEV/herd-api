from db import get_cursor

def release_in_automatic_pipelines(iteration_id):
    """ Release an iteration in all it's automatic pipelines """
    cursor = get_cursor()
    cursor.execute(
        "INSERT INTO release (iteration_id, deployment_pipeline_id)\n" + \
        "SELECT iteration_id, deployment_pipeline_id\n" + \
        "  FROM iteration\n" + \
        "  JOIN branch USING (branch_id)\n" + \
        "  JOIN deployment_pipeline USING (branch_id)\n" + \
        "where iteration_id = %s",
        (123,),
    )
    cursor.close()



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
