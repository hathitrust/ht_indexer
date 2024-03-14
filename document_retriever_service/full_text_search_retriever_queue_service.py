import argparse
import inspect
import os
import sys
import time

from document_generator.document_generator import DocumentGenerator
from ht_utils.ht_logger import get_ht_logger
from full_text_search_retriever_service import FullTextSearchRetrieverService
from ht_queue_service.queue_producer import QueueProducer
from ht_indexer_api.ht_indexer_api import HTSolrAPI
import ht_utils.ht_mysql

logger = get_ht_logger(name=__name__)

current = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent = os.path.dirname(current)
sys.path.insert(0, parent)


class FullTextSearchRetrieverQueueService(FullTextSearchRetrieverService):
    """
    This class is responsible to retrieve the documents from the Catalog and generate the full text search entry
    There are three main use cases:
        1- Retrieve all the items of a record in the Catalog - the query will contain the id of the record
        2- Retrieve a specific item of a record in the Catalog - the query will contain the ht_id of the item
        3- Retrieve all the items of all the records in the Catalog - the query will be *:*
    By default, the query is None, then an error will be raised if the query is not provided
    All the entries are published in a queue
    """

    def __init__(self, catalog_api=None,
                 document_generator_obj: DocumentGenerator = None,
                 queue_name: str = None, queue_host: str = None, queue_user: str = None, queue_password: str = None):

        super().__init__(catalog_api, document_generator_obj, None, None)

        self.queue_producer = QueueProducer(queue_user, queue_password, queue_host,
                                            queue_name, "retriever")

    def publish_document(self, file_name: str = None, content: dict = None):

        """
        Publish the document in a queue
        """
        message = content
        self.queue_producer.publish_messages(message)

    def full_text_search_retriever_service(self, query, start, rows, document_repository):
        """
        This method is used to retrieve the documents from the Catalog and generate the full text search entry
        """
        count = 0
        for result in self.retrieve_documents(query, start, rows):
            for record in result:

                item_id = record.ht_id
                logger.info(f"Processing document {item_id}")

                try:
                    self.generate_full_text_entry(item_id, record, document_repository)
                except Exception as e:
                    logger.error(f"Document {item_id} failed {e}")
                    continue
            count += len(result)
            logger.info(f"Total of processed items {count}")


def main():
    parser = argparse.ArgumentParser()

    # Using queue or local machine
    queue_name = os.environ["QUEUE_NAME"]
    queue_host = os.environ["QUEUE_HOST"]
    queue_user = os.environ["QUEUE_USER"]
    queue_password = os.environ["QUEUE_PASS"]

    # Catalog Solr server
    try:
        solr_url = os.environ["SOLR_URL"]
    except KeyError:
        logger.error("Error: `SOLR_URL` environment variable required")
        sys.exit(1)

    solr_api_catalog = HTSolrAPI(url=solr_url)

    # MySql connection
    try:
        mysql_host = os.environ["MYSQL_HOST"]
    except KeyError:
        logger.error("Error: `MYSQL_HOST` environment variable required")
        sys.exit(1)

    try:
        mysql_user = os.environ["MYSQL_USER"]
    except KeyError:
        logger.error("Error: `MYSQL_USER` environment variable required")
        sys.exit(1)

    try:
        mysql_pass = os.environ["MYSQL_PASS"]
    except KeyError:
        logger.error("Error: `MYSQL_PASS` environment variable required")
        sys.exit(1)

    ht_mysql = ht_utils.ht_mysql.HtMysql(
        host=mysql_host,
        user=mysql_user,
        password=mysql_pass,
        database=os.environ.get("MYSQL_DATABASE", "ht")
    )

    logger.info("Access by default to `ht` Mysql database")

    parser.add_argument("--query", help="Query used to retrieve documents", default=None
                        )

    parser.add_argument("--document_repository",
                        help="Could be pairtree or local", default="local"
                        )

    args = parser.parse_args()

    document_generator = DocumentGenerator(ht_mysql)

    document_indexer_service = FullTextSearchRetrieverQueueService(solr_api_catalog, document_generator, queue_name,
                                                                   queue_host,
                                                                   queue_user, queue_password)

    if args.query is None:
        logger.error("Error: `query` parameter required")
        sys.exit(1)

    # TODO: Add start and rows to a configuration file
    start = 0
    rows = 100

    start_time = time.time()

    document_indexer_service.full_text_search_retriever_service(
        args.query,
        start,
        rows,
        document_repository=args.document_repository)

    logger.info(f"Total time to retrieve and generate documents {time.time() - start_time:.10f}")


if __name__ == "__main__":
    main()
