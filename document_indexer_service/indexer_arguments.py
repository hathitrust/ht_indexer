import os
from ht_indexer_api.ht_indexer_api import HTSolrAPI


class IndexerServiceArguments:

    def __init__(self, parser):
        self.src_channel_name = None
        # Using queue or local machine
        self.queue_name = os.environ["QUEUE_NAME"]
        self.queue_host = os.environ["QUEUE_HOST"]
        self.queue_user = os.environ["QUEUE_USER"]
        self.queue_password = os.environ["QUEUE_PASS"]

        parser.add_argument(
            "--solr_indexing_api",
            help="",
            required=True,
            default="http://solr-lss-dev:8983/solr/#/core-x/",
        )

        # Path to the folder where the documents are stored. This parameter is useful for running the script locally
        parser.add_argument(
            "--document_local_path",
            help="Path of the folder where the documents are stored.",
            required=False,
            default=None
        )

        self.args = parser.parse_args()

        self.solr_api_full_text = HTSolrAPI(url=self.args.solr_indexing_api)

        self.document_local_path = self.args.document_local_path
