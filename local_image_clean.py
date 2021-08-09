import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CLEAN_NONE_IMAGE_CMD = "docker images | grep none | awk '{print $3}'|xargs -r docker rmi -f"
LIST_ALL_IMAGE_CMD = "docker images | grep -v TAG | awk '{printf (\"%s:%s %s\\n\", $1,$2,$3)}'"
LIST_USED_IMAGE_CMD = "docker ps -a  | grep -v IMAGE | awk '{print $2}'"
REMOVE_LOCAL_IMAGE = "docker rmi {}"


def clean_none_image():
    os.popen(CLEAN_NONE_IMAGE_CMD)


def list_used_images():
    return os.popen(LIST_USED_IMAGE_CMD).read().split('\n')


def list_all_images():
    out_lines = os.popen(LIST_ALL_IMAGE_CMD).read().split('\n')
    images = []
    for line in out_lines:
        image_pair = line.split(' ')
        if len(image_pair) != 2:
            continue
        images.append(image_pair)
    return images


def remove_image(image_name):
    logging.info(REMOVE_LOCAL_IMAGE.format(image_name))
    os.popen(REMOVE_LOCAL_IMAGE.format(image_name))


"""
0 0 12 * * ? python /home/ips/scripts/clean_local_images.py >> /home/ips/scripts/clean_local_images.log 2>&1
"""
if __name__ == '__main__':
    clean_none_image()

    used_images = set(list_used_images())
    for name, id in list_all_images():
        if (name in used_images) or (id in used_images):
            continue
        remove_image(name)
