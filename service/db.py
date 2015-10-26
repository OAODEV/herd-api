from config_finder import cfg

import psycopg2
import psycopg2.extensions




class PoliteCursor(psycopg2.extensions.cursor):
    def execute(self, sql, args):
        try:
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

connection = None
def get_cursor(connection=connection):
    if connection is None:
        connection = psycopg2.connect(
            host=cfg('pghost', None),
            port=cfg('pgport', '5433'),
            dbname=cfg('pgdatabase', 'herd'),
            user=cfg('pguser', None),
            password=cfg('pgpassword', None),
        )
    return connection.cursor(cursor_factory=PoliteCursor)
