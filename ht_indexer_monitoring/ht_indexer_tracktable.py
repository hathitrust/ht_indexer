import argparse
import inspect
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Any, Generator

from ht_full_text_search.export_all_results import SolrExporter

from ht_indexer_monitoring.monitoring_arguments import MonitoringServiceArguments
from ht_utils.ht_logger import get_ht_logger
from ht_utils.ht_mysql import HtMysql, get_mysql_conn

current = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent = os.path.dirname(current)
sys.path.insert(0, parent)

logger = get_ht_logger(name=__name__)

def create_ht_indexer_track_data():

    # Read the list of IDs from the file
    with open('/'.join([parent, 'document_retriever_service/list_htids_indexer_test.txt']), 'r') as file:
        ids = file.read().splitlines()

    # Create a JSON structure
    data = []
    for idx, ht_id in enumerate(ids, start=1):
        record = {
            "ht_id": ht_id,
            "record_id": f"record_{ht_id}",
            "status": "pending",
            "retriever_status": "pending",
            "generator_status": "pending",
            "indexer_status": "pending",
            "retriever_error": None,
            "generator_error": None,
            "indexer_error": None,
            "created_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "updated_at": None,
            "processed_at": None
        }
        data.append(HTIndexerTrackData(ht_id=record['ht_id'], record_id=record['record_id'], status=record['status']))

    # Write the JSON structure to a file
    #with open('ht_indexer_monitoring.json', 'w') as json_file:
    #    json.dump(data, json_file, indent=4)
    return data

@dataclass
class HTIndexerTrackData:
    """Data class to represent a row of the ht_indexer_tracktable table"""
    record_id: str
    ht_id: str
    status: str = 'pending'
    retriever_status: str = 'pending'
    generator_status: str = 'pending'
    indexer_status: str = 'pending'
    retriever_error: Optional[str] = None
    generator_error: Optional[str] = None
    indexer_error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None

class HTIndexerTracktable:
    """Class to interact with MySQL table ht_indexer_tracktable"""

    def __init__(self, db_conn: HtMysql, solr_exporter: SolrExporter = None):
        self.mysql_obj = db_conn
        self.solr_exporter = solr_exporter


    def get_catalog_data(self, query: str,
                         query_config_file_path: Path,
                         conf_query: str,
                         list_output_fields: List[str]) -> Generator[list[HTIndexerTrackData], Any, None]:
        """
        Get the data from the catalog.
        :return: List of data
        """

        # '"good"'
        data = []
        for x in self.solr_exporter.run_cursor(query, query_config_file_path, conf_query=conf_query,
                                          list_output_fields=list_output_fields):
            dict_x = json.loads(x)
            if "ht_id" in dict_x:

                for ht_id in dict_x["ht_id"]:
                    record = {
                        "ht_id": ht_id,
                        "record_id": dict_x["id"], #f"record_{ht_id}",
                        "status": "pending",
                        #"retriever_status": "pending",
                        #"generator_status": "pending",
                        #"indexer_status": "pending",
                        #"retriever_error": None,
                        #"generator_error": None,
                        #"indexer_error": None,
                        #"created_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                        #"updated_at": None,
                        #"processed_at": None
                    }
                    data.append(HTIndexerTrackData(ht_id=record['ht_id'], record_id=record['record_id'],
                                                   status=record['status']))

                #list_documents.extend([ht_id for ht_id in dict_x["ht_id"]])

            # Insert in MySQL a batch size of 1000 records
            if len(data) >= 10:
                yield data

    def create_table(self):
        """
        Create the table ht_indexer_tracktable if it does not exist.
        :return: None
        """
        ht_indexer_tracktable = """
        CREATE TABLE IF NOT EXISTS ht_indexer_tracktable (
            ht_id VARCHAR(255) UNIQUE NOT NULL,
            record_id VARCHAR(255) UNIQUE NOT NULL,
            status ENUM('pending', 'processing', 'failed', 'completed', 'requeued') NOT NULL DEFAULT 'Pending',
            retriever_status ENUM('pending', 'processing', 'failed', 'completed') NOT NULL DEFAULT 'Pending',
            generator_status ENUM('pending','processing' ,'failed', 'completed') NOT NULL DEFAULT 'Pending',
            indexer_status ENUM('pending', 'processing', 'failed', 'completed') NOT NULL DEFAULT 'Pending',
            retriever_error TEXT NULL,
            generator_error TEXT NULL,
            indexer_error TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            processed_at TIMESTAMP NULL DEFAULT NULL
        );
        """
        self.mysql_obj.create_table(ht_indexer_tracktable)

    def insert_batch(self, list_items: List[HTIndexerTrackData]):
        """Inserts a batch of HTIndexerTrackData objects into the database."""
        if not list_items:
            logger.info("No data to insert.")
            return

        insert_query = """INSERT INTO ht_indexer_tracktable (ht_id, record_id,  status, retriever_status, generator_status, indexer_status, retriever_error, generator_error, indexer_error) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                record_id = VALUES(record_id),
                status = VALUES(status),
                retriever_status = VALUES(retriever_status),
                generator_status = VALUES(generator_status),
                indexer_status = VALUES(indexer_status),
                retriever_error = VALUES(retriever_error),
                generator_error = VALUES(generator_error),
                indexer_error = VALUES(indexer_error),
                updated_at = CURRENT_TIMESTAMP;
            """
        batch_values = [
                (item.ht_id, item.record_id, item.status, item.retriever_status, item.generator_status, item.indexer_status, item.retriever_error, item.generator_error, item.indexer_error)
                for item in list_items
    ]

        self.mysql_obj.insert_batch(insert_query, batch_values)



