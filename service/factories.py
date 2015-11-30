from db import get_cursor
from functools import partial
from getters import (
    get_env,
    get_config,
)

def idem_maker(table_name, pk, keys, on_create_callback=lambda x: None):
    """ Return an idempotent maker function for the table and keys """
    def idem_maker(*value_args, **value_kwargs):
        """ Idempotently create an object """
        # there should not be more values than keys
        if len(value_args) > len(keys):
            message = "Cannot match values to keys. "
            message += "Got ({}) as values for the keys ({})".format(
                ', '.join(value_args),
                ', '.join(keys),
            )
            raise ValueError(message)

        # for every key missing a value, there should be an entry in value_kwargs
        missing_values = []
        for k in keys[len(value_args):]:
            if k not in value_kwargs:
                missing_values.append(k)
        if missing_values:
            message = "Missing values for keys ({})".format(
                ', '.join(missing_values)
            )
            raise ValueError(message)

        # associate the keys and values passed as args
        kv_dict = dict(zip(keys, value_args))
        # use value_kwargs to override and fill in everything else
        kv_dict.update(value_kwargs)
        # put these in a sorted consistantly orderd state (for testability)
        __keys__ = list(sorted(kv_dict.keys()))
        __vals__ = [kv_dict[k] for k in __keys__]

        # check if the object is already in the database
        cursor = get_cursor()
        # string for the WHERE clause key=%s, key2=%s ...
        matches = ' AND '.join(["{}=%s".format(k) for k in __keys__])
        cursor.execute(
            "SELECT {pk} FROM {table_name} WHERE {matches}".format(
                pk=pk,
                table_name=table_name,
                matches=matches,
            ),
            tuple(__vals__),
        )
        if cursor.rowcount > 0:
            object_id = cursor.fetchone()[0]
            cursor.close()
        else:
            # columns for the insert statement column, column2, colu...
            columns = ', '.join(__keys__)
            # a %s for each pair %s, %s, %s...
            value_placeholders = ', '.join(['%s' for k in __keys__])
            sql_template = "INSERT INTO {table_name} ({columns}) " + \
                "VALUES ({vals}) " + \
                "RETURNING {pk}"
            cursor.execute(
                sql_template.format(
                    table_name=table_name,
                    columns=columns,
                    vals=value_placeholders,
                    pk=pk,
                ),
                tuple(__vals__),
            )
            object_id = cursor.fetchone()[0]
            cursor.close()
            on_create_callback(object_id)

        return object_id

    idem_maker.__name__ = "{}_{}_maker".format(table_name, pk)
    return idem_maker

def new_deployment_pipeline(
        branch_id,
        copy_config_id=None,
        copy_env_id=None,
        automatic=False,
):
    """
    Make a new deployment pipeline from a branch

    Will create new config and environments as copies of the given config
    and environments, or use a unit config and environment.

    """

    # make config
    config_id = new_config(copy_config_id)

    # make env
    env_id = new_env(copy_env_id)

    # insert record
    cursor = get_cursor()
    cursor.execute(
        "INSERT INTO deployment_pipeline " + \
        "(branch_id, config_id, environment_id, automatic) " + \
        "VALUES (%s, %s, %s, %s) " + \
        "RETURNING deployment_pipeline_id",
        (branch_id, config_id, env_id, automatic),
    )
    deployment_pipeline_id = cursor.fetchone()[0]
    cursor.close()
    return deployment_pipeline_id

def new_config(based_on_id=None):
    """ Make a new config based on the given config or an empty one """
    if based_on_id:
        based_on_config = get_config(based_on_id)
        key_value_pairs_text = based_on_config['key_value_pairs']
    else:
        key_value_pairs_text = ''

    cursor = get_cursor()
    cursor.execute(
        "INSERT INTO config (key_value_pairs) VALUES (%s) RETURNING config_id",
        (key_value_pairs_text,),
    )
    config_id = cursor.fetchone()[0]
    cursor.close()
    return config_id

def new_env(based_on_id=None):
    """ Make a new environment based on the given config or an empty one """
    if based_on_id:
        based_on_env = get_env(based_on_id)
        settings_value = based_on_env['settings']
    else:
        settings_value = ''

    cursor = get_cursor()
    cursor.execute(
        "INSERT INTO environment (settings) VALUES (%s) RETURNING environment_id",
        (settings_value,),
    )
    env_id = cursor.fetchone()[0]
    cursor.close()
    return env_id

def idem_release_in_automatic_pipelines(iteration_id):
    """
    Idempotently release an iteration in all it's automatic pipelines

    The idempotency is gained by a uniqueness constraint in the database
    on the (iteration_id, deployment_pipeline_id) pair.

    only the first insert can happen without a conflict (which we will need to
    catch and do nothing).

    when we are on postgres 9.5 we can do this with "ON CONFLICT DO NOTHING"

    """

    cursor = get_cursor()
    try:
        cursor.execute(
            "INSERT INTO release (iteration_id, deployment_pipeline_id)\n" + \
            "     SELECT iteration_id, deployment_pipeline_id\n" + \
            "       FROM iteration\n" + \
            "       JOIN branch USING (branch_id)\n" + \
            "       JOIN deployment_pipeline USING (branch_id)\n" + \
            "      WHERE iteration_id = %s\n" + \
            "  RETURNING release_id",
            (123,),
        )
    except:
        pass
    release_ids = cursor.fetchall()
    cursor.close()
    return release_ids

idem_make_service = idem_maker(
    'service',
    'service_id',
    ['service_name'],
)
idem_make_feature = idem_maker(
    'feature',
    'feature_id',
    ['feature_name', 'service_id'],
)
new_auto_deployment_pipeline = partial(new_deployment_pipeline, automatic=True)
idem_make_branch = idem_maker(
    'branch',
    'branch_id',
    ['branch_name', 'feature_id'],
    new_auto_deployment_pipeline,
)
idem_make_iteration = idem_maker(
    'iteration',
    'iteration_id',
    ['commit_hash', 'branch_id'],
)
