from unittest.mock import Mock
connection = Mock()

def get_cursor():
    return connection.cursor()
