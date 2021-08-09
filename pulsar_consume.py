import pulsar


if __name__ == '__main__':
    client = pulsar.Client('pulsar://10.1.241.135:6650')
    consumer = client.subscribe('app-state',
                                subscription_name='my-sub')

    while True:
        msg = consumer.receive()
        print("Received message: '%s'" % msg.data())
        consumer.acknowledge(msg)

    client.close()