#!/usr/bin/env /Library/Developer/CommandLineTools/usr/bin/python3
import os
import time

import gistyc

AUTH_TOKEN = "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"
BASE_DIR = "/Users/yejiaxin/Documents/文档/学习笔记/"


def get_local_files():
    local_file = os.listdir(BASE_DIR)
    return list(filter(lambda filename: filename[-2:] == "md", local_file))


def get_gists_files(api: gistyc.GISTyc):
    gist_list = api.get_gists()
    gist_files = []
    for gist in gist_list:
        for gist_filename in gist.get("files").keys():
            gist_files.append(gist_filename)
    return gist_files


def update_gist(api: gistyc.GISTyc, filename):
    file_path = os.path.join(BASE_DIR, filename)
    api.update_gist(file_name=file_path)


def create_gist(api: gistyc.GISTyc, filename):
    file_path = os.path.join(BASE_DIR, filename)
    api.create_gist(file_name=file_path)


def get_gists_url_list(api: gistyc.GISTyc):
    gist_list = api.get_gists()
    gist_url_list = {}
    for gist in gist_list:
        html_url = gist.get("html_url")
        for file_name in gist.get("files").keys():
            if file_name[-2:] == "md":
                gist_url_list[file_name] = html_url
    return gist_url_list


if __name__ == '__main__':
    start = time.time()
    gist_api = gistyc.GISTyc(auth_token=AUTH_TOKEN)
    local_files = get_local_files()
    gists_files = get_gists_files(gist_api)
    need_create_files = set(local_files) - set(gists_files)
    need_update_files = set(local_files) - need_create_files

    for file in need_create_files:
        print("create gist " + file)
        create_gist(gist_api, file)

    for file in need_update_files:
        print("update gist " + file)
        update_gist(gist_api, file)

    gist_urls = get_gists_url_list(gist_api)
    for filename, url in gist_urls.items():
        print(filename + ": " + url)

    print("sync gists cost {}s".format(time.time()-start))