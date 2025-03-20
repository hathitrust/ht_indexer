import mysql.connector
import ht_utils.ht_utils
import sys
import os

from ht_utils.ht_logger import get_ht_logger

logger = get_ht_logger(name=__name__)

def get_mysql_conn():
    # MySql connection
    try:
        mysql_host = os.getenv("MYSQL_HOST", "mysql-sdr")
        logger.info(f"Connected to MySql_Host: {mysql_host}")
    except KeyError:
        logger.error("Error: `MYSQL_HOST` environment variable required")
        sys.exit(1)

    try:
        mysql_user = os.getenv("MYSQL_USER", "mdp-lib")
    except KeyError:
        logger.error("Error: `MYSQL_USER` environment variable required")
        sys.exit(1)

    try:
        mysql_pass = os.getenv("MYSQL_PASS", "mdp-lib")
    except KeyError:
        logger.error("Error: `MYSQL_PASS` environment variable required")
        sys.exit(1)

    ht_mysql = ht_utils.ht_mysql.HtMysql(
        host=mysql_host,
        user=mysql_user,
        password=mysql_pass,
        database=os.getenv("MYSQL_DATABASE", "ht")
    )

    logger.info("Access by default to `ht` Mysql database")

    return ht_mysql



class HtMysql:

    def __init__(self, host: str = None, user: str = None, password: str = None, database: str = None):
        self.db_conn = HtMysql.create_mysql_conn(host=host, user=user, password=password, database=database)

    @staticmethod
    def create_mysql_conn(host: str = None, user: str = None, password: str = None, database: str = None):
        if not all([host, user, password, database]):
            logger.error("Please pass the valid host, user, password and database")
            sys.exit(1)
        try:
            conn = mysql.connector.connect(host=host, user=user, password=password, database=database)
            return conn
        except mysql.connector.Error as e:
            logger.error(f"MySQL Connection Error: "
                         f"{ht_utils.ht_utils.get_general_error_message('DatabaseConnection', e)}")
            sys.exit(1)

    def query_mysql(self, query: str = None) -> list:
        cursor = self.db_conn.cursor()
        cursor.execute(query)

        results = cursor.fetchall()

        list_docs = []
        for row in results:
            doc = {}
            for name, value in zip(cursor.description, row):
                doc.update({name[0]: value})
            list_docs.append(doc)

        return list_docs

    def table_exists(self, table_name: str) -> bool:
        cursor = self.db_conn.cursor()
        try:
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            result = cursor.fetchone()
            return result is not None
        except mysql.connector.Error as e:
            logger.error(f"Error checking if table exists: {e}")
        finally:
            cursor.close()

    def insert_batch(self, insert_query: str, batch_values: list):
        cursor = self.db_conn.cursor()
        try:
            cursor.executemany(insert_query, batch_values)
            self.db_conn.commit()
            logger.info(f"Inserted {len(batch_values)} records successfully.")
        except mysql.connector.Error as e:
            logger.error(f"Error inserting batch of records: {e}")
            self.db_conn.rollback()
        finally:
            cursor.close()

    def create_table(self, create_table_sql: str):
        cursor = self.db_conn.cursor()
        try:
            cursor.execute(create_table_sql)
            self.db_conn.commit()
            logger.info("Table created successfully")
        except mysql.connector.Error as e:
            logger.error(f"Failed to create table: {e}")
            self.db_conn.rollback()
        finally:
            cursor.close()