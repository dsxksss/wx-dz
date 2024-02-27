#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random
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


def Game_remind(robot: Robot) -> None:
    # 获取接收人
    receivers = ["24309710403@chatroom"]

    texts = [
        "今天打不打? 我最喜欢玩游戏了,一天不玩就会死掉 [快哭了][可怜]",
        "今天要一起打游戏吗？我超级喜欢游戏，不玩一天就感觉要死掉了 [快哭了][可怜]",
        "想一起玩游戏吗？我对游戏情有独钟，一天不玩就觉得无法生存 [快哭了][可怜]",
        "今天打游戏怎么样？我是游戏狂热爱好者，不玩就感觉要崩溃 [快哭了][可怜]",
        "今天要不要一起打游戏？我对游戏着迷，不玩就感觉生无可恋 [快哭了][可怜]",
        "想和我一起玩游戏吗？我是游戏控，不玩就觉得世界失色 [快哭了][可怜]",
        "今天一起打游戏吗？我是游戏迷，不玩就觉得生命失去了意义 [快哭了][可怜]",
        "想和我一起游戏吗？我对游戏痴迷，不玩就觉得人生无趣 [快哭了][可怜]",
        "今天要不要一起打游戏？我是游戏爱好者，不玩就感觉自己要完蛋了 [快哭了][可怜]",
        "想和我一起打游戏吗？我对游戏着迷，不玩就感觉生不如死 [快哭了][可怜]",
        "今天要一起玩游戏吗？我是游戏狂热粉，不玩就觉得人生失色 [快哭了][可怜]",
    ]

    for r in receivers:
        for _ in range(3):
            robot.sendTextMsg(
                random.choice(texts),
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
    robot.onEveryTime("08:30", Game_remind, robot=robot)
    robot.onEveryTime("12:30", Game_remind, robot=robot)
    robot.onEveryTime("18:00", Game_remind, robot=robot)

    # 让机器人一直跑
    robot.keepRunningAndBlockProcess()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-c", type=int, default=0, help=f"选择模型参数序号: {ChatType.help_hint()}"
    )
    args = parser.parse_args().c
    main(args)
