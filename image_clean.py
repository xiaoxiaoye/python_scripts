# -*- encoding: utf-8 -*-
import os
import sys
import getopt


def usage():
    return """\
usage: python {} --registry_url=http://127.0.0.1:6999 --registry_path=. --image_name=redis --image_tags=latest,v1
选项:
    --image_name        必填，镜像名称
    --image_tags        镜像tag列表,不填为所有tag
    --registry_url      仓库地址,默认值[http://127.0.0.1:6999]
    --registry_path     仓库数据目录,默认为当前目录
    """.format(__file__)


def clean_images(registry_url, registry_path, filter_image_name, filter_image_tags):
    command_str = "find {} | grep current | grep link | grep {}".format(
        registry_path, filter_image_name)
    print(command_str)

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
        print("{}:{}".format(image_name, image_tag))

        # 读取镜像的digest, 用于拼接删除url
        with open(line) as fd:
            image_manifest = fd.read()
        print(image_manifest)

        # 执行镜像删除动作
        delete_cmd = "curl -i -X DELETE --header \"Accept:application/vnd.docker.distribution.manifest.v2+json\" {}/v2/{}/manifests/{}".format(
            registry_url, image_name, image_manifest)
        print(delete_cmd)
        delete_res = os.popen(delete_cmd).read()
        print(delete_res)

        # 仓库垃圾回收命令
        registry_gc_cmd = "docker exec vos-registry registry garbage-collect /etc/docker/registry/config.yml | grep \"blob eligible for deletion\""
        gc_res = os.popen(registry_gc_cmd).read()
        for line in gc_res.split('\n'):
            if line:
                delete_layer_cmd = "find {} | grep {} |grep _layers | grep {} | xargs rm -rf".format(
                    registry_path, image_name, line.split(':')[-1])
                print(delete_layer_cmd)
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

    if len(sys.argv) < 2:
        print(usage())
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
    except getopt.GetoptError:
        print(usage())
        exit(1)

    if not image_name:
        print("image_name is empty")
        sys.exit(1)

    clean_images(registry_url, registry_path, image_name, image_tags)
