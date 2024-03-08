import calendar
import datetime

from chinese_calendar import is_workday
from robot import Robot


class ReportReminder:

    @staticmethod
    def remind(robot: Robot) -> None:

        receivers = robot.config.REPORT_REMINDERS
        if not receivers:
            receivers = ["filehelper"]
            
        # 日报周报月报提醒
        for receiver in receivers:
            today = datetime.datetime.now().date()
            # 如果是非工作日
            if not is_workday(today):
                robot.sendTextMsg(
                    "休息日快乐, 记得把没补的周报日报写一下喔 箱底们呐",
                    receiver,
                    "notify@all",
                )
            # 如果是工作日
            if is_workday(today):
                msg = "写工作日报了! 写工作日报了! 写工作日报了! 别忘记写日报了箱底们呐!!!(补交日期只有30天内, 早写早完事!) [快哭了][凋谢] [快哭了][凋谢] [快哭了][凋谢]"
                for _ in range(3):
                    robot.sendTextMsg(msg, receiver, "notify@all")

            # 如果是本周最后一个工作日
            if ReportReminder.last_work_day_of_week(today) == today:
                msg = "写工作周报了! 写工作周报了! 写工作周报了! 别忘记写周报了箱底们呐!!!(补交日期只有30天内, 早写早完事!) [快哭了][凋谢] [快哭了][凋谢] [快哭了][凋谢]"
                for _ in range(3):
                    robot.sendTextMsg(msg, receiver, "notify@all")

            # 如果本日是本月最后一整周的最后一个工作日:
            if ReportReminder.last_work_friday_of_month(today) == today:
                robot.sendTextMsg(
                    "一个月又过去了喔, 打工快乐!(别忘记补周报日报喔 箱底们呐) [呲牙][强]",
                    receiver,
                    "notify@all",
                )

    # 计算本月最后一个周的最后一个工作日
    @staticmethod
    def last_work_friday_of_month(d: datetime.date) -> datetime.date:
        days_in_month = calendar.monthrange(d.year, d.month)[1]
        weekday = calendar.weekday(d.year, d.month, days_in_month)
        if weekday == 4:
            last_friday_of_month = datetime.date(d.year, d.month, days_in_month)
        else:
            if weekday >= 5:
                last_friday_of_month = datetime.date(
                    d.year, d.month, days_in_month
                ) - datetime.timedelta(days=(weekday - 4))
            else:
                last_friday_of_month = datetime.date(
                    d.year, d.month, days_in_month
                ) - datetime.timedelta(days=(weekday + 3))
        while not is_workday(last_friday_of_month):
            last_friday_of_month = last_friday_of_month - datetime.timedelta(days=1)
        return last_friday_of_month

    # 计算本周最后一个工作日
    @staticmethod
    def last_work_day_of_week(d: datetime.date) -> datetime.date:
        weekday = calendar.weekday(d.year, d.month, d.day)
        last_work_day_of_week = datetime.date(
            d.year, d.month, d.day
        ) + datetime.timedelta(days=(6 - weekday))

        while not is_workday(last_work_day_of_week):
            last_work_day_of_week = last_work_day_of_week - datetime.timedelta(days=1)
        return last_work_day_of_week
