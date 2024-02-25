#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import signal
from argparse import ArgumentParser

from base.func_report_reminder import ReportReminder
from configuration import Config
from constants import ChatType
from robot import Robot, __version__
from wcferry import Wcf


# def weather_report(robot: Robot) -> None:
#     """模拟发送天气预报"""

#     # 获取接收人
#     receivers = ["24309710403@chatroom"]

#     # 获取天气，需要自己实现，可以参考 https://gitee.com/lch0821/WeatherScrapy 获取天气。
#     report = "这就是获取到的天气情况了"

#     for r in receivers:
#         robot.sendTextMsg(report, r, "wxid_d2v9quh2emsu22")
#         # robot.sendTextMsg(report, r, "notify@all")   # 发送消息并@所有人


def APEX_report(robot: Robot) -> None:
    """模拟发送天气预报"""

    # 获取接收人
    receivers = ["24309710403@chatroom"]

    for r in receivers:
        robot.sendTextMsg(
            "今天打不打? 我最喜欢玩APEX了一天不玩就会死掉 [快哭了][可怜]",
            r,
            "wxid_d2v9quh2emsu22",
        )
        # robot.sendTextMsg(report, r, "notify@all")   # 发送消息并@所有人


def main(chat_type: int):
    config = Config()
    wcf = Wcf(debug=True)

    def handler(sig, frame):
        wcf.cleanup()  # 退出前清理环境
        exit(0)

    signal.signal(signal.SIGINT, handler)

    robot = Robot(config, wcf, chat_type)
    robot.LOG.info(f"WeChatRobot【{__version__}】成功启动···")

    # 机器人启动发送测试消息
    # robot.sendTextMsg(
    #     "大家好我叫丁真,最喜欢抽电子烟,我来自理塘",
    #     "24309710403@chatroom"
    # )

    # 接收消息
    # robot.enableRecvMsg()     # 可能会丢消息？
    robot.enableReceivingMsg()  # 加队列

    # robot.newsReport()

    # # 每天 18:30 发送新闻
    # robot.onEveryTime("18:42", robot.newsReport)
    # # 每天 16:30 提醒发日报周报月报
    # robot.onEveryTime("14:21", ReportReminder.remind, robot=robot)

    robot.onEveryTime("08:00", APEX_report, robot=robot)
    robot.onEveryTime("18:00", APEX_report, robot=robot)


    # 让机器人一直跑
    robot.keepRunningAndBlockProcess()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-c", type=int, default=0, help=f"选择模型参数序号: {ChatType.help_hint()}"
    )
    args = parser.parse_args().c
    main(args)
