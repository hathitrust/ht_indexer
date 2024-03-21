import os
import sys

from ht_utils.ht_logger import get_ht_logger
import ht_utils.ht_mysql

logger = get_ht_logger(name=__name__)


def get_mysql_conn():
    # MySql connection
    try:
        mysql_host = os.getenv("MYSQL_HOST", "mysql-sdr")  # os.environ["MYSQL_HOST"]
    except KeyError:
        logger.error("Error: `MYSQL_HOST` environment variable required")
        sys.exit(1)

    try:
        mysql_user = os.getenv("MYSQL_USER", "mdp-lib")  # os.environ["MYSQL_USER"]
    except KeyError:
        logger.error("Error: `MYSQL_USER` environment variable required")
        sys.exit(1)

    try:
        mysql_pass = os.getenv("MYSQL_PASS", "mdp-lib")  # os.environ["MYSQL_PASS"]
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


class GeneratorServiceArguments:

    def __init__(self, parser):
        self.src_channel_name = None
        parser.add_argument("--document_repository",
                            help="Could be pairtree or local", default="local"
                            )

        # Path to the folder where the documents are stored. This parameter is useful for runing the script locally
        parser.add_argument("--document_local_path",
                            help="Path of the folder where the documents (.xml file to index) are stored.",
                            required=False,
                            default=None
                            )

        self.args = parser.parse_args()

        # MySql connection
        self.db_conn = get_mysql_conn()

        # Using queue or local machine
        self.src_queue_name = os.environ["SRC_QUEUE_NAME"]
        self.src_queue_host = os.environ["SRC_QUEUE_HOST"]
        self.src_queue_user = os.environ["SRC_QUEUE_USER"]
        self.src_queue_password = os.environ["SRC_QUEUE_PASS"]

        # Using queue or local machine
        self.tgt_queue_name = os.environ["TGT_QUEUE_NAME"]
        self.tgt_queue_host = os.environ["TGT_QUEUE_HOST"]
        self.tgt_queue_user = os.environ["TGT_QUEUE_USER"]
        self.tgt_queue_password = os.environ["TGT_QUEUE_PASS"]

        self.document_repository = self.args.document_repository

        self.document_local_path = self.args.document_local_path
