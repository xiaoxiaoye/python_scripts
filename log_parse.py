# encoding: utf-8
import re
import sys
from datetime import datetime

split_pattern = re.compile(
    r"([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}) [0-9]+ \[([0-9a-z]+)\] [0-9]+ \[([a-z]+)\] (.*)")
start_pattern = re.compile(
    r".*>>>>>>>>>>>>>>>>>>dispatch msg start!\[msg_type\:([-0-9]+).*")
end_pattern = re.compile(
    r".*<<<<<<<<<<<<<<<<<<<dispatch msg end!\[msg_type\:([-0-9]+).*")
app_pattern = re.compile(r".*APP_ID\" : ([0-9]+),.*")


def log_split(log_line):
    result = split_pattern.match(log_line)
    if result:
        log_time = result.group(1)
        log_thread_id = result.group(2)
        log_level = result.group(3)
        log_info = result.group(4)
        return True, log_time, log_thread_id, log_level, log_info
    return False, None, None, None, None


def message_start(log_line):
    result = start_pattern.match(log_line)
    if result:
        return True, result.group(1)
    return False, None


def message_end(log_line):
    result = end_pattern.match(log_line)
    if result:
        return True, result.group(1)
    return False, None


def parse_app_id(log_line):
    result = app_pattern.match(log_line)
    if result:
        return True, result.group(1)
    return False, None


def keyword_filter(log_line):
    keywords = ["db_connector", "db_api"]
    for keyword in keywords:
        if keyword in log_line:
            return True
    return False


if __name__ == "__main__":
    '''
    按消息类型4111截取筛选日志
    python log_parse.py srm.0_-1_-1 msg_type 4111

    按APP_ID=1010802, 并过滤掉3006,3008消息
    python log_parse.py srm.0_-1_-1 app 1010802 3006,3008
    '''
    begin_time = datetime.now()
    file_name = str(sys.argv[1])
    r_search_type = str(sys.argv[2])
    r_search_value = str(sys.argv[3])
    r_exclude_msg_types = None
    if len(sys.argv) >= 4:
        r_exclude_msg_types = str(sys.argv[4:])
    # msg_begin_index = int(sys.argv[3])
    # msg_limit_nums = int(sys.argv[4])

    pre_thread_id = None
    # {thread_id1: [line1, line2], thread_id2: [line1, line2],...}
    thread_lines = {}
    dispatch_messages = {}
    '''
        msg_type: [
            {
                msg_type: "4111",
                msg_time: "2020-03-02 15:13:59.007409",
                log_lines: []
            }
        ]
    '''
    # ! 按线程id切分日志
    with open(file_name, "rb") as fp:
        line_no = 0
        while True:
            line = fp.readline()
            line_no += 1
            if line == b'':
                break

            try:
                match_flag, log_time, log_thread_id, log_level, log_info = log_split(
                    line)
                if match_flag:
                    pre_thread_id = log_thread_id
                    if thread_lines.get(log_thread_id, None) is None:
                        thread_lines[log_thread_id] = []
                    thread_lines[log_thread_id].append((line_no, line))
                else:
                    thread_lines[pre_thread_id].append((line_no, line))
            except Exception as e:
                print(line)
                print(e)

    # ! 相同线程日志按消息类型切分
    log_lines = []
    log_msg_type = None
    log_msg_time = None
    msg_start = False
    log_app_id = None
    for thread_id, lines in thread_lines.items():
        for line_no, line in lines:
            try:
                if not msg_start:
                    flag, msg_type = message_start(line)
                    if flag:
                        log_msg_type = msg_type
                        log_lines = []
                        log_lines.append((line_no, line))
                        msg_start = True
                        match_flag, log_time, log_thread_id, log_level, log_info = log_split(
                            line)
                        log_msg_time = log_time
                else:
                    log_lines.append((line_no, line))

                    app_matched, app_id = parse_app_id(line)
                    if app_matched:
                        log_app_id = app_id
                        # print("app_id:{}".format(log_app_id))

                    flag, msg_type = message_end(line)
                    if flag:
                        msg_start = False
                        if dispatch_messages.get(log_msg_type, None) is None:
                            dispatch_messages[log_msg_type] = []
                        dispatch_messages[log_msg_type].append(
                            {
                                "msg_time": log_msg_time,
                                "log_lines": log_lines,
                                "msg_type": log_msg_type,
                                "app_id": log_app_id
                            }
                        )
                        log_app_id = None
            except Exception:
                print(line_no, line)
                raise

    # ! 按消息类型筛选日志
    if r_search_type == "msg_type":
        if dispatch_messages.get(r_search_value, False):
            messages = sorted(
                dispatch_messages[r_search_value], key=lambda x: x["msg_time"])
            with open("./log/msg_type_{}.log".format(r_search_value), "wb") as fp:
                for msg in messages:
                    print("app_id: {}, msg_type: {}, receive time: {}, line_no: {}".format(msg.get(
                        "app_id", None), msg.get("msg_type", None), msg.get("msg_time", None), msg["log_lines"][0][0]))
                    fp.write(
                        "\n=========================================================\n\n")
                    for line_no, line in msg.get("log_lines", []):
                        if keyword_filter(line):
                            continue
                        line_str = "{} {}".format(line_no, line)
                        fp.write(line_str)
        else:
            print("no msg_type:{} in this log file".format(r_search_value))

    # ! 按app_id筛选日志
    elif r_search_type == "app":
        app_messages = []
        for msg_type, messages in dispatch_messages.items():
            # 去除内部消息
            if msg_type[0] == "-":
                continue

            # 排除指定消息类型
            if msg_type in r_exclude_msg_types:
                continue

            for msg in messages:
                if msg["app_id"] == r_search_value:
                    app_messages.append(msg)

        app_messages = sorted(app_messages, key=lambda x: x["msg_time"])
        with open("./log/app_id_{}.log".format(r_search_value), "wb") as fp:
            for app_msg in app_messages:
                print("msg_time:{}, msg_type:{}, line_no:{} in {}".format(
                    app_msg["msg_time"], app_msg["msg_type"], app_msg["log_lines"][0][0], file_name))
                fp.write(
                    "\n=========================================================\n\n")
                for line_no, line in app_msg.get("log_lines", []):
                    if keyword_filter(line):
                        continue
                    line_str = "{} {}".format(line_no, line)
                    fp.write(line_str)

    # 统计各消息的总数
    for msg_type, msgs in dispatch_messages.items():
        print("{}: {}".format(msg_type, len(msgs)))

    end_time = datetime.now()
    cost_time = end_time - begin_time
    print("cost {} seconds".format(cost_time.total_seconds()))
