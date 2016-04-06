from config_finder import cfg

import psycopg2
import psycopg2.extensions


class PoliteCursor(psycopg2.extensions.cursor):
    def execute(self, sql, args=None, print_sql=False):
        try:
            if print_sql:
                print("executing sql ({}) with args ({})".format(sql, args))
            psycopg2.extensions.cursor.execute(self, sql, args)
        except Exception as e:
            print("Error executing sql, {}".format(e))
            self.close()
            self.connection.rollback()
            raise e

    def close(self):
        super().close()
        self.connection.commit()


def m2_get_cursor():
    connection = psycopg2.connect(
        # Model version 2 cursor is configured with dashes in keys
        host=cfg(    'pg-host',     'herd-postgres'),
        port=cfg(    'pg-port',     '5433'),
        dbname=cfg(  'pg-database', 'herd'),
        user=cfg(    'pg-user',     'herd_user'),
        password=cfg('pg-password',  None),
    )
    return connection.cursor(cursor_factory=PoliteCursor)


def get_cursor(connection=None):
    if connection is None:
        connection = psycopg2.connect(
            host=cfg('pghost', 'api-postgres'),
            port=cfg('pgport', '5433'),
            dbname=cfg('pgdatabase', 'herd'),
            user=cfg('pguser', None),
            password=cfg('pgpassword', None),
        )
    return connection.cursor(cursor_factory=PoliteCursor)