def main():

    # Get parameters
    parser = argparse.ArgumentParser()

    init_args_obj = MonitoringServiceArguments(parser)

    # MySQL connection to retrieve documents from the ht database
    db_conn = get_mysql_conn()
    ht_indexer_tracktable = HTIndexerTracktable(db_conn, solr_exporter=init_args_obj.solr_exporter)

    # Query Catalog to retrieve N number of items
    # query="SELECT htid FROM hf LIMIT 1000000"
    # data = ht_indexer_tracktable.mysql_obj.query_mysql(query)

    if not ht_indexer_tracktable.mysql_obj.table_exists("ht_indexer_tracktable"):
        logger.info("Creating ht_indexer_tracktable table.")
        ht_indexer_tracktable.create_table()

    total_documents = 0
    for item in ht_indexer_tracktable.get_catalog_data(init_args_obj.query,
                                                    init_args_obj.query_config_file_path,
                                                       init_args_obj.conf_query,
                                                       init_args_obj.output_fields):
        print(item)
        total_documents += len(item)

        # Add data to the table
        ht_indexer_tracktable.insert_batch(item)

        if total_documents >= int(init_args_obj.args.num_found):
            break



    # TODO: Things to discuss:
    # 1- I want to add the record_id and ht_id. It probably be better to retrieve documents from Solr
    # instead from MySQL. Retriever services can process one item at a time or all the items in a record.
    # 2- ht_indexer_tracktable is a table to monitor the status of the documents.
    # Right now, I'm creating a list of items to insert in the table for testing purposes.
    # In the future, this table will be populated by different services when new documents are added to the system.
    # services (retriever, generator, indexer) will update the status of the documents in the table.
    # 3- retriever_service will be a cron job that will start every morning to retrieve the documents with status
    # pending in ht_indexer_tracktable.
    # For experimentation, after creating the table, I will start the retriever_service to retrieve the documents
    # What do I need to run ht_indexer_monitoring/ht_indexer_tracktable.py in Kubernetes?
        #MySql user/password with write access to the database?

    #data = create_ht_indexer_track_data()



    # Start retriever service to retrieve the documents with status pending in ht_indexer_tracktable


if __name__ == "__main__":
    main()