"""
Models

config = Config([(k, v)])
env = Environment('qa-sandbox', [(k, v)])

Service('your-project')
    .branch('feature_new')
    .iteration('abcdef12345', build_name='x/project:latest')
    .release(config)
    .deploy()

"""

from db import get_cursor
from uuid import uuid4

default = str(uuid4())

def represent(table,
              columns,
              values,
              on_conflict='DO NOTHING',
              returning=default):
    cursor = get_cursor()
    if returning == default:
        returning = '{}_id'.format(table)
    column_str = ', '.join(columns)
    value_placeholders = ', '.join(['%s' for x in values])
    cursor.execute(
        "INSERT INTO {} ({})\n" + \
        "     VALUES ({})\n" + \
        "ON CONFLICT {}\n" + \
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
    cursor.close()
    return return_value


class Service:

    def __init__(self, service_name):
        self.service_id = represent('service', ['service_name'], [service_name])

    def branch(self, branch_name):
        return Branch(branch_name, self)


class Branch:

    def __init__(self, branch_name, service):
        self.branch_id = represent(
            'branch',
            ['branch_name', 'service_id'],
            [branch_name, service.service_id],
        )

    def iteration(self, commit_hash):
        return Iteration(commit_hash, self)


class Iteration:

    def __init__(self, commit_hash, branch, image_name=None):
        self.iteration_id = represent(
            'iteration',
            ['commit_hash', 'branch_id', 'image_name'],
            [commit_hash, branch.branch_id, image_name],
            on_conflict='DO UPDATE',
        )

    def release(self, config=None):
        """
        Release this iteration with this config.

        Default config to the most recent config used in a release under
        this branch or the null config.

        """

        if config is None:
            # find correct config
            pass

        return Release(self, config)


class Release:

    def __init__(self, iteration, config):
        self.release_id = represent(
            'release',
            ['iteration_id', 'config_id'],
            [iteration.iteration_id, config.config_id],
        )

    def deploy(self):
        pass


class Config:

    def __init__(self, kvpairs={}, config_id=None):

        if kvpairs and config_id:
            raise TypeError(
                'Config must be passed kvpairs or a config_id but not both'
            )

        if kvpairs:
            key_value_pairs = '\n'.join([
                '{}={}'.format(k, v)
                for k, v
                in kvpairs.items()
            ])
            self.config_id = represent(
                'config',
                ['key_value_pairs'],
                [key_value_pairs],
            )
        elif config_id:
            self.config_id = represent(
                'config',
                ['config_id'],
                [config_id],
            )
        else:
            raise TypeError(
                'Config must be passed kvpairs or a config_id but not both'
            )

