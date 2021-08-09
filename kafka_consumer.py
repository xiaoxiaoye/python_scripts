import copy
import json

import pymysql
from kafka import KafkaConsumer

DEFAULT_RECORD = {
    # "AUDIT_LOG_ID": 0,
    "OUT_AUDIT_LOG_ID": "",
    "SRC_CODE": "",
    "IDENTITY_NAME": "",
    "RESOURCE_KIND": 0,
    "RESOURCE_CODE": "",
    "MAIN_ACCOUNT_NAME": "",
    "SUB_ACCOUNT_NAME": "",
    "OP_TYPE_ID": "",
    "OP_TYPE_NAME": "",
    "OP_LEVEL_ID": 0,
    "OPERATE_CONTENT": "",
    "OPERATE_RESULT": 0,
    "MODULE_ID": 0,
    "MODULE_NAME": "",
    "TASK_CODE": "",
    "BANKAPPROVE": "",
    "BANK_PROOF": "",
    "BANKFLAG": "",
    "CLIENT_NETWORK_ADDRESS": "",
    "CLIENT_NAME": "",
    "CLIENT_ADDRESS": "",
    "CLIENT_PORT": "",
    "CLIENT_MAC": "",
    "CLIENT_CPU_SERIAL": "",
    "SERVER_ADDRESS": "",
    "SERVER_PORT": "",
    "SERVER_MAC": "",
    "EXT1": "",
    "EXT2": "",
    "EXT3": "",
    "ORG_NAME": "",
    "OPERATE_TYPE": 0,
    "OPERATE_NUM": "",
    "IS_SHIELD": 0,
    "QUERY_REASON": "",
    "EXT4": "",
    "CCSLOGDATAID": "",
    "CALLBILLID": "",
    "NOTE1": "",
    "NOTE2": "",
    "OPERATE_DATE": "2020-11-18 17:10:13",
    "SOURCE_DATA": ""
}


def convert_record_to_sql(entity):
    record = copy.deepcopy(DEFAULT_RECORD)
    record.update(entity)
    str_sql = "INSERT INTO audit_log({}) VALUES ({})"
    column_sql = ""
    values_sql = ""
    for column, _ in DEFAULT_RECORD.items():
        column_sql += column + ","
        if column in ("AUDIT_LOG_ID", "RESOURCE_KIND", "OP_LEVEL_ID", "OPERATE_RESULT", "OPERATE_TYPE", "IS_SHIELD", "MODULE_ID"):
            values_sql += str(record[column]) + ","
            continue
        values_sql += "\'" + record[column] + "\'" + ","
    column_sql = column_sql[:-1]
    values_sql = values_sql[:-1]
    str_sql = str_sql.format(column_sql, values_sql)
    return str_sql


def save_entity(connection: pymysql.Connection, entity):
    str_sql = convert_record_to_sql(entity)
    print("SQL: {}".format(str_sql))
    with connection.cursor() as cursor:
        cursor.execute(str_sql)
    connection.commit()


if __name__ == '__main__':
    consumer = KafkaConsumer("CLPO-4A-TOPIC",
                             bootstrap_servers=["10.1.245.157:9092"],
                             value_deserializer=lambda m: json.loads(m.decode(encoding='UTF-8',errors='ignore')))

    print(consumer.topics())
    print(consumer.bootstrap_connected())
    print(consumer.partitions_for_topic("CLPO-4A-TOPIC"))
    print(consumer.subscription())
    print(consumer.assignment())

    mysql_connection = pymysql.connect(host="10.1.245.157",port=3306, user="root", password="vos", database="vos",
                                       cursorclass=pymysql.cursors.DictCursor)

    print("begin receive message...")

    try:
        for message in consumer:
            print("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                                 message.offset, message.key,
                                                 message.value))
            save_entity(mysql_connection, message.value)
    except Exception as e:
        print(e)
    finally:
        mysql_connection.close()
