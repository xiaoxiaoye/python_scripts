# -*- encoding: utf-8 -*-
import os
import sys
import getopt
import re
import logging

# 仓库垃圾回收命令
REGISTRY_GC_COMMAND = "/usr/local/bin/docker exec vos-registry registry garbage-collect /etc/docker/registry/config.yml"

# 镜像命名规则
# auit-service-1.0_20201010v1.0
REGEX_IMAGE = re.compile(r"(.*)_([0-9]{8})v(.*)")

# 日志设置
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO,format=LOG_FORMAT)

def usage():
    return """\
    usage: python {} --registry_url=http://127.0.0.1:6999 --registry_path=. 
    说明:
        当不带--image_name,--image_tags参数，对所有镜像清理历史版本，保留version_limits个历史版本
    选项:
    --registry_url      必填，仓库地址,默认值[http://127.0.0.1:6999]
    --registry_path     必填，仓库数据目录,默认为当前目录
    --version_limits    选填，相同镜像保留历史版本数目
    --image_name        选填，镜像名称
    --image_tags        选填，镜像tag列表,不填为所有tag
    """.format(__file__)

def clean_images(registry_url, registry_path, filter_image_name, filter_image_tags):
    command_str = "find {} | grep current | grep link | grep {}".format(registry_path, filter_image_name)
    logging.info(command_str)

    output = os.popen(command_str).read()
    lines = output.split('\n')
    for line in lines:
        paths = line.split('/')
        if len(paths) < 9:
            continue
        image_name = paths[-6]
        image_tag = paths[-3]
        if filter_image_tags and image_tag not in filter_image_tags:
            continue
        logging.info("{}:{}".format(image_name, image_tag))

        # 读取镜像的digest, 用于拼接删除url
        with open(line) as fd:
            image_manifest = fd.read()
        logging.info(image_manifest)

        # 执行镜像删除动作
        delete_cmd = "curl -i -X DELETE --header \"Accept:application/vnd.docker.distribution.manifest.v2+json\" {}/v2/{}/manifests/{}".format(
            registry_url, image_name, image_manifest)
        logging.info(delete_cmd)
        delete_res = os.popen(delete_cmd).read()
        logging.info(delete_res)

        registry_gc(registry_path=registry_path, image_name=image_name)

def list_images_by_files(registry_path):
    image_map = {}
    command_str = "find {} | grep current | grep link".format(registry_path)
    output = os.popen(command_str).read()
    lines = output.split('\n')
    for line in lines:
        paths = line.split('/')
        if len(paths) < 9:
            continue
        image_name = paths[-6]
        image_tag = paths[-3]
        result = REGEX_IMAGE.match(image_name)
        if result:
            image = {
                "out_image_name": image_name,
                "out_image_tag": image_tag,
                "inner_image_name": result.group(1),
                "inner_image_date": int(result.group(2)),
                "inner_image_version": float(result.group(3))
            }
            if image["inner_image_name"] in image_map:
                image_map[image["inner_image_name"]].append(image)
            else:
                image_map[image["inner_image_name"]] = [image,]
    return image_map

def filter_images(images, version_limits):
    def comp_image(image1, image2):
        if image1["inner_image_date"] == image2["inner_image_date"]:
            comp_val = image1["inner_image_version"] - image2["inner_image_version"]
            if comp_val > 0:
                return 1
            elif comp_val < 0:
                return -1
            else:
                return 0
        return image1["inner_image_date"] - image2["inner_image_date"]

    images = sorted(images, cmp=comp_image)
    if len(images) > version_limits:
        return images[:len(images)-version_limits]
    return []

def clean_old_image_version(registry_url, registry_path, version_limits):
    logging.info("clean image version begin...")
    classified_images = list_images_by_files(registry_path)
    for _, images in classified_images.items():
        filtered_images = filter_images(images, version_limits)
        for image in filtered_images:
            image_name = image["out_image_name"]
            image_tag = image["out_image_tag"]
            clean_images(registry_url, registry_path, image["out_image_name"], [image["out_image_tag"],])
            logging.info("{}:{} has been deleted".format(image_name, image_tag))
    registry_gc(registry_path=registry_path, is_delete_layers=False)
    
def disploy_images(prefix_message, images):
    logging.info("{}".format(prefix_message))
    for image in images:
        logging.info("{}:{}".format(image["out_image_name"],image["out_image_tag"] ))

def registry_gc(registry_path=None,image_name=None, is_delete_layers=True):
    registry_gc_cmd = "{} | grep \"blob eligible for deletion\"".format(REGISTRY_GC_COMMAND)
    gc_res = os.popen(registry_gc_cmd).read()
    if not is_delete_layers:
        return
    for line in gc_res.split('\n'):
        if line:
            delete_layer_cmd = "find {} | grep {} |grep _layers | grep {} | xargs rm -rf".format(registry_path,image_name,line.split(':')[-1])
            logging.info(delete_layer_cmd)
            os.popen(delete_layer_cmd)
    

if __name__ == '__main__':
    # 仓库地址
    registry_url = "http://127.0.0.1:6999"
    # 仓库数据目录
    registry_path = "."
    # 镜像过滤关键字
    image_name = ""
    # 镜像tag列表
    image_tags = []
    # 保留的历史版本数量
    version_limits=10

    if len(sys.argv) < 2:
        logging.info(usage())
        exit(1)
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h",
                                   ["help", "registry_url=", "registry_path=", "image_name=", "image_tags="])
        for opt, arg in opts:
            if opt in ["-h", "--help"]:
                print(usage())
                sys.exit()
            elif opt == "--registry_url":
                registry_url = arg
            elif opt == "--registry_path":
                registry_path = arg
            elif opt == "--image_name":
                image_name = arg
            elif opt == "--image_tags":
                image_tags = arg.split(",")
            elif opt == "--version_limits":
                version_limits = int(arg)
    except getopt.GetoptError:
        logging.info(usage())
        exit(1)

    if not image_name:
        clean_old_image_version(registry_url, registry_path, version_limits)
        sys.exit(0)

    clean_images(registry_url, registry_path, image_name, image_tags)

