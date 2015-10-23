from config_finder import cfg

import psycopg2

connection = None
def get_cursor():
    global connection
    if not connection:
        connection = psycopg2.connect(
            host=cfg('pghost', None),
            port=cfg('pgport', '5433'),
            dbname=cfg('pgdatabase', 'herd'),
            user=cfg('pguser', None),
            password=cfg('pgpassword', None),
        )
    return connection.cursor()
