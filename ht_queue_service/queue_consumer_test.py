import sys
import os

from ht_queue_service.queue_consumer import QueueConsumer


class TestHTConsumerService:
    def test_queue_does_not_exist(self):
        ht_consumer = QueueConsumer("guest",
                                    "guest",
                                    "localhost",
                                    "catalog_queue",
                                    "test")

        try:
            ht_consumer.consume_message()
        except KeyboardInterrupt:
            print("Interrupted by user")
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
