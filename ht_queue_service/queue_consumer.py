# consumer

import pika
import json

from ht_utils.ht_logger import get_ht_logger

logger = get_ht_logger(name=__name__)


# os.environ['RABBITMQ_HOST'] = 'localhost'
# os.environ['RABBITMQ_PORT'] = '5672'
# os.environ['RABBITMQ_USERNAME'] = 'guest'
# os.environ['RABBITMQ_PASSWORD'] = 'guest'


# To get message from the queue you have to define a callback functions that is subscribed to a queue
#
# make a class to connect to the rabbitMQ
# create a channel
# create a queue
# create a callback function
# start consuming the queue
# create a thread to start consuming the queue

def ht_queue_connection(queue_connection: pika.BlockingConnection,
                        ht_channel_name: str, queue_name: str):
    ht_channel = queue_connection.channel()

    # exchange - this can be assumed as a bridge name which needed to be declared so that queues can be accessed
    ht_channel.exchange_declare(ht_channel_name, durable=True, exchange_type="topic")

    # Check if the queue exist
    # Declare the queue as durable, so the queue will survive a broker restart
    ht_channel.queue_declare(queue=queue_name, durable=True)

    ht_channel.queue_bind(exchange=ht_channel_name, queue=queue_name, routing_key=queue_name)
    return ht_channel


class QueueConsumer:
    def __init__(self, user: str, password: str, host: str, queue_name: str, channel_name: str):
        # Define credentials (user/password) as environment variables
        # declaring the credentials needed for connection like host, port, username, password, exchange etc
        self.credentials = pika.PlainCredentials(username=user, password=password)

        self.host = host
        self.queue_name = queue_name
        self.channel_name = channel_name

        self.queue_connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host,
                                                                                  credentials=self.credentials))
        self.ht_channel = ht_queue_connection(self.queue_connection, self.channel_name, self.queue_name)
        # This uses the basic.qos protocol method to tell RabbitMQ not to give more than one message to a worker
        # at a time
        self.ht_channel.basic_qos(prefetch_count=1)

    def consume_message(self):
        logger.info(f"Got a message from Queue {self.queue_name}")
        # auto_ack=True, means that the message will be removed from the queue once it has been consumed, it is use
        # to make sure no message is lost
        self.ht_channel.basic_consume(queue=self.queue_name,
                                      auto_ack=True,
                                      on_message_callback=self.callback_function
                                      )

        # logger.info(' [*] Waiting for messages. To exit press CTRL+C')
        # self.ht_channel.start_consuming()

    def callback_function(self, ch, method, properties, body):
        print(f"Got a message from Queue {self.queue_name}")

        # ['order.stop.create']
        body = json.loads(body)
        return body
