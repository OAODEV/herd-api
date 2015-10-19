import os
import uuid

"""
NO_DEFAULT is an unguessable value identifying the case that nothing was passed
in for the default return.

given that it's unguessable, if we see this value we can be confident that it
was not passed in by client code.
"""
NO_DEFAULT = uuid.uuid4()


def cfg(key, default=NO_DEFAULT):
    """
    checks a number of spots for a configuration value.

    If it can't find it anywhere and there is no default there is an error

    It checks three spots.
    first
      os.environ[key]
    second
      the contents of a file at /secret/<key>
    third
      the first line containing <key>=<value>\n in a file at /env

    """

    def default_return():
        """ given we can't find a key, return the default or raise an error """

    # check the first spot (os.environ)
    try:
        return os.environ[key]
    except KeyError:
        pass

    # check the second spot (/secret/<key>)
    try:
        with open("/secret/{}".format(key), "r") as cfile:
            return cfile.read().strip()
    except EnvironmentError:
        pass

    # check the third spot (some line in the file at /env)
    try:
        with open("/env", 'r') as envfile:
            for line in envfile.readlines():
                k, v = line.split('=')
                if k == key:
                    return v.strip()
    except EnvironmentError:
        pass

    # couldnt find the key, if there was a default passed, raise Error
    if default is NO_DEFAULT:
        raise KeyError(
            "config_finder.cfg could not find the key '{}'".format(key)
        )
    # otherwise return the default that was passed
    else:
        return default
