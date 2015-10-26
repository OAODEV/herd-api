from config_finder import cfg

import psycopg2
import psycopg2.extensions


connection = psycopg2.connect(
    host=cfg('pghost', None),
    port=cfg('pgport', '5433'),
    dbname=cfg('pgdatabase', 'herd'),
    user=cfg('pguser', None),
    password=cfg('pgpassword', None),
)


class PoliteCursor(psycopg2.extensions.cursor):
    def execute(self, sql, args):
        try:
            print("executing sql ({}) with args ({})".format(sql, args))
            psycopg2.extensions.cursor.execute(self, sql, args)
        except Exception e:
            print("Error executing sql, {}".format(e.message))
            self.close()
            self.connection.rollback()
            raise e

    def close(self):
        self.close()
        self.connection.commit()


def get_cursor():
    return connection.cursor(cursor_factory=PoliteCursor)
