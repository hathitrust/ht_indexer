import os
import json
import argparse

from document_generator.document_generator_service import DocumentGeneratorService
from indexer_config import DOCUMENT_LOCAL_PATH
from document_generator.generator_arguments import get_mysql_conn

from ht_utils.ht_logger import get_ht_logger

logger = get_ht_logger(name=__name__)


class DocumentGeneratorServiceLocal(DocumentGeneratorService):
    def __init__(self, db_conn, src_queue_name: str = 'retriever_queue', src_queue_host: str = None,
                 src_queue_user: str = None,
                 src_queue_password: str = None, src_channel_name: str = "retriever", document_repository: str = None,
                 document_local_folder: str = "indexing_data", document_local_path: str = DOCUMENT_LOCAL_PATH,
                 required_tgt_queue: bool = True):
        """
        This class is responsible to retrieve from the queue a message with metadata at item level and generate
        the full text search entry and publish the document in a local folder

        :param db_conn: Mysql connection
        :param src_queue_name: Name of the queue to read the messages
        :param src_queue_host: Host of the queue to read the messages
        :param src_queue_user: User of the queue to read the messages
        :param src_queue_password: Password of the queue to read the messages
        :param src_channel_name: Name of the channel

        :param document_repository: Parameter to know if the plain text of the items is in the local or remote repository
        """

        super().__init__(db_conn, src_queue_name=src_queue_name, src_queue_host=src_queue_host,
                         src_queue_user=src_queue_user,
                         src_queue_password=src_queue_password, src_channel_name=src_channel_name,
                         tgt_queue_name='', tgt_queue_host='', tgt_queue_user=None,
                         tgt_queue_password=None, tgt_channel_name='', document_repository=document_repository,
                         required_tgt_queue=required_tgt_queue
                         )

        self.document_local_folder = document_local_folder
        self.document_local_path = document_local_path

        # Create the directory to load the JSON files if it does not exit
        try:
            if self.document_local_path:
                document_local_path = os.path.abspath(self.document_local_path)
            os.makedirs(os.path.join(document_local_path, document_local_folder))
        except FileExistsError:
            pass

    def publish_document(self, content: dict = None):
        """
        Right now, the entry is saved in a file and, but it could be published in a queue
        """
        file_name = content.get('id')

        file_path = f"{os.path.join(self.document_local_path, self.document_local_folder)}/{file_name}.json"
        with open(file_path, "w") as f:
            json.dump(content, f)
        logger.info(f"File {file_name} created in {file_path}")


def main():
    """ This script will process the remaining documents in the queue and generate the full-text search documents in
    a local computer. Each stage is process in sequence."""

    # 1. Retrieve the documents from the queue AND # 2. Generate the full text search entry AND
    # 3. Publish the document in a local folder

    parser = argparse.ArgumentParser()

    parser.add_argument("--document_repository",
                        help="Could be pairtree or local", default="local"
                        )

    # Path to the folder where the documents are stored. This parameter is useful for runing the script locally
    parser.add_argument("--document_local_path",
                        help="Path of the folder where the documents (.xml file to index) are stored.",
                        required=False,
                        default=None
                        )

    args = parser.parse_args()

    # MySql connection
    db_conn = get_mysql_conn()

    # Generate full-text search document in a local folder
    document_generator_service = DocumentGeneratorServiceLocal(db_conn,
                                                               os.environ["SRC_QUEUE_NAME"],
                                                               os.environ["SRC_QUEUE_HOST"],
                                                               os.environ["SRC_QUEUE_USER"],
                                                               os.environ["SRC_QUEUE_PASS"],
                                                               'retriever',
                                                               args.document_repository,
                                                               document_local_folder="indexing_data",
                                                               document_local_path=args.document_local_path,
                                                               required_tgt_queue=False)
    document_generator_service.generate_document()


if __name__ == "__main__":
    main()
