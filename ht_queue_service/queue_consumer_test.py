import json

from ht_queue_service.queue_consumer import QueueConsumer
from ht_queue_service.queue_producer import QueueProducer


class TestHTConsumerService:
    def test_queue_does_not_exist(self, message=None):
        message = {"ht_id": "1234", "ht_title": "Hello World", "ht_author": "John Doe"}
        ht_producer = QueueProducer("guest", "guest", "localhost", "catalog_queue", "test")

        ht_producer.publish_messages(message)

        queue_consumer = QueueConsumer("guest",
                                       "guest",
                                       "localhost",
                                       "catalog_queue",
                                       "test")

        for method_frame, properties, body in queue_consumer.ht_channel.consume('catalog_queue'):
            # Display the message parts
            output_message = json.loads(body.decode('utf-8'))
            assert message == output_message

            break
