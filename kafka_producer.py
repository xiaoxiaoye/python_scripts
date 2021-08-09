import json

from kafka import KafkaProducer
from kafka.errors import KafkaError

if __name__ == '__main__':
    broker_server = "master-1:9092"
    topic = "CLPO-4A-TOPIC"
    producer = KafkaProducer(bootstrap_servers=[broker_server],
                             value_serializer=lambda m: json.dumps(m).encode("ascii"))

    data = {
        "AUDIT_LOG_ID": "2",
        "SERVER_ADDRESS": "10.10.152.158",
        "SUB_ACCOUNT_NAME": "NQSHJM0003",
        "MODULE_ID": 1,
        "OPERATE_RESULT": "0",
        "SERVER_PORT": "80",
        "OP_TYPE_ID": "1-SHNGBOSS_CRM-10000",
        "MODULE_NAME": "CRM你好",
        "CLIENT_PORT": "80",
        "SRC_CODE": "1",
        "CLIENT_NETWORK_ADDRESS": "10.10.149.14",
        "OP_LEVEL_ID": "2",
        "OUT_AUDIT_LOG_ID": "10630715025",
        "OP_TYPE_NAME": "CRM logint",
        "RESOURCE_CODE": "SHNGCRM",
        "CLIENT_ADDRESS": "10.10.149.14",
        "IDENTITY_NAME": "4ABOSSLog",
        "IS_SHIELD": "0",
        "RESOURCE_KIND": "1",
        "OPERATE_CONTENT": "log in",
        "OPERATE_DATE": "2020-11-18 17:10:13",
        "CLIENT_MAC": "00:6A:50:B6:12:12",
        "CREATE_DATE": "20201118 171013",
        "SERVER_MAC": "00-50-56-96-9B-17"
    }
    future = producer.send(topic, data)
    try:
        record_metadata = future.get(timeout=100)
        print(record_metadata.topic)
        print(record_metadata.partition)
        print(record_metadata.offset)
    except KafkaError as e:
        print(e)
