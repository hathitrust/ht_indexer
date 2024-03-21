import pika


def ht_queue_connection(queue_connection: pika.BlockingConnection,
                        ht_channel_name: str, queue_name: str):
    # queue a name is important when you want to share the queue between producers and consumers

    # channel - a channel is a virtual connection inside a connection
    # get channel
    ht_channel = queue_connection.channel()

    # exchange - this can be assumed as a bridge name which needed to be declared so that queues can be accessed
    # declare the exchange
    ht_channel.exchange_declare(ht_channel_name, durable=True, exchange_type="direct")

    # Check if the queue exist
    # Declare a queue
    ht_channel.queue_declare(queue=queue_name, durable=True, exclusive=False, auto_delete=False)

    # The relationship between exchange and a queue is called a binding.
    # Link the exchange to the queue to send messages.
    ht_channel.queue_bind(exchange=ht_channel_name, queue=queue_name, routing_key=queue_name)

    ht_channel.basic_qos(prefetch_count=1)

    ht_channel.confirm_delivery()
    return ht_channel
