import glob
from pathlib import Path
from typing import Text

import requests

from ht_utils.ht_logger import get_ht_logger

logger = get_ht_logger(name=__name__)


class HTSolrAPI:
    def __init__(self, url):
        self.url = url

    def get_solr_status(self):
        response = requests.get(self.url)
        return response

    def index_document(self, path: Text):
        """Read an XML and feed into SOLR for indexing"""
        data_path = Path(path)  # Path(f"{os.path.dirname(__file__)}/{path}")
        list_documents = glob.glob(f"{data_path}/*.xml")
        for doc in list_documents:
            doc = doc.replace(" ", "+")
            logger.info(f"Indexing {doc}")
            with open(doc, "rb") as xml_file:
                data_dict = xml_file.read()
                response = requests.post(
                    f"{self.url.replace('#/', '')}update/?commit=true",
                    headers={"Content-Type": "application/xml"},
                    data=data_dict,
                    params={
                        "commit": "true",
                    },
                )

        return response

    def get_documents(
        self,
        query: str = None,
        response_format: Text = "json",
        start: int = 0,
        rows: int = 100,
    ):
        data_query = {"q": "*:*"}
        if query:
            data_query["q"] = query
        else:
            data_query = {"q": "*:*"}

        data_query.update({"start": start, "rows": rows})

        solr_headers = {"Content-type": "application/json"}

        response = requests.post(
            f"{self.url.replace('#/', '')}query",
            params=data_query,
            headers=solr_headers,
        )

        return response
