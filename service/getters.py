from uuid import uuid4

from db import get_cursor
import lense

def make_getter(table_name, key, values='*'):
    """ return a getter that looks for values in a table by a key """

    default = uuid4()
    def getter(__val__=default, **kwargs):
        """
        return the values in the key passed to the factory

        a single keyword argument may be passed to specify an alternate key

        >>> getter(x)
        # looks for key=x where key was passed to make_getter

        >>> getter(myKey=y)
        # looks for myKey=y

        """

        # we need either a single kwarg telling us the key(override) and the value
        if len(kwargs) == 1:
            __key__ = list(kwargs.keys())[0]
            __val__ = kwargs[__key__]
        # or we need to be passed a value for this getter's default key
        else:
            if __val__ == default:
                raise LookupError("please provide a value to look for")
            __key__ = key

        sql_template = "SELECT {values} FROM {table_name} WHERE {key}=%s"
        sql = sql_template.format(
            table_name=table_name,
            values=values,
            key=__key__,
        )
        cursor = get_cursor()
        cursor.execute(sql, (__val__,))
        row_dict = dict(zip(lense.fst(cursor.description), cursor.fetchone()))
        cursor.close()
        return row_dict

    getter.__name__ = "{}_{}_getter".format(table_name, key)
    return getter

get_iteration = make_getter("iteration", "iteration_id")
get_config = make_getter("config", "config_id")
get_env = make_getter("environment", "environment_id")
