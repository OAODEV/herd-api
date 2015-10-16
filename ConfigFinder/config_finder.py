import os


NO_DEFAULT = uuid.uuid4()
def config_val(key, default=NO_DEFAULT):
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

    # check the first spot (os.environ)
    try:
        return os.environ[key]
    except KeyError:
        pass

    # check the second spot (/secret/<key>)
    try:
        with open("/secret/{}".format(key), "r") as cfile:
            return cfile.read()
    except EnvironmentError:
        pass

    # check the third spot (some line in the file at /env)
    try:
        with open("/env", 'r') as envfile:
            for line in envfile.readlines():
                k, v = line.split('=')
                if k == key:
                    return v
    except EnvironmentError:
        if default is NO_DEFAULT:
            raise Exception("could not find config for key {}".format(key))
        else:
            return default
