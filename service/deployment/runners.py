from functools import singledispatch
from db import get_cursor

from deployment.constants import actions
from deployment import gce

class Runners(object):

    def __init__(self, runners=[]):
        self.__all__ = runners

    def all(self):
        return self.__all__

    def register(self, runner):
        self.__all__.append(runner)


runners = Runners()
runners.register(gce.runner)

# overload the run function.
# default to an error when called with unimplemented types
@singledispatch
def run(*args, **kwargs):
    """ the default run should not raise an error showing the allowed types """
    raise TypeError(
        "run may be called with the following types {}. got {}".format(
            list(run.registry.keys()),
            str(args) + str(kwargs),
        )
    )

# int (release_id) implementeation
@run.register(int)
def run_int(release_id):
    """ give a release request to all the runners """
    for runner in runners.all():
        runner({
            "release_id": release_id,
            "action": actions.UPDATE
        })

# list implementation
run.register(list, lambda ids: list(map(run, ids)))
"""
Lift the run function into the list domain

This makes `run` (which accepts a single int) also accept lists of ints
by mapping run over the list it is given (when it's given a list)

Don't implement collections.Iterable because that could lead to
unexpected results

run({'1': 2, '3': 4}) would end up calling run on all keys and values
through the tuple implementation which doesn't seem all that clear.

"""

# tuple implementation
run.register(tuple, lambda ids: list(map(run, ids)))

# string implementation
@run.register(str)
def run_string(release_id):
    """ convert to int then run """
    return run(int(release_id))
