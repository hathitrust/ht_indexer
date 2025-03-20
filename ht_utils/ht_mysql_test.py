from unittest.mock import Mock, patch
from ht_utils.ht_mysql import HtMysql

class TestHtMysql:

    @patch('ht_utils.ht_mysql.mysql.connector.connect')
    def test_create_table(self, mock_connect):
        # Mock the database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # SQL statement to create a table
        create_table_sql = """
        CREATE TABLE test_table (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            message VARCHAR(255) UNIQUE NOT NULL,
            status ENUM('pending', 'processing', 'failed', 'completed', 'requeued') NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        # Create an instance of HtMysql and call the create_table method
        ht_mysql = HtMysql(host='localhost', user='user', password='password', database='test_db')
        ht_mysql.create_table(create_table_sql)

        # Assert that the cursor's execute method was called with the correct SQL statement
        mock_cursor.execute.assert_called_once_with(create_table_sql)
        # Assert that the connection's commit method was called
        mock_conn.commit.assert_called_once()

    @patch('ht_utils.ht_mysql.mysql.connector.connect')
    def test_table_exits(self, mock_connect):
        # Mock the database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock the result of the SHOW TABLES query
        mock_cursor.fetchone.return_value = ('test_table',)

        # Create an instance of HtMysql and call the table_exists method
        ht_mysql = HtMysql(host='localhost', user='user', password='password', database='test_db')
        table_name = 'test_table'
        result = ht_mysql.table_exists(table_name)

        # Assert that the cursor's execute method was called with the correct SQL statement
        mock_cursor.execute.assert_called_once_with(f"SHOW TABLES LIKE '{table_name}'")
        # Assert that the result is True
        assert result is True