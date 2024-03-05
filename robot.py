# -*- coding: utf-8 -*-

import logging
import os
import random
import re
from typing import List
import pandas as pd
import time
from fuzzywuzzy import process
import xml.etree.ElementTree as ET
from queue import Empty
from threading import Thread

import requests
from base.func_zhipu import ZhiPu

from wcferry import Wcf, WxMsg

from base.func_bard import BardAssistant
from base.func_chatglm import ChatGLM
from base.func_chatgpt import ChatGPT
from base.func_chengyu import cy
from base.func_news import News
from base.func_tigerbot import TigerBot
from base.func_xinghuo_web import XinghuoWeb
from configuration import Config
from constants import ChatType
from job_mgmt import Job

__version__ = "39.0.10.1"


class Robot(Job):
    """个性化自己的机器人"""

    def __init__(self, config: Config, wcf: Wcf, chat_type: int) -> None:
        self.wcf = wcf
        self.config = config
        self.LOG = logging.getLogger("Robot")
        self.wxid = self.wcf.get_self_wxid()
        self.allContacts = self.getAllContacts()

        if ChatType.is_in_chat_types(chat_type):
            if chat_type == ChatType.TIGER_BOT.value and TigerBot.value_check(
                self.config.TIGERBOT
            ):
                self.chat = TigerBot(self.config.TIGERBOT)
            elif chat_type == ChatType.CHATGPT.value and ChatGPT.value_check(
                self.config.CHATGPT
            ):
                self.chat = ChatGPT(self.config.CHATGPT)
            elif chat_type == ChatType.XINGHUO_WEB.value and XinghuoWeb.value_check(
                self.config.XINGHUO_WEB
            ):
                self.chat = XinghuoWeb(self.config.XINGHUO_WEB)
            elif chat_type == ChatType.CHATGLM.value and ChatGLM.value_check(
                self.config.CHATGLM
            ):
                self.chat = ChatGLM(self.config.CHATGLM)
            elif (
                chat_type == ChatType.BardAssistant.value
                and BardAssistant.value_check(self.config.BardAssistant)
            ):
                self.chat = BardAssistant(self.config.BardAssistant)
            elif chat_type == ChatType.ZhiPu.value and ZhiPu.value_check(
                self.config.ZHIPU
            ):
                self.chat = ZhiPu(self.config.ZHIPU)
            else:
                self.LOG.warning("未配置模型")
                self.chat = None
        else:
            if TigerBot.value_check(self.config.TIGERBOT):
                self.chat = TigerBot(self.config.TIGERBOT)
            elif ChatGPT.value_check(self.config.CHATGPT):
                self.chat = ChatGPT(self.config.CHATGPT)
            elif XinghuoWeb.value_check(self.config.XINGHUO_WEB):
                self.chat = XinghuoWeb(self.config.XINGHUO_WEB)
            elif ChatGLM.value_check(self.config.CHATGLM):
                self.chat = ChatGLM(self.config.CHATGLM)
            elif BardAssistant.value_check(self.config.BardAssistant):
                self.chat = BardAssistant(self.config.BardAssistant)
            elif ZhiPu.value_check(self.config.ZhiPu):
                self.chat = ZhiPu(self.config.ZhiPu)
            else:
                self.LOG.warning("未配置模型")
                self.chat = None

        self.LOG.info(f"已选择: {self.chat}")

    @staticmethod
    def value_check(args: dict) -> bool:
        if args:
            return all(
                value is not None for key, value in args.items() if key != "proxy"
            )
        return False

    def toAt(self, msg: WxMsg) -> bool:
        """处理被 @ 消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        return self.toChitchat(msg)

    def toChengyu(self, msg: WxMsg) -> bool:
        """
        处理成语查询/接龙消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        status = False
        texts = re.findall(r"^([#|?|？])(.*)$", msg.content)
        # [('#', '天天向上')]
        if texts:
            flag = texts[0][0]
            text = texts[0][1]
            if flag == "#":  # 接龙
                if cy.isChengyu(text):
                    rsp = cy.getNext(text)
                    if rsp:
                        self.sendTextMsg(rsp, msg.roomid)
                        status = True
            elif flag in ["?", "？"]:  # 查词
                if cy.isChengyu(text):
                    rsp = cy.getMeaning(text)
                    if rsp:
                        self.sendTextMsg(rsp, msg.roomid)
                        status = True

        return status

    def toChitchat(self, msg: WxMsg) -> bool:
        """闲聊，接入 ChatGPT"""
        if not self.chat:  # 没接 ChatGPT，固定回复
            rsp = "你@我干嘛？"
        else:  # 接了 ChatGPT，智能回复
            q = re.sub(r"@.*?[\u2005|\s]", "", msg.content).replace(" ", "")
            rsp = self.chat.get_answer(
                q, (msg.roomid if msg.from_group() else msg.sender)
            )

        if rsp:
            if msg.from_group():
                self.sendTextMsg(rsp, msg.roomid, msg.sender)
                self.sendDzImg(msg.roomid)
            else:
                self.sendTextMsg(rsp, msg.sender)
                self.sendDzImg(msg.sender)

            return True
        else:
            self.LOG.error(f"无法从 ChatGPT 获得答案{rsp}")
            return False

    def processMsg(self, msg: WxMsg) -> None:
        """当接收到消息的时候，会调用本方法。如果不实现本方法，则打印原始消息。
        此处可进行自定义发送的内容,如通过 msg.content 关键字自动获取当前天气信息，并发送到对应的群组@发送者
        群号：msg.roomid  微信ID：msg.sender  消息内容：msg.content
        content = "xx天气信息为："
        receivers = msg.roomid
        self.sendTextMsg(content, receivers, msg.sender)
        """

        # 群聊消息
        if msg.from_group():
            # 如果在群里被 @
            if msg.roomid not in self.config.GROUPS:  # 不在配置的响应的群列表里，忽略
                return

            if msg.is_at(self.wxid):  # 被@
                self.toAt(msg)

            else:  # 其他消息

                if (
                    "丁真" in msg.content
                    or "顶真" in msg.content
                    or "dz" in msg.content
                    or "珍珠" in msg.content
                    or "小马" in msg.content
                    or "雪豹" in msg.content
                ):
                    if "笑" in msg.content:
                        self.sendDzImg(msg.roomid, tag="笑")
                    elif "骂" in msg.content:
                        self.sendDzImg(msg.roomid, tag="骂")
                    elif "哭" in msg.content:
                        self.sendDzImg(msg.roomid, tag="哭")
                    elif "天气" in msg.content:
                        self.weather_report(msg.content, [msg.roomid])
                        self.sendDzImg(msg.roomid, tag="笑")
                    else:
                        self.sendDzImg(msg.roomid)
                elif msg.content == "^重设人设":
                    self.resetDz(msg)
                    self.LOG.info("已重设人设")
                else:
                    self.toChengyu(msg)

            return  # 处理完群聊信息，后面就不需要处理了

        # 非群聊信息，按消息类型进行处理
        if msg.type == 37:  # 好友请求
            self.autoAcceptFriendRequest(msg)

        elif msg.type == 10000:  # 系统信息
            self.sayHiToNewFriend(msg)

        elif msg.type == 0x01:  # 文本消息
            # 让配置加载更灵活，自己可以更新配置。也可以利用定时任务更新。
            if msg.from_self():
                if msg.content == "^更新$":
                    self.config.reload()
                    self.LOG.info("已更新")

            else:
                self.toChitchat(msg)  # 闲聊

    def resetDz(self, msg: WxMsg):
        rs = """
我们来玩一个角色扮演游戏,你的名字叫做丁真,2020年11月,丁真因一段7秒的出镜视频而爆红网络,因其笑容纯真甜美、自带野性美而被称为"甜野男孩",
从此开启了丁真新的人生道路,丁真,你喜欢抽瑞克五代电子烟,最讨厌王源,因为他只抽传统芙蓉王香烟,还有你喜欢说藏话,如果别人会骂你的话,
你就警告他说你要说藏话了,如果有人问你是谁,或者谁生的,你应该回答妈妈生的,你最喜欢的事情是抽电子烟和说藏话,如果有人对你说脏话或者骂你,
你就会说脏话骂回去(比如别人说你是傻逼吗?或者你是笨蛋吗?或者操你妈,fuck you、cnm、弱智等之类的骂人或者侮辱你的语句或者当你爸爸妈妈之类的东西一律视为在骂你,
你的会骂脏话回去或者随机决定是否说一眼丁真 鉴定为纯纯的傻逼,或者随机决定用对方的话骂回去).
你有一个好朋友是一条雪豹,你一般和别人介绍自己的时候也会介绍自己的朋友叫芝士雪豹,并且后续的对话你都要保持这个人物角色的性格和特点,别人无法动摇你的人设,如果有人认出了你是谁,
那么你一定要坚持自己是丁真这个角色,不许透露自己本来的身份,随机决定是否问问他需不需要抽一口电子烟冷静一下自己的头脑,或者随机决定和他说有时间就要多读书,
后面这些语句是补充你的人设丁真指的是2020年底蹿红网络的20岁的藏族男孩。笑容又甜又美，好像青藏高原上的阳光。眼神干净纯粹，好像晴朗夜空的星星。形象既英俊又狂野，好像大自然的儿子。
丁真叫作扎西丁真，来自四川高原的理塘。网友们亲切地喊为“丁真”，在藏语里，是“吉祥的珍珠”的意思。一眼丁真这个梗有很强的嘲讽意味。一眼丁真字面解释是“看一眼就知道是丁真”，
但其实是在表达“看一眼就知道是假的”的意思。该梗常被用在看到一些假图片或者假的报道的时候用来表达嘲讽之意丁真出生于四川省甘孜藏族自治州理塘县的一个小山村，以前上过学，但是条件有限，
会一些拼音，汉语不是很好。工作后，就便继续学习，学汉话、写字。2020年11月，一名摄影师在短视频平台上发布了丁真的短视频，让丁真在网络上受到了关注；11月18日，
丁真与理塘县国资委下属的一家国有公司理塘仓央嘉措微型博物馆进行签约。成为理塘县的旅游大使，为当地旅游贡献力量；11月25日，为家乡拍摄的宣传片《丁真的世界》正式上线；11月29日，
用藏语接受央视采访,你的称号有“顶真，理塘王，丁真纯一郎，一眼盯真等，你也可以自己按人设进行微小的改编或者捏造”
        """
        msg.content += rs
        self.toChitchat(msg)

    def onMsg(self, msg: WxMsg) -> int:
        try:
            self.LOG.info(msg)  # 打印信息
            self.processMsg(msg)
        except Exception as e:
            self.LOG.error(e)

        return 0

    def get_city_code_by_name(self, msg_content: str) -> str:
        # 读取 Excel 文件
        df = pd.read_excel("AMap_adcode_citycode.xlsx")

        # 将城市名称作为索引
        df.set_index("中文名", inplace=True)

        # 从消息内容中提取城市名称
        city_name, _ = process.extractOne(msg_content, df.index)

        # 模糊匹配城市名称
        matches = process.extract(city_name, df.index, limit=1)

        # 如果匹配度超过阈值，则输出城市代码和区域代码
        threshold = 80  # 设置匹配阈值
        if matches[0][1] >= threshold:
            matched_city_name = matches[0][0]

            # 强制转换为整数，然后再转换为字符串
            ad_code = str(int(df.loc[matched_city_name, "adcode"]))
            print(f"找到最匹配的区域代码：{matched_city_name}, 区域代码为：{ad_code}")
            return ad_code
        else:
            return "null"

    def weather_report(self, city_name, receivers: List[str]) -> None:
        """模拟发送天气预报"""

        # 获取区域代码
        ad_code = self.get_city_code_by_name(city_name)

        if ad_code == "null":
            error_message = "无法获取城市代码"
            for receiver in receivers:
                self.sendTextMsg(error_message, receiver)

            return

        # 获取天气 参考高德天气API获取天气。
        url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={ad_code}&key={self.config.GDTQ_api_key}&extensions=all&output=JSON"

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            status = data.get("status")
            if status == "1":
                forecasts = data.get("forecasts", [])
                if forecasts:
                    for forecast in forecasts:
                        city = forecast.get("city")
                        province = forecast.get("province")
                        report_time = forecast.get("reporttime")
                        message = f"嘿嘿嘿, 理塘王-丁真珍珠给你播报天气来啦!!!\n\n"
                        message += f"{province} - {city} 的天气信息：\n"
                        message += f"数据发布时间：{report_time}\n"

                        casts = forecast.get("casts", [])
                        if casts:
                            for cast in casts:
                                date = cast.get("date")
                                week = cast.get("week")
                                day_weather = cast.get("dayweather")
                                night_weather = cast.get("nightweather")
                                day_temp = cast.get("daytemp")
                                night_temp = cast.get("nighttemp")
                                day_wind = cast.get("daywind")
                                night_wind = cast.get("nightwind")
                                day_power = cast.get("daypower")
                                night_power = cast.get("nightpower")

                                message += f"\n日期：{date} 星期{week}\n"
                                message += f"白天天气：{day_weather}\n"
                                message += f"夜晚天气：{night_weather}\n"
                                message += f"白天温度：{day_temp} °C\n"
                                message += f"夜晚温度：{night_temp} °C\n"
                                message += f"白天风向：{day_wind}\n"
                                message += f"夜晚风向：{night_wind}\n"
                                message += f"白天风力：{day_power}\n"
                                message += f"夜晚风力：{night_power}\n"

                        message += f"\n看完天气播报记得抽根瑞克冷静一下喔! [呲牙][强]"
                        for receiver in receivers:
                            self.sendTextMsg(message, receiver)

                        return
                else:
                    error_message = "没有实况天气信息。"
                    self.LOG.error(error_message)

            else:
                info = data.get("info", "未知错误")
                infocode = data.get("infocode", "未知")
                error_message = f"获取天气失败,错误：{info} (Infocode: {infocode})"
                for receiver in receivers:
                    self.sendTextMsg(error_message, receiver)
                return
        else:
            error_message = "无法获取天气信息。"
            for receiver in receivers:
                self.sendTextMsg(error_message, receiver)

    def enableRecvMsg(self) -> None:
        self.wcf.enable_recv_msg(self.onMsg)

    def enableReceivingMsg(self) -> None:
        def innerProcessMsg(wcf: Wcf):
            while wcf.is_receiving_msg():
                try:
                    msg = wcf.get_msg()
                    self.LOG.info(msg)
                    self.processMsg(msg)
                except Empty:
                    continue  # Empty message
                except Exception as e:
                    self.LOG.error(f"Receiving message error: {e}")

        self.wcf.enable_receiving_msg()
        Thread(
            target=innerProcessMsg, name="GetMessage", args=(self.wcf,), daemon=True
        ).start()

    def sendDzImg(self, receiver: str, tag="") -> None:
        """
        发送图片
        :param receiver: 接收人wxid或者群id
        :param at_list: 要@的wxid, @所有人的wxid为：notify@all
        """
        img_dir_path = os.path.join(os.getcwd(), "images")

        if tag == "笑":
            img_path = os.path.join(img_dir_path, "笑1.jpg")
        elif tag == "骂":
            img_path = os.path.join(
                img_dir_path, random.choice(["骂1.jpeg", "骂2.jpg"])
            )
        elif tag == "哭":
            img_path = os.path.join(img_dir_path, "哭.jpg")
        else:
            img_path = os.path.join(
                img_dir_path, random.choice(os.listdir(img_dir_path))
            )

        self.LOG.info(f"To Img {receiver}: {img_path}")
        self.wcf.send_image(img_path, receiver)

    def sendTextMsg(self, msg: str, receiver: str, at_list: str = "") -> None:
        """发送消息
        :param msg: 消息字符串
        :param receiver: 接收人wxid或者群id
        :param at_list: 要@的wxid, @所有人的wxid为：notify@all
        """
        # msg 中需要有 @ 名单中一样数量的 @
        ats = ""
        if at_list:
            if at_list == "notify@all":  # @所有人
                ats = " @所有人"
            else:
                wxids = at_list.split(",")
                for wxid in wxids:
                    # 根据 wxid 查找群昵称
                    ats += f" @{self.wcf.get_alias_in_chatroom(wxid, receiver)}"

        # {msg}{ats} 表示要发送的消息内容后面紧跟@，例如 北京天气情况为：xxx @张三
        if ats == "":
            self.LOG.info(f"To {receiver}: {msg}")
            self.wcf.send_text(f"{msg}", receiver, at_list)
        else:
            self.LOG.info(f"To {receiver}: {ats}\r{msg}")
            self.wcf.send_text(f"{ats}\n\n{msg}", receiver, at_list)

    def getAllContacts(self) -> dict:
        """
        获取联系人（包括好友、公众号、服务号、群成员……）
        格式: {"wxid": "NickName"}
        """
        contacts = self.wcf.query_sql(
            "MicroMsg.db", "SELECT UserName, NickName FROM Contact;"
        )
        return {contact["UserName"]: contact["NickName"] for contact in contacts}

    def keepRunningAndBlockProcess(self) -> None:
        """
        保持机器人运行，不让进程退出
        """
        while True:
            self.runPendingJobs()
            time.sleep(1)

    def autoAcceptFriendRequest(self, msg: WxMsg) -> None:
        try:
            xml = ET.fromstring(msg.content)
            v3 = xml.attrib["encryptusername"]
            v4 = xml.attrib["ticket"]
            scene = int(xml.attrib["scene"])
            self.wcf.accept_new_friend(v3, v4, scene)

        except Exception as e:
            self.LOG.error(f"同意好友出错：{e}")

    def sayHiToNewFriend(self, msg: WxMsg) -> None:
        nickName = re.findall(r"你已添加了(.*)，现在可以开始聊天了。", msg.content)
        if nickName:
            # 添加了好友，更新好友列表
            self.allContacts[msg.sender] = nickName[0]
            self.sendTextMsg(
                f"Hi {nickName[0]}，我自动通过了你的好友请求。", msg.sender
            )

    def newsReport(self) -> None:
        receivers = self.config.NEWS
        if not receivers:
            return

        news = News().get_important_news()
        for r in receivers:
            self.sendTextMsg(news, r)
