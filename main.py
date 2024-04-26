#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import signal
from argparse import ArgumentParser

from base.func_chengyu import Chengyu
from base.func_report_reminder import ReportReminder
from configuration import Config
from constants import ChatType
from robot import Robot, __version__
from wcferry import Wcf


djyp_room = "24309710403@chatroom"
test_room = "44946008946@chatroom"
wpp_room = "34804723034@chatroom"

qmh = "wxid_d2v9quh2emsu22"
zxk = "wxid_krjnrubsezs412"
cxf = "wxid_af2xqrab4s6z22"
xgw = "wxid_e2ir27n3tk2v22"
wly = "wxid_d6j3mqs9pxie22"
rzq = "wxid_jkbj2u83b6kq22"
hds1 = "wxid_ylp0qx47nbat22"
hds2 = "wxid_r94mrmhey9pn22"

sy = [qmh, cxf, zxk, xgw, rzq, wly, hds1, hds2]


# def signin_remind(robot: Robot, is_up: bool, at="") -> None:
#     up = "上班打卡喔! 上班打卡喔! 上班打卡喔! 别忘记打卡喔箱底们呐!!! [快哭了][凋谢] [快哭了][凋谢] [快哭了][凋谢]"
#     down = "下班打卡喔! 下班打卡喔! 下班打卡喔! 别忘记打卡喔箱底们呐!!! [呲牙][强] [呲牙][强] [呲牙][强]"

#     robot.sendTextMsg(
#         up if is_up else down, djyp_room, at if not at == "" else "notify@all"
#     )


def game_remind(robot: Robot) -> None:
    # 获取接收人
    receiver = djyp_room

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

    # qmh
    robot.sendTextMsg(random.choice(texts), receiver, qmh)

    # cxf
    robot.sendTextMsg(random.choice(texts), receiver, cxf)

def remake_remind(robot: Robot) -> None:
    # 获取接收人
    receiver = test_room

    texts = [
        "被指到的人，今天可以考虑重开喔 [笑脸][强]",
        "原来你还活着呀? [笑脸]",
        "记得要玩原神喔，今天又是原气满满的一天呢! [笑脸][强]",
    ]

    # 随机发送
    robot.sendTextMsg(random.choice(texts), receiver, random.choice(sy))

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

    # 接收消息
    # robot.enableRecvMsg()     # 可能会丢消息？
    robot.enableReceivingMsg()  # 加队列

    # 每天 08:30 发送新闻
    robot.onEveryTime("08:30", robot.newsReport)

    # robot.onEveryTime("08:30", game_remind, robot=robot)
    # robot.onEveryTime("18:00", game_remind, robot=robot)

    # 打卡提示
    robot.onEveryTime(
        "09:00", lambda: ReportReminder.signin_remind(robot=robot, is_up=True)
    )
    robot.onEveryTime(
        "17:00", lambda: ReportReminder.signin_remind(robot=robot, is_up=False)
    )
    
    
    # 搞心态提示
    robot.onEveryTime("08:00", remake_remind, robot=robot)
    robot.onEveryTime("21:00", remake_remind, robot=robot)

    # # 每天 18:30 提醒发日报周报月报
    robot.onEveryTime("18:30", ReportReminder.remind, robot=robot)

    # 让机器人一直跑
    robot.keepRunningAndBlockProcess()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-c", type=int, default=2, help=f"选择模型参数序号: {ChatType.help_hint()}"
    )
    args = parser.parse_args().c
    main(args)
