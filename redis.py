# -*- encoding: utf-8 -*-

import logging
import sys
from getopt import GetoptError, getopt
from os import popen

# 默认的master ip地址
DEFAULT_MASTER_IP = "127.0.0.1"

# 默认的redis服务端口
DEFAULT_REDIS_PORT = 6379

# 默认的密码
DEFAULT_PASSWORD = "1hblsqT!"

# 默认的哨兵端口
DEFAULT_SENTINEL_PORT = 26379

# redis容器名称
REDIS_CONTAINER_NAME = "redis"

# 哨兵容器名称
SENTINEL_CONTAINER_NAME = "sentinel"

# 镜像名称
DEFAULT_IMAGE = "redis"


def write_file(file, context):
    f = open(file, "w")
    f.write(context)
    f.close()


def create_redis_conf(port=DEFAULT_REDIS_PORT,
                      password=DEFAULT_PASSWORD,
                      is_master=True,
                      master_ip=DEFAULT_MASTER_IP,
                      master_port=DEFAULT_REDIS_PORT,
                      master_password=DEFAULT_PASSWORD):
    redis_conf = """\
port {}
logfile /log/redis-{}.log

save 900 1
save 300 10
save 60 10000

dbfilename dump.rdb
dir /data

requirepass {}\
""".format(port, port, password)

    slave_conf = """
slaveof {} {}
masterauth {}\
""".format(master_ip, master_port, master_password)

    if not is_master:
        redis_conf += slave_conf
    write_file("./config/redis-{}.conf".format(port), redis_conf)


def create_redis_run_script(container_name=REDIS_CONTAINER_NAME,
                            image_name=DEFAULT_IMAGE,
                            port=DEFAULT_REDIS_PORT):
    container_name = "{}-{}".format(container_name, port)
    run_script = """\
docker rm -vf {}
docker run \\
-dt \\
--net=host \\
-v `pwd`/../config/redis-{}.conf:/usr/local/etc/redis/redis.conf \\
-v `pwd`/../log:/log \\
-v `pwd`/../data:/data \\
--name {} \\
{} \\
redis-server /usr/local/etc/redis/redis.conf\
""".format(container_name, port, container_name, image_name)
    write_file("./bin/redis-{}.sh".format(port), run_script)


def create_sentinel_conf(master_ip=DEFAULT_MASTER_IP,
                         master_port=DEFAULT_REDIS_PORT,
                         master_password=DEFAULT_PASSWORD,
                         port=DEFAULT_SENTINEL_PORT):
    sentinel_conf = """\
sentinel deny-scripts-reconfig yes
sentinel monitor mymaster {} {} 2
sentinel down-after-milliseconds mymaster 60000
sentinel auth-pass mymaster {}
port {}
logfile "/log/sentinel-{}.log"\
""".format(master_ip, master_port, master_password, port, port)
    write_file("./config/sentinel-{}.conf".format(port), sentinel_conf)


def create_sentinel_run_script(container_name=SENTINEL_CONTAINER_NAME,
                               image_name=DEFAULT_IMAGE,
                               port=DEFAULT_SENTINEL_PORT):
    container_name = "{}-{}".format(container_name, port)
    run_script = """\
docker rm -vf {}
docker run \\
-dt \\
--net=host \\
-v `pwd`/../config/sentinel-{}.conf:/usr/local/etc/redis/sentinel.conf \\
-v `pwd`/../log:/log \\
--name {} \\
{} \\
redis-server /usr/local/etc/redis/sentinel.conf --sentinel\
""".format(container_name, port, container_name, image_name)
    write_file("./bin/sentinel-{}.sh".format(port), run_script)


def start(role="master", port=DEFAULT_REDIS_PORT):
    popen("chmod -R 0777 log config data")
    redis_start_cmd = "cd bin && sh redis-{}.sh".format(port)
    sentinel_start_cmd = "cd bin && sh sentinel-{}.sh".format(port)
    if role in ["master", "slave"]:
        popen(redis_start_cmd)
    if role == "sentinel":
        popen(sentinel_start_cmd)


def prepare():
    popen("mkdir -p bin config log data && chmod 0777 log")
    popen("cd image && docker load -i redis.tar")


def usage():
    return """
安装前请修改脚本中的如下配置项:
DEFAULT_MASTER_IP:  指定master的IP地址
DEFAULT_REDIS_PORT: 指定master的端口

部署master(master的端口不能通过--port指定，因为slave和sentinel需要master的IP和端口):
python redis.py --role=master

部署slave:
python redis.py --role=slave --port=6379

部署sentinel:
python redis.py --role=sentinel --port=26379

使用场景：
1. 单机单实例部署
python redis.py --role=master
2. 单机模拟高可用部署
python redis.py --role=master (默认端口为6379)
python redis.py --role=slave --port=6389
python redis.py --role=slave --port=6399
python redis.py --role=sentinel --port=26379
python redis.py --role=sentinel --port=26389
python redis.py --role=sentinel --port=26399
3. 多机高可用部署
修改脚本配置后，复制到多个节点
节点1:
python redis.py --role=master
python redis.py --role=sentinel --port=26379
节点2:
python redis.py --role=slave
python redis.py --role=sentinel --port=26379
节点3:
python redis.py --role=slave
python redis.py --role=sentinel --port=26379
"""


if __name__ == "__main__":
    roles = ["master", "slave", "sentinel"]

    if len(sys.argv) < 2:
        logging.info(usage)
        exit(1)

    role = "master"
    port = None
    container_name_include_port = False

    try:
        opts, args = getopt(sys.argv[1:], "h", ["help", "role=", "port="])
        for opt, arg in opts:
            if opt == "--role":
                role = arg
            elif opt == "--port":
                port = arg
                container_name_include_port = True
            elif opt in ["-h", "--help"]:
                print(usage())
                exit(0)
    except GetoptError:
        logging.info(usage())
        exit(1)

    if not port:
        if role == "slave":
            port = DEFAULT_REDIS_PORT
        if role == "sentinel":
            port = DEFAULT_SENTINEL_PORT

    if role == "master":
        port = DEFAULT_REDIS_PORT

    prepare()

    if role == "master":
        create_redis_conf(is_master=True, port=port)
        create_redis_run_script(port=port)

    if role == "slave":
        create_redis_conf(is_master=False, port=port)
        create_redis_run_script(port=port)

    if role == "sentinel":
        create_sentinel_conf(port=port)
        create_sentinel_run_script(port=port)

    start(role=role, port=port)
