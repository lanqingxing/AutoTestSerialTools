# This is a sample Python script.
import binascii
import ctypes
import struct
import resources_rc
from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIntValidator, QFontMetrics, QIcon
from PyQt5.QtCore import QTranslator, QMetaObject, QTimer, QCoreApplication
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox, QComboBox, QLabel, QActionGroup, QAction, \
    QHBoxLayout, QSplitter, QWidget, QFileDialog


import command_utils
from AutoTest import Ui_MainWindow
from Logger import Logger
from Status import Status
from UpdatePlanBuilder import UpdatePlanBuilder
from UpdatePortListThread import UpdatePortListThread

myappid = "wo de app"
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
# LOG_FORMAT = "%(asctime)s>%(levelname)s>%(process)d>%(processName)s>%(thread)d>%(thread)s>%(module)s>%(lineno)d>%(funcName)s>%(message)s"
# DATE_FORMAT = "%y-%m-%d %H:%M:%S,"
# DATE_FORMAT = "%y-%m-%d %H:%M:%S %p"
__LOG_FORMAT = "%(asctime)s>%(levelname)s>PID:%(process)d %(thread)d>%(module)s>%(funcName)s>%(lineno)d>%(message)s"
# logging.basicConfig(level=logging.DEBUG, format=__LOG_FORMAT, )
# logging.basicConfig(level=logging.ERROR, format=LOG_FORMAT, )

# 是否打印调试信息标志
debug = True
# if debug==True:
#     logging.debug("进入主程序，开始导入包...")
import time
from time import sleep
import os
import sys
import re
import codecs
import threading
# 配置
# 统计线程周期
periodStatistics = 1
import serial
from userSerial import userSerial,suportBandRateList

# 错误替换字符
replaceError = "*E*"
def userCodecsReplaceError(error):
    """
    字符编解码异常处理 直接将错误字节替代为"*E*"
    :param error: UnicodeDecodeError实例
    :return:
    """
    if not isinstance(error, UnicodeDecodeError):
        raise error

    return (replaceError, error.start + 1)

def userCodecsError(error):
    """
    字符编解码异常处理 暂缓+替代
    Error handler for surrogate escape decoding.

    Should be used with an ASCII-compatible encoding (e.g., 'latin-1' or 'utf-8').
    Replaces any invalid byte sequences with surrogate code points.

    As specified in https://docs.python.org/2/library/codecs.html#codecs.register_error.
    """
    # We can't use this with UnicodeEncodeError; the UTF-8 encoder doesn't raise
    # an error for surrogates. Instead, use encode.
    if not isinstance(error, UnicodeDecodeError):
        raise error
    # print(error)
    # print(error.start)
    # print(error.end)
    # print(error.encoding)
    # print(error.object)
    # print(error.reason)
    # 引发异常 待继续接收更多数据后再尝试解码处理
    if error.end - error.start <= 3:
        raise error
    # 从出错位置开始到所处理数据结束，如果数据长度>=5,则第一个字节必然是错误字节，而非未完整接收
    # 此时直接将第一个字节使用*E*代替，并返回下一个字节索引号
    else:
        return (replaceError, error.start + 1)

# 添加自定义解码异常处理handler
codecs.register_error("userCodecsReplaceError",userCodecsReplaceError)
codecs.register_error("userCodecsError",userCodecsError)

class userMain(QMainWindow,Ui_MainWindow):
    def __init__(self, mac_section):
        super().__init__()
        self.log = Logger('all.log', level='debug')
        if debug == True:
            self.log.logger.debug("初始化主程序:")
            # logging.debug("初始化主程序:")
        self.setupUi(self)

        self.update_plan_builder = None
        self.plan = []
        self.flashInfo= {}
        self.localPlatformVersion = None
        self.localAppVersion = None
        self.latestPlatformVersion = None
        self.latestAppVersion = None
        self.mac_section = mac_section
        self.masterMac.setEnabled(False)
        self.slaveMac.setEnabled(True)
        self.masterPin.setEnabled(False)
        self.slavePin.setEnabled(False)
        self.slaveMac_2.setEnabled(False)
        self.slaveMac_3.setEnabled(False)
        self.masterPin_pw.setEnabled(False)
        self.label_Local.hide()
        self.label_progress.hide()
        self.label_Latest.hide()
        # 实例化翻译家
        self.trans = QTranslator()
        self.projects = ["威胜", "泰瑞捷"]  # 初始化的项目数组
        self.project_name = "威胜"
        self.pickerOptions = [
            {
                "chipsType": "ING9188xx/ING9187xx",
                "topAddress": 0x00084000,
                "page_size": 8 * 1024,
                "manual_reboot": True
            },
            {
                "chipsType": "ING9168xx",
                "topAddress": 0x02080000,
                "page_size": 4 * 1024,
                "manual_reboot": False
            }
        ]
        # 设置窗口标志
        # flag = self.windowFlags()
        # self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint,True)  # 窗体总在最前端
        # self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint,True)  # 窗体总在最前端self.textBrowserReceive.setTextInteractionFlags(Qt.NoTextInteraction )
        # 添加chipsType到ComboBox
        for item in self.pickerOptions:
            self.comboBoxChips.addItem(item["chipsType"])

        self.comboBoxProject.addItems(self.projects)
        self.comboBoxProject.currentTextChanged.connect(self.update_command_combo)
        # 初始化串口对象
        self.__comBoxPortBuf = ""#当前使用的串口号
        self.__comPortList = []#系统可用串口号
        self.__com = userSerial(baudrate=115200, timeout=0.1)#实例化串口对象
        self.command_list = []  # 创建一个空数组用于存储 command
        self.utils = command_utils.CommandUtils(self.mac_section, self.project_name)
        self.mac_info = self.utils.mac_info
        self.__commands = self.utils.load_commands_from_ini_t()
        for section, command in self.__commands.items():
            print(f"Section: {section}\r\n")
            print(f"command: {command}")
            self.command_list.append(command)
        # 获取所有 section 名并将其添加到下拉框中
        for section in self.utils.config.sections():
            # 跳过某些特定的 section，如果需要
            if "MAC" in section:
                continue
            self.comboBoxCommand.addItem(section)
        self.command_queue = []
        self.current_command = None
        # 连接ComboBox选择事件
        self.comboBoxChips.currentIndexChanged.connect(self.update_top_address)
        # 设置默认显示
        self.update_top_address()


        self.lineEdit_MTU.setValidator(QIntValidator(0, 99999999))

        # 链接函数
        self.pushButtonSelect.clicked.connect(self.add_path)  # 查找函数，并在lineEdit中显示
        # 初始化成功和失败计数
        self.success_count = 0
        self.fail_count = 0
        # 创建一个定时器，检测2秒超时
        self.timeout_timer = None
        self.connection_status = 0
        self.rssiData = []
        self.__except_commands = False
        self.response_received = False
        self.CheckDevStatus = 0
        # self.timeout_timer.setSingleShot(True)  # 只触发一次

        self.timer_send = QTimer()
        self.timer_send.timeout.connect(self.periodSendThread)
        self.masterMac.addItem(self.mac_info['masterMac'])
        # self.masterMac.setText(self.mac_info['masterMac'])
        self.slaveMac.addItem(self.mac_info['slaveMac'])
        self.slaveMac_2.addItem(self.mac_info['slaveMac_2'])
        self.slaveMac_3.addItem(self.mac_info['slaveMac_3'])
        self.masterPin_pw.addItem(self.mac_info['masterPin_pw'])
        self.masterPin.addItem(self.mac_info['masterPin'])
        self.slavePin.addItem(self.mac_info['slavePin'])

        # 非PyQt控件无法支持自动信号与槽函数连接，必须手动进行
        self.__com.signalRcv.connect(self.on_com_signalRcv)
        self.__com.signalRcvError.connect(self.on_com_signalRcvError)
        self.__com.update_signal.connect(self.update_label)
        self.__com.label_progress_signal.connect(self.showProgress)
        self.__com.progress_signal.connect(self.emitProgress)
        # 创建线程
        self.update_thread = UpdatePortListThread()
        # 连接信号，当线程执行完毕后触发更新UI的函数
        self.update_thread.update_ports_signal.connect(self.__update_comboBoxPortList)
        # 获取可用串口号列表
        newportlistbuf = userSerial.getPortsList()
        self.__update_comboBoxPortList(newportlistbuf)  # 更新系统支持的串口设备并更新端口组合框内容
        self.__update_comboBoxBandRateList()# 更新波特率组合框内容

        self.send_count = 0  # 用于记录发送次数
        self.__txPeriodEnable = False#周期发送使能
        self.__RcvBuff = bytearray()
        self.lineEditPeriodMs.setValidator(QIntValidator(0,99999999))# 周期发送时间间隔验证器
        self.__txPeriod = int(self.lineEditPeriodMs.text())#周期长度ms

        # self.comboBoxSndHistory.setInsertPolicy(QComboBox.InsertAtBottom)

        # 设置发送区字符有效输入范围
        # r"^-?(90|[1-8]?\d(\.\d{1,4})?)$"  匹配-90至90之间，小数点后一至四位小数的输入限制
        # r(^-?180$)|(^-?1[0-7]\d$)|(^-?[1-9]\d$)|(^-?[1-9]$)|^0$");
        # self.textEditSend.setValidator(QIntValidator(0,99999999))
        # self.__textEditMasterMacLast = self.masterMac.text()  # 发送编辑区上次masterMac字符串备份
        # if self.__textEditMasterMacLast != "":
        #     self.masterMac.setText(self.__textEditMasterMacLast)
        # self.__textEditSlaveMacLast = self.slaveMac.text()  # 发送编辑区上次slaveMac字符串备份
        # if self.__textEditSlaveMacLast != "":
        #     self.slaveMac.setText(self.__textEditSlaveMacLast)
        # self.__textEditMasterPinLast = self.masterPin.text()  # 发送编辑区上次masterPin字符串备份
        # if self.__textEditMasterPinLast != "":
        #     self.masterPin.setText(self.__textEditMasterPinLast)
        self.__periodSendBuf = bytearray()#周期发送时 发送数据缓存

        # 设置定时器
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self.scroll_text)
        # self.scroll_timer.start(1000)  # 每100毫秒滚动一次
        # self.masterPin_pw.setSelection(0, 0)
        # self.masterPin_pw.setCursorPosition(0)
        # self.slavePin.setSelection(0, 0)
        # self.slavePin.setCursorPosition(0)
        self.scroll_index = 0  # 当前滚动的起始位置

        # self.pushButtonClearHello.addAction(self.actionClearReceive)

        if debug == True:
            self.log.logger.debug("当前系统可用端口:{}".format(self.__comPortList))
            # logging.debug("当前系统可用端口:{}".format(self.__comPortList))
            # logging.debug("初始化主程序完成")
            self.log.logger.debug("初始化主程序完成")

    def update_command_combo(self, project_name):
        """
        根据选择的项目更新指令下拉框的内容
        """
        print(f"project_name: {project_name}")
        self.project_name = project_name
        self.comboBoxCommand.clear()
        self.command_list.clear()
        self.utils = command_utils.CommandUtils(self.mac_section, self.project_name)
        self.mac_info = self.utils.mac_info
        self.__commands = self.utils.load_commands_from_ini_t()
        for section, command in self.__commands.items():

            self.command_list.append(command)
        # 获取所有 section 名并将其添加到下拉框中
        for section in self.utils.config.sections():
            # 跳过某些特定的 section，如果需要
            if "MAC" in section:
                continue
            self.comboBoxCommand.addItem(section)
        self.masterMac.clear()
        self.slaveMac.clear()
        self.slaveMac_2.clear()
        self.slaveMac_3.clear()
        self.masterPin_pw.clear()
        self.masterPin.clear()
        self.slavePin.clear()
        print(f"self.mac_info-----: {self.mac_info}")
        self.masterMac.addItem(self.mac_info['masterMac'])
        # self.masterMac.setText(self.mac_info['masterMac'])
        self.slaveMac.addItem(self.mac_info['slaveMac'])
        self.slaveMac_2.addItem(self.mac_info['slaveMac_2'])
        self.slaveMac_3.addItem(self.mac_info['slaveMac_3'])
        self.masterPin_pw.addItem(self.mac_info['masterPin_pw'])
        self.masterPin.addItem(self.mac_info['masterPin'])
        self.slavePin.addItem(self.mac_info['slavePin'])

    def add_path(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 ZIP 文件", "", "ZIP Files (*.zip)")
        if file_path:
            if self.__com.getPortState() == True:
                # print('开始获取版本号------------')
                self.send_command(self.utils.send_commands_get_version_0000002E())
            self.lineEditZipPath.setText(file_path)
            self.update_plan_builder = UpdatePlanBuilder(file_path)
            self.update_plan_builder.start()  # 启动线程
            # self.build_update_plan()

        else:
            self.log.logger.info("未选择 ZIP 文件")
            print("未选择 ZIP 文件")

    def build_update_plan(self):
        """构建更新计划，将 platform、app 和 bins 添加到计划中"""
        if not self.update_plan_builder:
            print("No update_plan_builder available, returning empty plan.")
            self.log.logger.warning("No update_plan_builder available, returning empty plan.")
            return []
        if not self.update_plan_builder.data:
            self.label_Latest.hide()
            self.log.logger.warning("No data available, returning empty plan.")
            print("No data available, returning empty plan.")
            return []
        # print("----------------------------.",self.update_plan_builder.data)
        plan = []
        # self.textBrowserReceive.insertHtml(
        #     f"本地zip文件json内容是，<br><span style='color:red;'>{self.update_plan_builder.manifest}</span>")
        # self.textBrowserReceive.insertHtml("<br>")
        is_update_platform = False
        is_update_app = False
        if 'platform_merge_app' in self.update_plan_builder.data:
            is_update_platform = False
            is_update_app = True
            platform_merge_app = self.update_plan_builder.data['platform_merge_app']
            platform_version_str = '.'.join([f"{byte}" for byte in platform_merge_app['platform_version']])
            print("self.localPlatformVersion-----platform_merge_app---=", platform_version_str)
            app_version_str = '.'.join([f"{byte}" for byte in platform_merge_app['app_version']])
            print("self.localAppVersion-----platform_merge_app----=", app_version_str)
            self.latestPlatformVersion = platform_version_str
            self.latestAppVersion = app_version_str
            self.label_Latest.setText(f"Latest: app:{self.latestAppVersion} | platform:{self.latestPlatformVersion}")
            self.label_Latest.show()
            plan.append({
                "name": platform_merge_app['name'],
                "address": platform_merge_app['address'],
                "data": platform_merge_app['data']
            })
        else:

            # 添加 platform 和 app 到更新计划
            if 'platform' in self.update_plan_builder.data:
                # print("self.localPlatformVersion--------=", self.localPlatformVersion)
                # print("self.localAppVersion---------=", self.localAppVersion)

                platform_version_str = '.'.join([f"{byte}" for byte in self.update_plan_builder.data['platform']['version']])
                # print("self.localPlatformVersion-----xxxxx---=", platform_version_str )
                app_version_str = '.'.join([f"{byte}" for byte in self.update_plan_builder.data['app']['version']])
                # print("self.localAppVersion-----xxxxx----=", app_version_str)
                is_update_platform = self.localPlatformVersion != platform_version_str
                is_update_app = is_update_platform or self.localAppVersion != app_version_str
                # print("isUpdatePlatform--------=", is_update_platform)
                # print("isUpdateApp---------=", is_update_app)
                self.latestPlatformVersion = platform_version_str
                self.latestAppVersion = app_version_str
                self.label_Latest.setText(
                    f"Latest: app:{self.latestAppVersion} | platform:{self.latestPlatformVersion}")
                self.label_Latest.show()
            else:
                is_update_platform = False
                is_update_app = True


            if is_update_platform:
                plan.append({
                    "name": self.update_plan_builder.data['platform']['name'],
                    "address": self.update_plan_builder.data['platform']['address'],
                    "data": self.update_plan_builder.data['platform']['data']
                })
            if is_update_app:
                plan.append({
                    "name": self.update_plan_builder.data['app']['name'],
                    "address": self.update_plan_builder.data['app']['address'],
                    "data": self.update_plan_builder.data['app']['data']
                })

        # print("isUpdatePlatform=", is_update_platform)
        # print("isUpdateApp=", is_update_app)
        # print("plan length=-----------", len(plan))
        # print("buildUpdatePlan plan=", plan)
        # print("buildUpdatePlan binsPlan=", len(self.update_plan_builder.data.get('bins', [])))
        # 添加 bins 到更新计划
        for bin_info in self.update_plan_builder.data['bins']:
            # print("bin_info plan=", bin_info)
            if 'data' in bin_info:
                plan.append(bin_info)

        if len(plan) < 1:
            return plan

        # print("plan length=", len(plan))
        top_address = self.flashInfo["topAddress"]
        page_size = self.flashInfo["page_size"]
        for item in plan:
            # print("item data length=", len(item['data']))
            print("top=", hex(top_address))
            padding = 4 - (len(item['data']) % 4)
            print("padding=", padding)

            if padding != 4:
                new_data = bytearray(len(item['data']) + padding)
                new_data[:len(item['data'])] = item['data']
                item['data'] = new_data

            page_num = (len(item['data']) + page_size - 1) // page_size
            print("page_num=", page_num)
            top_address -= page_num * page_size
            print("top end=", hex(top_address))

            if 'writeAddress' in item:
                item['write_addr'] = item['writeAddress']
            else:
                item['write_addr'] = top_address
        # print("buildUpdatePlan plan=", plan)
        return plan
        
    def update_top_address(self):
        # 获取当前选中的 chipsType 的 topAddress
        index = self.comboBoxChips.currentIndex()
        if index >= 0:
            top_address = self.pickerOptions[index]["topAddress"]
            self.flashInfo = self.pickerOptions[index]
            self.lineEdit_TopAddress.setText(f"{hex(top_address)}")
            self.plan = self.build_update_plan()
    def scroll_text(self):
        text = self.masterPin_pw.text()
        self.scroll_index += 1
        if self.scroll_index > len(text):  # 重新开始滚动
            self.scroll_index = 0
        self.masterPin_pw.setText(text[self.scroll_index:] + text[:self.scroll_index])
# 串口配置相关
#     更新系统支持的串口设备并更新端口组合框内容
    def __update_comboBoxPortList(self,newportlistbuf):
        start = time.time()
        # 获取可用串口号列表
        # newportlistbuf = userSerial.getPortsList()
        if self.__comBoxPortBuf == "" or  newportlistbuf != self.__comPortList:
            self.__comPortList = newportlistbuf

            if len(self.__comPortList) > 0:
                # 将串口号列表更新到组合框
                self.comboBoxPort.setEnabled(False)
                self.comboBoxPort.clear()
                self.comboBoxPort.addItems([self.__comPortList[i][0] for i in range(len(self.__comPortList))])

                # self.__comBoxPortBuf为空值 默认设置为第一个串口
                if self.__comBoxPortBuf == "":
                    self.__comBoxPortBuf = self.__comPortList[0][0]
                else:
                    # 遍历当前列表 查找是否上次选定的串口在列表中出现，如果出现则选中上次选定的串口
                    seq = 0
                    for i in self.__comPortList:
                        if i[1] == self.__comBoxPortBuf:
                            self.comboBoxPort.setCurrentIndex(seq)
                            break
                        seq+=1
                    # 全部遍历后发现上次选定串口无效时，设置第一个串口
                    else:
                        self.__comBoxPortBuf = self.__comPortList[0][0]

                self.comboBoxPort.setEnabled(True)
                if debug == True:
                    # logging.debug("更新可用串口列表")
                    self.log.logger.debug("更新可用串口列表")

            else:
                self.comboBoxPort.setEnabled(False)
                self.comboBoxPort.clear()
                self.__comBoxPortBuf = ""

                _translate = QtCore.QCoreApplication.translate
                self.comboBoxPort.addItem(_translate("AssistantLXL", "No Port Can Be Use"))
                # self.comboBoxPort.setEnabled(True)
                if debug == True:
                    # logging.warning("更新可用串口列表：无可用串口设备")
                    self.log.logger.warning("更新可用串口列表：无可用串口设备")
        else:
            if debug == True:
                self.log.logger.debug("更新可用串口列表：列表未发生变化")
                # logging.debug("更新可用串口列表：列表未发生变化")

        stop = time.time()
        if debug == True:
            self.log.logger.debug("更新串口列表时间{}s".format(stop-start))
            # logging.debug("更新串口列表时间{}s".format(stop-start))

    # self.comboBoxPort.activated[str].connect(self.onActivated)  # 手动触发时启动
    # self.comboBoxPort.enterEventSignal.connect(self.on_comboBoxPort_enterEventSignal)
    # def on_comboBoxPort_currentIndexChanged(self, text):#选中组合框中与当前不同的项目时触发
    @QtCore.pyqtSlot(str)
    def on_comboBoxPort_activated(self, text):# 手动触发时启动
        if isinstance(text,int):
            if debug == True:
                self.log.logger.debug("更换选中串口号:{}".format(text))
                # logging.debug("更换选中串口号:{}".format(text))
        if isinstance(text,str):
            if debug == True:
                self.log.logger.debug("更换选中串口号:{}".format(text))
                # logging.debug("更换选中串口名称:{}".format(text))
            if(text != ""):
                # 切换串口前，如果当前为已打开端口则关闭端口
                # if self.__com.getPortState() == True:
                #     self.on_pushButtonOpen_toggled(False)
                self.__comBoxPortBuf = text

    # 鼠标移入控件事件 原定移入时更新串口设备列表
    @QtCore.pyqtSlot()
    def on_comboBoxPort_enterEventSignal(self):
        if debug == True:
            # logging.debug("鼠标移入comboBoxPort控件，即将更新串口列表")
            # logging.debug("鼠标移入comboBoxPort控件")
            self.log.logger.debug("鼠标移入comboBoxPort控件")
        # self.__update_comboBoxPortList()# 由于系统调用时间过长，取消自动更新为手动更新
    # def on_comboBoxPort_dropdown(self,event):
    #     print(event)
    #
    # def on_comboBoxPort_mousePressEvent(event):
    #     print(event)
    # 更新波特率组合框
    def __update_comboBoxBandRateList(self):
        # 将串口号列表更新
        self.comboBoxBand.setEnabled(False)
        self.comboBoxBand.clear()
        self.comboBoxBand.addItems([str(i) for i in suportBandRateList])
        # 设置默认波特率
        self.comboBoxBand.setCurrentText("115200")
        # print(self.comboBoxBand.currentIndex())
        self.comboBoxBand.setEnabled(True)

    # self.comboBoxBand
    # def on_comboBoxBand_currentIndexChanged(self,text):
    @QtCore.pyqtSlot(str)
    def on_comboBoxBand_activated(self, text):
        if isinstance(text,str):
            try:
                self.__com.port.baudrate = (int(text))
                if debug == True:
                    self.log.logger.debug("更新波特率:{}".format(self.__com.port.baudrate))
                    # logging.debug("更新波特率:{}".format(self.__com.port.baudrate))
            except Exception as e:
                if debug == True:
                    self.log.logger.debug("更新波特率:{}".format(e))
                    # logging.error("更新波特率:{}".format(e))

    @QtCore.pyqtSlot()
    def on_pushButtonClose_clicked(self):
        #  关闭当前打开的串口
        self.timer_send.stop()
        if self.__com.getPortState() == True:
            self.__com.port.close()
            self.pushButtonSend.setEnabled(True)
            self.singleButtonSend.setEnabled(True)
            self.eButtonSend.setEnabled(True)
            self.send_count = 0
            self.__except_commands = False
            if debug == True:
                self.log.logger.debug("端口{}已关闭".format(self.__comBoxPortBuf))
                # logging.debug("端口{}已关闭".format(self.__comBoxPortBuf))
        else:
            if debug == True:
                self.log.logger.debug("端口{}未打开".format(self.__comBoxPortBuf))
                # logging.debug("端口{}未打开".format(self.__comBoxPortBuf))
        self.__pushButtonOpen_State_Reset()
    # # 打开/关闭开关
    # self.pushButtonOpen
    # def on_pushButtonOpen_pressed(self):
    @QtCore.pyqtSlot()
    def on_pushButtonOpen_clicked(self):
    #  打开指定串口
        portBuf = self.__comBoxPortBuf
        # 在端口列表中搜索当前串口名称对应的端口号
        # seq = 0
        # for i in self.__comPortList:
        #     if i[1] == self.__comBoxPortBuf:
        #         portBuf  = i[0]
        #         break
        #     seq+=1

        if (portBuf != ""):
            try:

                self.__com.port.bytesize = int(self.DataBit.currentText())
                self.__com.port.stopbits = int(self.stopbits.currentText())
                self.__com.port.parity = self.Paritybits.currentText()
                self.__com.open(portBuf)

                if debug == True:
                    self.log.logger.debug("端口{}已打开".format(portBuf))
                    self.log.logger.debug("DataBit---{}".format(self.DataBit.currentText()))
                    self.log.logger.debug("stopbits---{}".format(self.stopbits.currentText()))
                    self.log.logger.debug("Paritybits---{}".format(self.Paritybits.currentText()))
                    # logging.debug("DataBit---{}".format(self.DataBit.currentText()))
                    # logging.debug("stopbits---{}".format(self.stopbits.currentText()))
                    # logging.debug("Paritybits---{}".format(self.Paritybits.currentText()))
                    # logging.debug("端口{}已打开".format(portBuf))

                self.pushButtonOpen.setEnabled(False)
                self.pushButtonClose.setEnabled(True)
                self.comboBoxBand.setEnabled(False)
                self.comboBoxPort.setEnabled(False)
                self.DataBit.setEnabled(False)
                self.stopbits.setEnabled(False)
                self.Paritybits.setEnabled(False)


            except Exception as e:
                # self.__NullLabel.setText(e.args[0].args[0])
                if debug == True:
                    self.log.logger.error("端口{}打开出错".format(e))
                    # logging.error("端口{}打开出错".format(e))
                QMessageBox.critical(self, "Port Error", "此串口不能被打开！串口被占用或参数错误！")
                # return None

        else:
            if debug == True:
                self.log.logger.debug("无可用串口")
                # logging.debug("无可用串口")
            self.__pushButtonOpen_State_Reset()

    def parse_packet(self, byte_list):
        # 跳过同步字节 FE FE FE FE
        header = byte_list[:4]
        if header != [0xFE, 0xFE, 0xFE, 0xFE]:
            if debug == True:
                self.log.logger.debug("Response parsed Fail:Invalid header(0xFE, 0xFE, 0xFE, 0xFE).")
            self.textBrowserReceive.insertPlainText("Response parsed Fail:Invalid header(0xFE, 0xFE, 0xFE, 0xFE).")
            self.textBrowserReceive.insertPlainText("\r\n")
            self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)  # 将坐标移动到文本结尾，
            return

        # 报文起始符
        start_byte = byte_list[4]
        if start_byte != 0x68:
            if debug == True:
                self.log.logger.debug("Response parsed Fail:Invalid start byte(0x68).")
            self.textBrowserReceive.insertPlainText("Response parsed Fail:Invalid start byte(0x68).")
            self.textBrowserReceive.insertPlainText("\r\n")
            self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)  # 将坐标移动到文本结尾，
            return
            # 长度 L (两个字节)
        length_bytes = byte_list[5:7][::-1]
        length = length_bytes[0] * 256 + length_bytes[1]  # 将两个字节组合为一个整数
        # logging.debug("Parsed Length: 0x{:02X}".format(length))

        # 类型 T (一个字节)
        type_byte = byte_list[7]
        # logging.debug("Parsed Type: 0x{:02X}".format(type_byte))
        # 解析地址（6字节）
        # C0~C3 (接下来的四个字节)
        control_code = byte_list[8:12][::-1]
        # logging.debug("Parsed C0~C3: {}".format([hex(b) for b in control_code]))
        control_code_str = ''.join([f"{byte:02X}" for byte in control_code])
        # logging.debug("address_str:{}".format(control_code_str))


        # A5~A0 (接下来的六个字节)
        address = byte_list[12:18]
        # logging.debug("Parsed A5~A0: {}".format([hex(b) for b in address]))
        address_str = ''.join([f"{byte:02X}" for byte in address])
        # logging.debug("Parsed A5~A0_str:{}".format(address_str))
        # R0~R3 (接下来的四个字节)
        R = byte_list[18:22]
        # logging.debug("Parsed R0~R3: {}".format([hex(b) for b in R]))
        # 报文结束符
        end_byte = byte_list[22]
        if end_byte != 0x68:
            if debug == True:
                self.log.logger.debug("Response parsed Fail:Invalid end byte(0x68).")
            self.textBrowserReceive.insertPlainText("Response parsed Fail:Invalid end byte(0x68).")
            self.textBrowserReceive.insertPlainText("\r\n")
            self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)  # 将坐标移动到文本结尾，
            return

            # D0~Dn (接下来的 N 个字节，N 为长度 L 的值)
        data_field = byte_list[23:23 + length]
        # logging.debug("Parsed D0~Dn: {}".format([hex(b) for b in data_field]))
        data_field_str = ''.join([f"{byte:02X}" for byte in data_field])
        # logging.debug("Parsed D0~Dn_str:{}".format(data_field_str))
        # 校验和 CS (倒数第二个字节)
        checksum = byte_list[23 + length]
        # logging.debug("Parsed Checksum: 0x{:02X}".format(checksum))

        # 报文结束符
        final_end_byte = byte_list[24 + length]
        # logging.debug("final_end_byte: 0x{:02X}".format(final_end_byte))
        if final_end_byte != 0x16:
            if debug == True:
                self.log.logger.debug("Response parsed Fail:Invalid final end byte(0x16).")
            self.textBrowserReceive.insertPlainText("Response parsed Fail:Invalid final end byte(0x16).")
            self.textBrowserReceive.insertPlainText("\r\n")
            self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)  # 将坐标移动到文本结尾，
            return

        # 计算校验和
        calculated_checksum = sum(byte_list[4:23 + length]) % 256

        # 校验校验和
        if checksum != calculated_checksum:
            if debug == True:
                self.log.logger.debug(f"Response parsed Fail:Invalid checksum: expected {calculated_checksum}, got {checksum}")
            self.textBrowserReceive.insertPlainText(f"Response parsed Fail:Invalid checksum: expected {calculated_checksum}, got {checksum}")
            self.textBrowserReceive.insertPlainText("\r\n")
            self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)  # 将坐标移动到文本结尾，
            return
        if debug == True:
            self.log.logger.debug("Parsed Length: 0x{:02X}".format(length))
            self.log.logger.debug("Parsed Type: 0x{:02X}".format(type_byte))
            self.log.logger.debug("Parsed C0~C3: {}".format([hex(b) for b in control_code]))
            self.log.logger.debug("Parsed A5~A0: {}".format([hex(b) for b in address]))
            self.log.logger.debug("Parsed R0~R3: {}".format([hex(b) for b in R]))
            self.log.logger.debug("Parsed D0~Dn: {}".format([hex(b) for b in data_field]))
            self.log.logger.debug("Parsed Checksum: 0x{:02X}".format(checksum))
            self.log.logger.debug("final_end_byte: 0x{:02X}".format(final_end_byte))
            self.log.logger.debug("calculated_checksum: 0x{:02X}".format(calculated_checksum))
        # logging.debug("calculated_checksum: 0x{:02X}".format(calculated_checksum))
        # 打印解析结果
        return {
            "length": f"{length:02X}",
            "type": f"{type_byte:02X}",
            "code": control_code_str,
            "address": address,
            "data": data_field
        }

    def __pushButtonOpen_State_Reset(self):
        _translate = QtCore.QCoreApplication.translate
        # self.pushButtonOpen.setText(_translate("AssistantLXL", "Open"))
        # 设置Checked状态会导致on_pushButtonOpen_toggled触发
        self.pushButtonOpen.setEnabled(True)
        self.pushButtonClose.setEnabled(True)
        # self.pushButtonOpen.setChecked(True)  # 使按钮处于选中状态
        self.comboBoxBand.setEnabled(True)
        self.comboBoxPort.setEnabled(True)
        self.DataBit.setEnabled(True)
        self.stopbits.setEnabled(True)
        self.Paritybits.setEnabled(True)

    @QtCore.pyqtSlot()
    def on_pushButtonUpdateini_pressed(self):
        self.comboBoxCommand.clear()
        self.command_list.clear()
        self.utils = command_utils.CommandUtils(self.mac_section, self.project_name)
        self.mac_info = self.utils.mac_info
        self.__commands = self.utils.load_commands_from_ini_t()
        for section, command in self.__commands.items():
            print(f"Section: {section}\r\n")

            self.command_list.append(command)
        # 获取所有 section 名并将其添加到下拉框中
        for section in self.utils.config.sections():
            # 跳过某些特定的 section，如果需要
            if "MAC" in section:
                continue
            self.comboBoxCommand.addItem(section)
        self.masterMac.clear()
        self.slaveMac.clear()
        self.slaveMac_2.clear()
        self.slaveMac_3.clear()
        self.masterPin_pw.clear()
        self.masterPin.clear()
        self.slavePin.clear()

        self.masterMac.addItem(self.mac_info['masterMac'])
        # self.masterMac.setText(self.mac_info['masterMac'])
        self.slaveMac.addItem(self.mac_info['slaveMac'])
        self.slaveMac_2.addItem(self.mac_info['slaveMac_2'])
        self.slaveMac_3.addItem(self.mac_info['slaveMac_3'])
        self.masterPin_pw.addItem(self.mac_info['masterPin_pw'])
        self.masterPin.addItem(self.mac_info['masterPin'])
        self.slavePin.addItem(self.mac_info['slavePin'])
    # 串口设备更新按键
    @QtCore.pyqtSlot()
    def on_pushButtonUpdate_pressed(self):
        if debug == True:
            self.log.logger.debug("更新串口设备开始")
            # logging.debug("更新串口设备开始")
        # self.__update_comboBoxPortList()
       # 启动更新串口列表的线程
        self.update_thread.start()
        if debug == True:
            self.log.logger.debug("更新串口设备结束")
            # logging.debug("更新串口设备结束")

#     # 周期发送使能
#     self.checkBoxTxPeriodEnable
    @QtCore.pyqtSlot(bool)
    def on_checkBoxTxPeriodEnable_toggled(self,checked):
        self.__txPeriodEnable = checked
        print(f"on_checkBoxTxPeriodEnable_toggled: {self.__txPeriodEnable}")
        if self.__txPeriodEnable == True:  # 周期发送使能
            self.comboBoxCommand.setEnabled(False)
            self.lineEditPeriodMs.setEnabled(False)
            self.singleButtonSend.setEnabled(False)
            self.eButtonSend.setEnabled(False)
            self.__except_commands = False
            self.pushButtonSend.setEnabled(False)
            self.success_count = 0
            self.send_count = 0
            self.timer_send.start(int(self.lineEditPeriodMs.text()))
        else:
            self.timer_send.stop()
            timer = threading.Timer(6.0, self.send_count_timeout)
            timer.start()

            # self.textBrowserReceive.insertPlainText("停止定时发送指令，开始重置！！！")
            # self.textBrowserReceive.insertPlainText("\r\n")
            # self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)  # 将坐标移动到文本结尾，
            self.pushButtonSend.setEnabled(True)
            self.comboBoxCommand.setEnabled(True)
            self.lineEditPeriodMs.setEnabled(True)
            self.singleButtonSend.setEnabled(True)
            self.eButtonSend.setEnabled(True)
        if debug == True:
            self.log.logger.debug("更新周期发送使能:{}".format(checked))
            # logging.debug("更新周期发送使能:{}".format(checked))
    @QtCore.pyqtSlot(str)
    def on_masterMac_textChanged(self, text):
        if (text != ""):  #
            print(f"currMasterMac: {text}")
            self.__textEditMasterMacLast = text

    @QtCore.pyqtSlot(str)
    def on_slaveMac_textChanged(self, text):
        if (text != ""):  #
            print(f"slaveMac: {text}")
            self.__textEditSlaveMacLast = text

    @QtCore.pyqtSlot(str)
    def on_masterPin_textChanged(self, text):
        if (text != ""):  #
            print(f"masterPin: {text}")
            self.__textEditMasterPinLast = text
#     # 发送周期
#     self.lineEditPeriodMs
    @QtCore.pyqtSlot(str)
    def on_lineEditPeriodMs_textChanged(self,text):
        if (text != "" and text != "0"):#
            # 当text是0时，lstrip("0")将导致字符串结果是""
            self.lineEditPeriodMs.setText((self.lineEditPeriodMs.text().lstrip('0')))
            self.__txPeriod = int(text)
        else:#空或者0
            self.lineEditPeriodMs.setText("0")
            self.__txPeriod = 0
        if debug == True:
            self.log.logger.debug("更新周期发送时间设置:text-->{}  period-->{}".format(text, self.__txPeriod))
            # logging.debug("更新周期发送时间设置:text-->{}  period-->{}".format(text, self.__txPeriod))

#     #接收显示区
#     self.textBrowserReceive
#     def __textBrowserReceiveRefresh(self):
    @QtCore.pyqtSlot()
    def on_textBrowserReceive_textChanged(self):
        """
        文本浏览器textChanged槽函数
            文本浏览器中文本改变时将光标移动到末尾
        :return:
        """
        # self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)
        pass

    # self.com.signalRcv
    # 非PyQt控件无法支持自动信号与槽函数连接，必须手动进行
    @QtCore.pyqtSlot(int)
    def on_com_signalRcv(self,count):
        if debug == True:
            self.log.logger.debug("串口接收:{}".format(count))
            # logging.debug("串口接收:{}".format(count))

        self.__RcvBuff = self.__com.recv(count)
        if len(self.__RcvBuff) != 0 :
            if debug == True:
                # logging.debug("原始数据:{}".format(bytebuf))

                data =" ".join(["{:02X}".format(i) for i in self.__RcvBuff])
                self.log.logger.debug(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},当前窗口:{self.mac_section},接收到的原始数据:{data}")
                print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},当前窗口:{self.mac_section},接收到的原始数据:{data}")
                self.textBrowserReceive.insertPlainText(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},接收到的原始数据:{data}")
                self.textBrowserReceive.insertPlainText("\r\n")
                self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)  # 将坐标移动到文本结尾，
                # 将接收到的字节转换为列表
            byte_list = list(self.__RcvBuff)

            parsed_result = self.parse_packet(byte_list)
            print(parsed_result)
            if self.project_name == "威胜":
                self.parsed_ws_result(parsed_result)
            elif self.project_name == "泰瑞捷":
                self.parsed_trj_result(parsed_result)
            else:
                self.parsed_result(parsed_result)
        else:
            if debug == True:
                self.log.logger.error("串口接收异常:应接收{},实际未读取到任何数据".format(count))

                # logging.error("串口接收异常:应接收{},实际未读取到任何数据".format(count))

    def convert_to_datetime(self, data):
        """
        将大端格式的 24 字节 ASCII 码转为 datetime 对象
        :param data: 字节数据 (24 字节)
        :return: datetime 对象
        """
        # 转换 ASCII 数据为字符串
        ascii_string = ''.join(chr(byte) for byte in data if byte != 0)
        # 解析字符串格式为时间
        time_obj = datetime.strptime(ascii_string, "%b %d %Y %H:%M:%S")
        return time_obj
    def parse_passkey_status(self, status_byte):
        """
        解析连接状态标识字段
        :param status_byte: 1 字节的状态值 (int 类型)
        :return: 一个字典，包含每个连接状态
        """
        connections = {
            "主机 1": bool(status_byte & (1 << 0)),
            "从机 1": bool(status_byte & (1 << 1)),
            "从机 2": bool(status_byte & (1 << 2)),
            "从机 3": bool(status_byte & (1 << 3)),
        }
        # 返回连接状态为 True 的设备的 key 集合
        return [key for key, status in connections.items() if status]
    def parse_connection_status(self, status_byte):
        """
        解析连接状态标识字段
        :param status_byte: 1 字节的状态值 (int 类型)
        :return: 一个字典，包含每个连接状态
        """
        connections = {
            "主机 1": bool(status_byte & (1 << 0)),
            "主机 2": bool(status_byte & (1 << 1)),
            "从机 1": bool(status_byte & (1 << 2)),
            "从机 2": bool(status_byte & (1 << 3)),
            "从机 3": bool(status_byte & (1 << 4)),
        }
        # 返回连接状态为 True 的设备的 key 集合
        return [key for key, status in connections.items() if status]

    def parse_device_data_dynamic(self, data):
        idx = 0  # 当前索引

        def get_next_field(length):
            nonlocal idx
            field_data = data[idx:idx + length]  # 获取当前字段数据
            idx += length  # 更新索引位置
            return field_data

        # 获取长度字段（假设长度字段在第一个字节）
        length = data[idx]  # 第一个字节是长度
        idx += 1  # 移动索引

        # 获取设备地址（假设为6字节）
        device_address = get_next_field(6)
        print(f"device_address: {device_address}")
        # 获取RSSI值（2字节，带符号）
        rssi = int.from_bytes(get_next_field(2), byteorder="little", signed=True)
        print(f"rssi: {rssi}")
        # 获取广告标志（3字节）
        adv_flag = get_next_field(3)
        print(f"adv_flag: {adv_flag}")
        manufacturer_flag = get_next_field(2)
        print(f"manufacturer_flag: {manufacturer_flag}")
        # 获取设备类别码（1字节）
        device_category = get_next_field(1)
        print(f"device_category: {device_category}")
        # 获取厂商代码（2字节）
        manufacturer_code = get_next_field(2)
        print(f"manufacturer_code: {manufacturer_code}")
        # 获取自动配对校验码（2字节）
        auto_pair_code = get_next_field(2)
        print(f"auto_pair_code: {auto_pair_code}")
        # 获取连接PIN码密文（16字节）
        pin_code_cipher = get_next_field(16)
        print(f"pin_code_cipher: {pin_code_cipher}")
        device_flag = get_next_field(2)
        print(f"device_flag: {device_flag}")
        # 获取设备名称（最后3字节）
        device_name = get_next_field(3) # 设备名称（3字节ASCII）
        print(f"device_name: {device_name}")
        # 返回解析结果
        return {
            "设备信息数据长度:": length,
            "设备地址:": ":".join(f"{byte:02X}" for byte in device_address),
            "RSSI 值:": rssi,
            "广播数据标志(长度-类型-值):": "-".join(f"{byte:02X}" for byte in adv_flag),
            "厂商指定数据标志(长度-类型):": "-".join(f"{byte:02X}" for byte in manufacturer_flag),
            "设备类别码:": "".join(f"{byte:02X}" for byte in device_category),
            "厂商代码:": "".join(f"{byte:02X}" for byte in manufacturer_code),
            "断 路 器 自 动 配 对 校 验 码:": "".join(f"{byte:02X}" for byte in auto_pair_code),
            "连接 PIN 码密文:": "".join(f"{byte:02X}" for byte in pin_code_cipher),
            "广播设备名称标志(长度-类型):": "-".join(f"{byte:02X}" for byte in device_flag),
            "设备名称:": ''.join(chr(byte) for byte in device_name if byte != 0),
        }
    def parsed_trj_result(self,parsed_result):
        if parsed_result:
            self.response_received = True
            # logging.debug("Response parsed successfully.")
            code = parsed_result['code']
            # logging.debug("Parsed code:{}".format(code))
            length = parsed_result['length']
            type = parsed_result['type']
            data = parsed_result['data']
            macAddress = parsed_result['address']
            data_field_str = ' '.join([f"{byte:02X}" for byte in data])
            if debug == True:
                self.log.logger.debug("开始进行数据解析......\r\n")
            # logging.debug("Parsed D0~Dn_str:{}".format(data_field_str))
            self.textBrowserReceive.insertPlainText("开始进行数据解析......\r\n")
            self.textBrowserReceive.insertPlainText("\r\n")
            self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)  # 将坐标移动到文本结尾，
            if code == '00000007':
                last_six_data = data[-6:]  # 获取最后六个字节

                # 反向读取地址
                address = last_six_data[::-1]  # 反转地址字节序列

                # 打印结果
                # logging.debug("Last six bytes of data: {}".format(last_six_data))
                # logging.debug("Reversed address: {}".format(address))

                # 如果想以十六进制格式打印：
                last_six_data_hex = ''.join([f"{byte:02X}" for byte in last_six_data])
                address_hex = ''.join([f"{byte:02X}" for byte in address])

                # logging.debug(f"Last six bytes (hex): {last_six_data_hex}")
                # logging.debug(f"Reversed address (hex): {address_hex}")

                # 输出
                # print(f"Last six bytes (hex): {last_six_data_hex}")
                # print(f"Reversed address (hex): {address_hex}")
                if debug == True:
                    self.log.logger.debug("Last six bytes of data: {}".format(last_six_data))
                    self.log.logger.debug("Reversed address: {}".format(address))
                    self.log.logger.debug(f"Last six bytes (hex): {last_six_data_hex}")
                    self.log.logger.debug(f"Reversed address (hex): {address_hex}")
                    self.log.logger.debug(f"指令{code}解析成功，<br>数据域是{data_field_str}")

                self.textBrowserReceive.insertHtml(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
                self.send_command(self.utils.send_commands_trj00000007())
            elif code == '0000001B':

                # print(f"version: {version_DEC}")
                if debug == True:
                    self.log.logger.debug(f"指令{code}解析成功，<br>数据域是{data_field_str},设备固件编译时间是{self.convert_to_datetime(data)}")
                self.textBrowserReceive.insertHtml(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str},<br>设备固件编译时间是<span style='color:red;'>{self.convert_to_datetime(data)}</span>")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == '00000008':
                # 初始化 platform 数组
                version = [0, 0, 0]
                v = data[::-1]
                # logging.debug("version_data: {}".format(v))
                # 解析字节并进行位移操作
                version[0] = v[0]   # 第一个元素
                version[1] = v[1]  # 第二个元素，v[2]
                version[2] = v[3] + (v[2] << 8)   # 第三个元素，v[3]
                # print(f"version: {version}")
                version_DEC = '.'.join([f"{byte}" for byte in version])
                # print(f"version: {version_DEC}")
                if debug == True:
                    self.log.logger.debug(f"指令{code}解析成功，<br>数据域是{data_field_str},版本号是{version_DEC}")
                self.textBrowserReceive.insertHtml(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str},<br>版本号是<span style='color:red;'>{version_DEC}</span>")
                self.textBrowserReceive.insertHtml("<br>")

            elif code == '0000001D':
                if debug == True:
                    self.log.logger.debug(f"指令{code}解析成功，<br>数据域是{data_field_str},模组 SN 号是{data_field_str}")
                self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<br>模组 SN 号是<span style='color:red;'>{data_field_str}</span>")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == 'F20B0000':
                data_field = ''.join([f"{byte:02X}" for byte in data])
                if type == 'C2':
                    if Status.is_valid_status(data[0]):
                        print(f"状态码 {data_field} 表示: {Status.get_status_name(data[0])}")
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，{Status.get_status_name(data[0])}")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>{Status.get_status_name(data[0])}</span> ")
                    else:
                        print(f"状态码 {data_field} 未定义")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，状态码 {data_field} 未定义")
                elif type == '83':
                    # 连接状态标识
                    self.connection_status = data[0]
                    print(f"Connection Status: 0x{self.connection_status:02X} ")
                    status_dict = self.parse_passkey_status(self.connection_status)
                    print(f"status_dict: {status_dict}")
                    # 用来存储解析后的结果
                    passkey_addresses = {}
                    start_index = 1  # 数据的起始位置

                    for key in status_dict:
                        print(f"key: {key}")
                        if data[start_index] == 2:
                            end_index = start_index + 2 + 6  # 计算当前key对应数据的结束位置
                            value = data[start_index+2:end_index]  # 截取数据
                            print(f"value: {value}")
                            value_str = ' '.join([f"{b:02X}" for b in value])  # 转换为十六进制字符串
                            print(f"value_str: {value_str}")
                            passkey_addresses[key] = "蓝牙配对参数是 " + value_str
                            start_index = end_index
                        elif data[start_index] == 1:
                            end_index = start_index + 1
                            passkey_addresses[key] = "蓝牙just work 配对方式,配对参数长度为0"
                            start_index = end_index + 1  # 更新起始位置
                    print(f"passkey_addresses: {passkey_addresses}")
                    if debug == True:
                        log_message = (
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",设备配对信息标识位是<span style='color:red;'>{self.connection_status:02X}</span>"
                        )
                        for name, passkey in passkey_addresses.items():
                            log_message += f", <br>{name} <span style='color:red;'> {passkey}</span>"
                        self.log.logger.debug(log_message)
                    self.textBrowserReceive.insertHtml(log_message)
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")

            elif code == 'F20B0001':
                if type == 'C2':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    if Status.is_valid_status(data[0]):
                        print(f"状态码 {data_field} 表示: {Status.get_status_name(data[0])}")
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，{Status.get_status_name(data[0])}")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>{Status.get_status_name(data[0])}</span> ")
                    else:
                        print(f"状态码 {data_field} 未定义")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，状态码 {data_field} 未定义")
                elif type == '83':
                    chunks = [data[i:i + 6] for i in range(0, len(data), 6)]
                    hosts_and_slaves = {
                        "主机1": ':'.join([f"{b:02X}" for b in chunks[0]]),  # 主机1
                        "从机1": ':'.join([f"{b:02X}" for b in chunks[1]]),  # 从机1
                        "从机2": ':'.join([f"{b:02X}" for b in chunks[2]]),  # 从机2
                        "从机3": ':'.join([f"{b:02X}" for b in chunks[3]])  # 从机3
                    }

                    if debug == True:
                        log_message = (
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        )
                        for name, mac in hosts_and_slaves.items():
                            log_message += f", <br>{name} MAC 地址是<span style='color:red;'> {mac}</span>"
                        self.log.logger.debug(log_message)
                    self.textBrowserReceive.insertHtml(log_message)
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == '00000006':
                data_field = ''.join([f"{byte:02X}" for byte in data])
                if type == 'C2':

                    if Status.is_valid_status(data[0]):
                        print(f"状态码 {data_field} 表示: {Status.get_status_name(data[0])}")
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，{Status.get_status_name(data[0])}")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>{Status.get_status_name(data[0])}</span> ")
                    else:
                        print(f"状态码 {data_field} 未定义")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，状态码 {data_field} 未定义")
                elif type == '83':
                    mode = data[0]
                    if mode == 00:
                        mode_str = '未定义'
                    elif mode == 1:
                        mode_str = '缓存模式'
                    elif mode == 2:
                        mode_str = '直接传输模式'
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}，{mode_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>{mode_str}</span> ")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == 'F20B0002':
                if type == 'C2':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    if Status.is_valid_status(data[0]):
                        print(f"状态码 {data_field} 表示: {Status.get_status_name(data[0])}")
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，{Status.get_status_name(data[0])}")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>{Status.get_status_name(data[0])}</span> ")
                    else:
                        print(f"状态码 {data_field} 未定义")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，状态码 {data_field} 未定义")

                elif type == '83':
                    # 解析发射功率档位
                    power_level = data[0]  # 0x00
                    if power_level == 0x00:
                        power_dbm = 4  # 发射功率档位 0 代表 4dBm
                    elif power_level == 0x01:
                        power_dbm = 0
                    elif power_level == 0x02:
                        power_dbm = -4
                    elif power_level == 0x03:
                        power_dbm = -20
                    else:
                        power_dbm = "Unknown"
                        # 解析广播间隔
                    broadcast_interval = data[2] | data[1]  # 0x28 00 -> 40
                    broadcast_interval_ms = broadcast_interval * 0.625  # 单位是毫秒

                    # 解析扫描间隔
                    scan_interval = data[4] | data[3]  # 0xA0 00 -> 160
                    scan_interval_ms = scan_interval * 0.625  # 单位是毫秒
                    if debug == True:
                        self.log.logger.debug(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>发射功率是<span style='color:red;'>{power_dbm}</span> dBm"
                        f",<br>广播间隔是<span style='color:red;'>{broadcast_interval_ms}</span>ms,允许设定范围： 40~ 1000ms"
                        f",<br>扫描间隔是<span style='color:red;'>{scan_interval_ms}</span>ms,允许设定范 围：55~ 110ms")
                    self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>发射功率是<span style='color:red;'>{power_dbm}</span> dBm"
                        f",<br>广播间隔是<span style='color:red;'>{broadcast_interval_ms}</span>ms,允许设定范围： 40~ 1000ms"
                        f",<br>扫描间隔是<span style='color:red;'>{scan_interval_ms}</span>ms,允许设定范 围：55~ 110ms")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
                self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)  # 将坐标移动到文本结尾，
            elif code == 'F20B0003':
                if type == '83' or type == '04':
                    self.rssiData = data
                    # 连接状态标识
                    self.connection_status = data[0]
                    print(f"Connection Status: 0x{self.connection_status:02X} ")
                    status_dict = self.parse_connection_status(self.connection_status)
                    print(f"status_dict: {status_dict}")
                    # 用来存储解析后的结果
                    mac_addresses = {}
                    start_index = 1  # 数据的起始位置
                    for key in status_dict:
                        print(f"key: {key}")
                        end_index = start_index + 6  # 计算当前key对应数据的结束位置
                        value = data[start_index:end_index]  # 截取数据
                        print(f"value: {value}")
                        value_str = ':'.join([f"{b:02X}" for b in value])  # 转换为十六进制字符串
                        print(f"value_str: {value_str}")
                        mac_addresses[key] = value_str
                        start_index = end_index  # 更新起始位置
                    print(f"mac_addresses: {mac_addresses}")

                    if debug == True:
                        log_message = (
                             f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",连接状态标识是<span style='color:red;'>{self.connection_status:02X}</span>"
                        )
                        for name, mac in mac_addresses.items():
                            log_message += f", <br>{name} MAC 地址是<span style='color:red;'> {mac}</span>"
                        self.log.logger.debug(log_message)
                    self.textBrowserReceive.insertHtml(log_message)
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == '0000001C':
                if type == '83':
                    # print('--------------------------')
                    # 每组 8 字节 (6 字节蓝牙地址 + 2 字节 RSSI 值)
                    group_size = 8
                    groups = [data[i:i + group_size] for i in range(0, len(data), group_size)]
                    # print(f"groups: {groups}")
                    result = []
                    for group in groups:
                        # print(f"group--------: {group[:6]}")
                        if len(group) == group_size:
                            bluetooth_address = ':'.join([f"{b:02X}" for b in group[:6]])
                            # print(f"bluetooth_address: {bluetooth_address}")
                            rssi_value_hex = "".join([f"{b:02X}" for b in group[6:]])
                            # print(f"rssi_value_hex: {rssi_value_hex}")
                            # rssi_value_dec = int(rssi_value_hex, 16)  # 转为十进制

                            result.append({"bluetooth_address": bluetooth_address, "rssi_value": rssi_value_hex})

                    if debug == True:
                        log_message = (
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，"
                        )
                        for i, item in enumerate(result, start=1):
                            log_message += f"<br><span style='color:red;'> 蓝牙地址: {item['bluetooth_address']} ，<br>RSSI 值: {item['rssi_value']}</span>"
                        self.log.logger.debug(log_message)
                    self.textBrowserReceive.insertHtml(log_message)
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == '0000000C':
                if type == '83' or type == '04':
                    if data:
                        parsed_data_1 = self.parse_device_data_dynamic(data)
                        print(f"parsed_data_1: {parsed_data_1}")
                        if debug == True:
                            log_message = (
                                f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，"
                            )
                            for key, value in parsed_data_1.items():
                                print(f"{key}: {value}")
                                log_message += f"<br><span style='color:red;'> {key}{value}</span>"
                            self.log.logger.debug(log_message)
                        self.textBrowserReceive.insertHtml(log_message)
                    else:
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml("<br>")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == '00000000':
                if type == '01':
                    mac_Address = self.format_mac(macAddress[::-1])
                    macAddress_str = ''.join([f"{b:02X}" for b in macAddress[::-1]])
                    print(f"mac_Address: {macAddress_str}")
                    print(f"masterMac: {self.mac_info['masterMac']}")
                    print(f"slaveMac: {self.mac_info['slaveMac']}")
                    omd = data[17:21]
                    omd_str = ''.join([f"{b:02X}" for b in omd])
                    print(f"omd_str: {omd_str}")
                    if omd_str == 'F20B0200':
                        data_hex = "FEFEFEFE68710001000000001DA594BCD9F70000000068FEFEFEFE686B00C30501000000000000459E850102F20B02000101010205110102020A2042545F4D455445520000000000000000000000000000000000000000000000000906C100000000010A0631323334353616020914FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000D0BA16B516"
                        command = [int(data_hex[i:i + 2], 16) for i in
                                              range(0, len(data_hex), 2)]
                        if debug == True:
                            self.log.logger.debug(
                                f"检定模式测试，透传指令{code}解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml(
                            f"检定模式测试，透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml("<br>")
                        self.send_command(command)
                    elif omd_str == 'F20B0B00':
                        data_hex = "FEFEFEFE68350001000000001DA594BCD9F70000000068FEFEFEFE682F00C30501000000000000150D850103F20B0B00010914D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D90000E60B160C16"
                        command = [int(data_hex[i:i + 2], 16) for i in
                                   range(0, len(data_hex), 2)]
                        if debug == True:
                            self.log.logger.debug(
                                f"检定模式测试，透传指令{code}解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml(
                            f"检定模式测试，透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml("<br>")
                        self.send_command(command)
                    elif omd_str == 'F20B8000':
                        parsed_result = self.parse_FFFF0005_packet(data)
                        print(parsed_result)
                        # pulse_type = parsed_result['pulse_type']
                        # channel_interval = parsed_result['channel_interval']
                        # transmit_power = parsed_result['transmit_power']
                        # comm_address = parsed_result['comm_address']
                        # frequency_points_1 = parsed_result['frequency_points_1']
                        # frequency_points_2 = parsed_result['frequency_points_2']
                        # frequency_points_3 = parsed_result['frequency_points_3']
                        # frequency_points_4 = parsed_result['frequency_points_4']
                        # frequency_points_5 = parsed_result['frequency_points_5']
                        # 将 pulse_type 转换为整数
                        pulse_type = int(parsed_result['pulse_type'], 16)

                        # 定义一个字典来映射不同的 pulse_type 对应的解释
                        pulse_type_dict = {
                            0: "秒脉冲",
                            1: "需量周期",
                            2: "时段投切",
                            3: "正向谐波脉冲",
                            4: "反向谐波脉冲",
                            5: "无功脉冲",
                            6: "有功脉冲",
                            255: "关闭/退出检定"
                        }

                        # 判断 pulse_type 对应的解释
                        pulse_type_desc = pulse_type_dict.get(pulse_type, "未知脉冲类型")
                        # 输出结果
                        print(f"脉冲类型: {pulse_type_desc}")
                        # 将 channel_interval 转换为整数，单位为 ms
                        channel_interval = int(parsed_result['channel_interval'], 16)  # 16进制转换为整数

                        # transmit_power 的取值范围：0≤tx_power≤4
                        transmit_power = int(parsed_result['transmit_power'], 16)

                        # 判断发射功率并返回相应的值
                        transmit_power_dict = {
                            0: "4 dBm",
                            1: "0 dBm",
                            2: "-4 dBm",
                            3: "-8 dBm",
                            4: "-20 dBm"
                        }

                        # 获取 transmit_power 的对应功率
                        transmit_power_desc = transmit_power_dict.get(transmit_power, "无效的发射功率")
                        comm_address = parsed_result['comm_address']
                        comm_address_str = ' '.join([f"{b:02X}" for b in comm_address])
                        print(f"mac_Address: {comm_address_str}")
                        # 输出结果
                        print(f"信道发射间隔: {channel_interval} ms")
                        print(f"发射功率: {transmit_power_desc}")
                        if debug == True:
                            self.log.logger.debug(
                            f"检定模式测试，透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",<br>脉冲值：{pulse_type}，类型: <span style='color:red;'>{pulse_type_desc}</span>"
                            f",<br>信道发射间隔: <span style='color:red;'>{channel_interval}</span> ms"
                            f",<br>发射功率: <span style='color:red;'>{transmit_power_desc}</span>"
                            f",<br>检定通信地址 A5~A0是<span style='color:red;'>{comm_address_str}</span>")
                        self.textBrowserReceive.insertHtml(
                            f"检定模式测试，透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",<br>脉冲值：{pulse_type}，类型: <span style='color:red;'>{pulse_type_desc}</span>"
                            f",<br>信道发射间隔: <span style='color:red;'>{channel_interval}</span> ms"
                            f",<br>发射功率: <span style='color:red;'>{transmit_power_desc}</span>"
                            f",<br>检定通信地址 A5~A0是<span style='color:red;'>{comm_address_str}</span>")
                        for i in range(1, 6):
                            point_key = f'frequency_points_{i}'
                            frequency_value = self.parse_frequency(parsed_result[point_key])
                            print(f"frequency_value: {frequency_value}")
                            if frequency_value == 0xFFFF:
                                if debug == True:
                                    self.log.logger.debug(
                                    f"<br><span style='color:red;'>频点 {i}: 未配置 (FF FF)</span>")
                                self.textBrowserReceive.insertHtml(
                                    f"<br><span style='color:red;'>频点 {i}: 未配置 (FF FF)</span>")
                            elif 2360 <= frequency_value <= 2510:
                                if debug == True:
                                    self.log.logger.debug(
                                    f"<br>频点 {i}: <span style='color:red;'>{frequency_value}</span> MHz")
                                self.textBrowserReceive.insertHtml(
                                    f"<br>频点 {i}: <span style='color:red;'>{frequency_value}</span> MHz")
                            else:
                                if debug == True:
                                    self.log.logger.debug(
                                    f"<br><span style='color:red;'>频点 {i}: {frequency_value} MHz (无效频点)</span>")
                                self.textBrowserReceive.insertHtml(
                                    f"<br><span style='color:red;'>频点 {i}: {frequency_value} MHz (无效频点)</span>")
                        self.textBrowserReceive.insertHtml("<br>")
                        data_hex = "FEFEFEFE68200001000000001DA594BCD9F70000000068FEFEFEFE681A00C305010000000000001E95870100F20B800000000000E5EA16B316"
                        command = [int(data_hex[i:i + 2], 16) for i in
                                   range(0, len(data_hex), 2)]
                        self.send_command(command)
                        sleep(0.5)
                        self.send_command(self.utils.send_commands_F20B0201(parsed_result))
                    else:
                        if debug == True:
                            self.log.logger.debug(f"透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",<br>报文类型是<span style='color:red;'>{type}</span>"
                            f",<br>A5~A0 源端 MAC 地址是<span style='color:red;'>{mac_Address}</span>")
                        self.textBrowserReceive.insertHtml(
                        f"透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",<br>报文类型是<span style='color:red;'>{type}</span>"
                            f",<br>A5~A0 源端 MAC 地址是<span style='color:red;'>{mac_Address}</span>")
                        self.textBrowserReceive.insertHtml("<br>")
                        self.insert_text_with_separator()
                        slaveMacList = []
                        for i in range(self.slaveMac.count()):
                            slaveMacList.append(self.slaveMac.itemText(i))
                        print(f"slaveMacList-------------------- {slaveMacList}")
                        if macAddress_str not in slaveMacList:
                            self.slaveMac.addItem(macAddress_str)
                        command_bytes = list(self.__RcvBuff)
                        # 检查第八个字节是否是 81
                        if command_bytes[7] == 0x81:
                            print("第八个字节是 81，将其替换为 01")
                            command_bytes[7] = 0x01
                        else:
                            print(f"第八个字节不是 81，是 {hex(command_bytes[7])}")
                        length_bytes = command_bytes[5:7][::-1]
                        length_s = length_bytes[0] * 256 + length_bytes[1]

                        data_field = command_bytes[23:23 + length_s]
                        header = data_field[:4]
                        if header != [0xFE, 0xFE, 0xFE, 0xFE]:
                            header = [0xFE, 0xFE, 0xFE, 0xFE]
                            data_field_n = header + data_field
                            length_s = length_s + 4
                            L = list(struct.pack('<H', length_s))
                            command_bytes[5:7] = L
                            command_bytes[23:23 + length_s] = data_field_n
                            print(f"length_s，是 {length_s}")
                            print(f"command_bytes[5:7]，是 {self.format_mac(command_bytes[5:7])}")
                            calculated_checksum = sum(command_bytes[4:23 + length_s]) % 256
                            print(f"calculated_checksum，是 {calculated_checksum}")
                            command_bytes.append(calculated_checksum)
                            command_bytes += [0x16]
                            print(f"command_bytes: {self.format_mac(command_bytes)}")
                            self.send_command(command_bytes)
                        else:
                            calculated_checksum = sum(command_bytes[4:23 + length_s]) % 256
                            print(f"calculated_checksum，是 {calculated_checksum}")
                            command_bytes[23 + length_s] = calculated_checksum
                            print(f"command_bytes: {self.format_mac(command_bytes)}")
                            self.send_command(command_bytes)
                        # if macAddress_str not in self.utils.mac_commands:
                        #     if debug == True:
                        #         self.log.logger.debug(f"指令<b>{code}</b>透传测试结束")
                        #     self.textBrowserReceive.insertHtml(
                        #         f"指令<b>{code}</b>透传测试结束")
                        #     self.textBrowserReceive.insertHtml("<br>")
                        # else:



                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml("<br>")
            elif code == 'FFFF0005':
                if type == '82':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    print(f"data_field: {data_field}")
                    if data_field == '00':
                        if debug == True:
                            self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，检定模式,电能表管理 MCU,下发给蓝牙模块,配置成功!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，检定模式,电能表管理 MCU,下发给蓝牙模块,配置成功!!!")
                    elif data_field == 'FF':
                        if debug == True:
                            self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，检定模式,电能表管理 MCU,下发给蓝牙模块,配置失败!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>检定模式,电能表管理 MCU,下发给蓝牙模块,配置失败!!!</span>")
                    else:
                        if debug == True:
                            self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，检定模式,电能表管理 MCU,下发给蓝牙模块,配置失败!!!")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>检定模式,电能表管理 MCU,下发给蓝牙模块,配置失败!!!</span>")
                    self.textBrowserReceive.insertHtml("<br>")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml("<br>")
            elif code == '0000002E':
                if type == '83':
                    if len(data) == 8:
                        local_platform_major = data[0] + (data[1] << 8)
                        local_platform_minor = data[2]
                        local_platform_patch = data[3]
                        self.localPlatformVersion = f"{local_platform_major}.{local_platform_minor}.{local_platform_patch}"
                        local_app_major = data[4] + (data[5] << 8)
                        local_app_minor = data[6]
                        local_app_patch = data[7]
                        self.localAppVersion = f"{local_app_major}.{local_app_minor}.{local_app_patch}"
                        if debug == True:
                            self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<br><span style='color:red;'>Local: app:{self.localAppVersion} | platform:{self.localPlatformVersion}  </span>")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<br><span style='color:red;'>Local: app:{self.localAppVersion} | platform:{self.localPlatformVersion}  </span>")
                        self.textBrowserReceive.insertHtml("<br>")
                        self.label_Local.setText(f"Local: app:{self.localAppVersion} | platform:{self.localPlatformVersion}")
                        self.label_Local.show()
                        self.plan = self.build_update_plan()
                    else:
                        if len(data) == 1:
                            self.CheckDevStatus = data[0]
                        print(f"self.CheckDevStatus: {self.CheckDevStatus}")
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml("<br>")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml("<br>")
            else:
                if type == 'C2':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    if Status.is_valid_status(data[0]):
                        print(f"状态码 {data_field} 表示: {Status.get_status_name(data[0])}")
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，{Status.get_status_name(data[0])}")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>{Status.get_status_name(data[0])}</span> ")
                    else:
                        print(f"状态码 {data_field} 未定义")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，状态码 {data_field} 未定义")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            self.insert_text_with_separator()
            self.success_count += 1
            if self.timeout_timer:
                self.timeout_timer.cancel()
            print(f"self.success_count: {self.success_count}")
            print(f"self.__except_commands: {self.__except_commands}")
            self.process_command_queue()  # 解析成功后继续发送下一条指令"


        else:
            self.insert_text_with_separator()
            if debug == True:
                self.log.logger.debug("Failed to parse response.")
            # logging.debug("Failed to parse response.")
    def parsed_ws_result(self,parsed_result):
        if parsed_result:
            self.response_received = True
            # logging.debug("Response parsed successfully.")
            code = parsed_result['code']
            # logging.debug("Parsed code:{}".format(code))
            length = parsed_result['length']
            type = parsed_result['type']
            data = parsed_result['data']
            macAddress = parsed_result['address']
            data_field_str = ' '.join([f"{byte:02X}" for byte in data])
            if debug == True:
                self.log.logger.debug("开始进行数据解析......\r\n")
            # logging.debug("Parsed D0~Dn_str:{}".format(data_field_str))
            self.textBrowserReceive.insertPlainText("开始进行数据解析......\r\n")
            self.textBrowserReceive.insertPlainText("\r\n")
            self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)  # 将坐标移动到文本结尾，
            if code == '00000007' and length == '1B':
                last_six_data = data[-6:]  # 获取最后六个字节

                # 反向读取地址
                address = last_six_data[::-1]  # 反转地址字节序列

                # 打印结果
                # logging.debug("Last six bytes of data: {}".format(last_six_data))
                # logging.debug("Reversed address: {}".format(address))

                # 如果想以十六进制格式打印：
                last_six_data_hex = ''.join([f"{byte:02X}" for byte in last_six_data])
                address_hex = ''.join([f"{byte:02X}" for byte in address])

                # logging.debug(f"Last six bytes (hex): {last_six_data_hex}")
                # logging.debug(f"Reversed address (hex): {address_hex}")

                # 输出
                # print(f"Last six bytes (hex): {last_six_data_hex}")
                # print(f"Reversed address (hex): {address_hex}")
                if debug == True:
                    self.log.logger.debug("Last six bytes of data: {}".format(last_six_data))
                    self.log.logger.debug("Reversed address: {}".format(address))
                    self.log.logger.debug(f"Last six bytes (hex): {last_six_data_hex}")
                    self.log.logger.debug(f"Reversed address (hex): {address_hex}")
                    self.log.logger.debug(f"指令{code}解析成功，<br>数据域是{data_field_str}")

                self.textBrowserReceive.insertHtml(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
                self.send_command(self.utils.send_commands_00000007())
            elif code == '00000008':
                # 初始化 platform 数组
                version = [0, 0, 0]
                v = data[::-1]
                # logging.debug("version_data: {}".format(v))
                # 解析字节并进行位移操作
                version[0] = v[0]   # 第一个元素
                version[1] = v[1]  # 第二个元素，v[2]
                version[2] = v[3] + (v[2] << 8)   # 第三个元素，v[3]
                # print(f"version: {version}")
                version_DEC = '.'.join([f"{byte}" for byte in version])
                # print(f"version: {version_DEC}")
                if debug == True:
                    self.log.logger.debug(f"指令{code}解析成功，<br>数据域是{data_field_str},版本号是{version_DEC}")
                self.textBrowserReceive.insertHtml(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str},<br>版本号是<span style='color:red;'>{version_DEC}</span>")
                self.textBrowserReceive.insertHtml("<br>")

            elif code == 'F20B000A':
                if debug == True:
                    self.log.logger.debug(f"指令{code}解析成功，<br>数据域是{data_field_str},序列号是{data_field_str}")
                self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<br>序列号是<span style='color:red;'>{data_field_str}</span>")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == 'F20B0000':

                if type == '82':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    # print(f"Master MAC: {data_field}")
                    if data_field == '00':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str},配置成功!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，配置成功!!!")
                    elif data_field == '05':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str},检验失败，需要检查参数累加和校验字节!!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>检验失败，需要检查参数累加和校验字节!!!</span>")
                    elif data_field == 'FF':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str},配置的模块 MAC 地址参数为非法值!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>配置的模块 MAC 地址参数为非法值!!!</span>")
                    else:
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str},配置的模块 MAC 地址参数为非法值!!!")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>配置的模块 MAC 地址参数为非法值!!!</span>")
                elif type == '83':
                    # 本机 MAC 地址
                    master_mac = data[0:6]
                    print(f"Master MAC: {self.format_mac(master_mac)}")

                    # 从机 1 MAC 地址
                    slave_1_mac = data[6:12]
                    print(f"Slave 1 MAC: {self.format_mac(slave_1_mac)}")

                    # 从机 2 MAC 地址
                    slave_2_mac = data[12:18]
                    print(f"Slave 2 MAC: {self.format_mac(slave_2_mac)}")

                    # 从机 3 MAC 地址
                    slave_3_mac = data[18:24]
                    print(f"Slave 3 MAC: {self.format_mac(slave_3_mac)}")

                    # 厂商 ID
                    manufacturer_id = data[24:26]
                    print(f"Manufacturer ID: {''.join([f'{b:02X}' for b in manufacturer_id])}")

                    # 设备类型
                    device_type = data[26]
                    print(f"Device Type: 0x{device_type:02X}")

                    # 特征校验码
                    feature_code = data[27:29]
                    print(f"Feature Code: {''.join([f'{b:02X}' for b in feature_code])}")

                    # 主通道配对 PIN 码密文
                    master_pin = data[29:45]
                    print(f"Master Channel PIN: {''.join([f'{b:02X}' for b in master_pin])}")

                    # 主通道配对码
                    master_pairing_code = data[45:51]
                    print(f"Master Channel Pairing Code: {''.join([f'{b:02X}' for b in master_pairing_code])}")

                    # 从通道配对码
                    slave_pairing_code = data[51:69]
                    print(f"Slave Channel Pairing Code: {''.join([f'{b:02X}' for b in slave_pairing_code])}")

                    # 校验和
                    checksum = data[-1]
                    print(f"Checksum: 0x{checksum:02X}")
                    # 计算校验和
                    calculated_checksum = sum(data[:-3]) % 256
                    print(f"calculated_checksum: 0x{calculated_checksum:02X}")
                    if debug == True:
                        self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>本机 MAC 地址是<span style='color:red;'>{self.format_mac(master_mac)}</span>"
                        f",<br>从机1MAC 地址是<span style='color:red;'>{self.format_mac(slave_1_mac)}</span>"
                        f",<br>从机2MAC 地址是<span style='color:red;'>{self.format_mac(slave_2_mac)}</span>"
                        f",<br>从机3MAC 地址是<span style='color:red;'>{self.format_mac(slave_3_mac)}</span>"
                        f",<br>厂商 ID是<span style='color:red;'>{''.join([f'{b:02X}' for b in manufacturer_id])}</span>"
                        f",<br>设备类型是<span style='color:red;'>{device_type:02X}</span>"
                        f",<br>特征校验码是<span style='color:red;'>{''.join([f'{b:02X}' for b in feature_code])}</span>"
                        f",<br>主通道配对 PIN 码加密后的密文(明文 模式)是<span style='color:red;'>{''.join([f'{b:02X}' for b in master_pin])}</span>"
                        f",<br>主通道配对码是<span style='color:red;'>{''.join([f'{b:02X}' for b in master_pairing_code])}</span>"
                        f",<br>从通道配对码是<span style='color:red;'>{''.join([f'{b:02X}' for b in slave_pairing_code])}</span>")
                    # 校验校验和
                    # if checksum != calculated_checksum:
                    self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>本机 MAC 地址是<span style='color:red;'>{self.format_mac(master_mac)}</span>"
                        f",<br>从机1MAC 地址是<span style='color:red;'>{self.format_mac(slave_1_mac)}</span>"
                        f",<br>从机2MAC 地址是<span style='color:red;'>{self.format_mac(slave_2_mac)}</span>"
                        f",<br>从机3MAC 地址是<span style='color:red;'>{self.format_mac(slave_3_mac)}</span>"
                        f",<br>厂商 ID是<span style='color:red;'>{''.join([f'{b:02X}' for b in manufacturer_id])}</span>"
                        f",<br>设备类型是<span style='color:red;'>{device_type:02X}</span>"
                        f",<br>特征校验码是<span style='color:red;'>{''.join([f'{b:02X}' for b in feature_code])}</span>"
                        f",<br>主通道配对 PIN 码加密后的密文(明文 模式)是<span style='color:red;'>{''.join([f'{b:02X}' for b in master_pin])}</span>"
                        f",<br>主通道配对码是<span style='color:red;'>{''.join([f'{b:02X}' for b in master_pairing_code])}</span>"
                        f",<br>从通道配对码是<span style='color:red;'>{''.join([f'{b:02X}' for b in slave_pairing_code])}</span>")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == 'F20B0002':
                if type == '82':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    # print(f"Master MAC: {data_field}")
                    if data_field == '00':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，设置参数成功!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，设置参数成功!!!")
                    elif data_field == 'FF':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，设置失败（参数不符合允许设定范围）!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>设置失败（参数不符合允许设定范围）!!!</span>")
                    else:
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，设置失败（参数不符合允许设定范围）!!!")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>设置失败（参数不符合允许设定范围）!!!</span>")
                elif type == '83':
                    # 解析发射功率档位
                    power_level = data[0]  # 0x00
                    if power_level == 0x00:
                        power_dbm = 4  # 发射功率档位 0 代表 4dBm
                    elif power_level == 0x01:
                        power_dbm = 0
                    elif power_level == 0x02:
                        power_dbm = -4
                    elif power_level == 0x03:
                        power_dbm = -20
                    else:
                        power_dbm = "Unknown"
                        # 解析广播间隔
                    broadcast_interval = data[2] << 8 | data[1]  # 0x28 00 -> 40
                    broadcast_interval_ms = broadcast_interval * 1.0  # 单位是毫秒

                    # 解析扫描间隔
                    scan_interval = data[4] << 8 | data[3]  # 0xA0 00 -> 160
                    scan_interval_ms = scan_interval * 1.0  # 单位是毫秒
                    if debug == True:
                        self.log.logger.debug(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>发射功率是<span style='color:red;'>{power_dbm}</span> dBm"
                        f",<br>广播间隔是<span style='color:red;'>{broadcast_interval_ms}</span>ms,允许设定范围： 40~ 1000ms"
                        f",<br>扫描间隔是<span style='color:red;'>{scan_interval_ms}</span>ms,允许设定范 围：55~ 110ms")
                    self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>发射功率是<span style='color:red;'>{power_dbm}</span> dBm"
                        f",<br>广播间隔是<span style='color:red;'>{broadcast_interval_ms}</span>ms,允许设定范围： 40~ 1000ms"
                        f",<br>扫描间隔是<span style='color:red;'>{scan_interval_ms}</span>ms,允许设定范 围：55~ 110ms")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
                self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)  # 将坐标移动到文本结尾，
            elif code == 'F20B0003':
                if type == '84':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    print(f"Master MAC: {data_field}")
                    if data_field == '00':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，通知上报接收成功!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，通知上报接收成功!!!")
                    elif data_field == 'FF':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，通知上报接收失败!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>通知上报接收失败!!!</span>")
                    else:
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，通知上报接收失败!!!")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>通知上报接收失败!!!</span>")
                elif type == '04' or type == '83':
                    self.connection_status = data[0]
                    print(f"Connection Status: 0x{self.connection_status:02X} ({bin(self.connection_status)})")
                    status_dict = self.parse_connection_status(self.connection_status)
                    print(f"status_dict: {status_dict}")
                    group_size = 6
                    groups = [data[i:i + group_size] for i in range(1, len(data), group_size)]
                    hosts_and_slaves = {
                        "主机1": ':'.join([f"{b:02X}" for b in groups[0]]),  # 主机1
                        "主机2": ':'.join([f"{b:02X}" for b in groups[1]]),  # 主机2
                        "从机1": ':'.join([f"{b:02X}" for b in groups[2]]),  # 从机1
                        "从机2": ':'.join([f"{b:02X}" for b in groups[3]]),  # 从机2
                        "从机3": ':'.join([f"{b:02X}" for b in groups[4]])  # 从机3
                    }


                    if debug == True:
                        log_message = (
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",<br>连接状态标识是<span style='color:red;'>{self.connection_status:02X}</span>"
                        )
                        for name, mac in hosts_and_slaves.items():
                            log_message += f", <br>{name} MAC 地址是<span style='color:red;'> {mac}</span>"
                        self.log.logger.debug(log_message)
                    self.textBrowserReceive.insertHtml(log_message)
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == 'F20B0008':
                if type == '82':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    print(f"Master MAC: {data_field}")
                    if data_field == '00':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，参数配置成功!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，参数配置成功!!!")
                    elif data_field == 'FF':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，参数非法（参数长度超长）!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>参数非法（参数长度超长）!!!</span>")
                    else:
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，参数非法（请检查）!!!")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>参数非法（请检查）!!!</span>")
                elif type == '83':
                    # 主机 1 MAC 地址
                    local_mac = data[0:6]
                    master_1_mac_str = ':'.join([f"{b:02X}" for b in local_mac])
                    print(f"Master 1 MAC: {master_1_mac_str}")

                    # 主通道 1 配对 PIN 码长度（第 7 字节）
                    channel_1_pin_length = data[6]
                    print(f"channel_1_pin_length: {channel_1_pin_length}")
                    # 主通道 1 配对 PIN 码（第 8-13 字节）
                    channel_1_pin = data[7:13]
                    channel_1_pin_str = ''.join([f"{b:02X}" for b in channel_1_pin])
                    print(f"channel_1_pin_str: {channel_1_pin_str}")
                    # 主通道 1 配对 PIN 码加密密文长度（第 14 字节）
                    channel_1_encrypted_pin_length = data[13]
                    print(f"channel_1_encrypted_pin_length: {channel_1_encrypted_pin_length}")
                    # 主通道 1 配对 PIN 码密文广播数据（第 15-30 字节）
                    channel_1_encrypted_pin = data[14:30]
                    channel_1_encrypted_pin_str = ''.join([f"{b:02X}" for b in channel_1_encrypted_pin])
                    print(f"channel_1_encrypted_pin_str: {channel_1_encrypted_pin_str}")
                    # 主通道 2 配对 PIN 码长度（第 31 字节）
                    channel_2_pin_length = data[30]
                    print(f"channel_2_pin_length: {channel_2_pin_length}")
                    # 主通道 2 配对 PIN 码（第 32-37 字节）
                    channel_2_pin = data[31:37]
                    channel_2_pin_str = ''.join([f"{b:02X}" for b in channel_2_pin])
                    print(f"channel_2_pin_str: {channel_2_pin_str}")
                    # 主通道 2 配对 PIN 码加密密文长度（第 38 字节）
                    channel_2_encrypted_pin_length = data[37]
                    print(f"channel_2_encrypted_pin_length: {channel_2_encrypted_pin_length}")
                    # 主通道 2 配对 PIN 码密文广播数据（第 39-54 字节）
                    channel_2_encrypted_pin = data[38:54]
                    channel_2_encrypted_pin_str = ''.join([f"{b:02X}" for b in channel_2_encrypted_pin])
                    print(f"channel_2_encrypted_pin_str: {channel_2_encrypted_pin_str}")
                    if debug == True:
                        self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>模块本地 MAC 地址是<span style='color:red;'>{master_1_mac_str}</span>"
                        f",<br>主通道 1 配对 PIN 码长度是<span style='color:red;'>{channel_1_pin_length}</span>"
                        f",<br>主通道 1 配对 PIN 码是<span style='color:red;'>{channel_1_pin_str}</span>"
                        f",<br>主通道 1 配对 PIN 码加密密文长度是<span style='color:red;'>{channel_1_encrypted_pin_length}</span>"
                        f",<br>主通道 1 配对 PIN 码密文广播数据是<span style='color:red;'>{channel_1_encrypted_pin_str}</span>"
                        f",<br>主通道 2 配对 PIN 码长度是<span style='color:red;'>{channel_2_pin_length}</span>"
                        f",<br>主通道 2 配对 PIN 码是<span style='color:red;'>{channel_2_pin_str}</span>"
                        f",<br>主通道 2 配对 PIN 码加密密文长度是<span style='color:red;'>{channel_2_encrypted_pin_length}</span>"
                        f",<br>主通道 2 配对 PIN 码密文广播数据是<span style='color:red;'>{channel_2_encrypted_pin_str}</span>")
                    self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>模块本地 MAC 地址是<span style='color:red;'>{master_1_mac_str}</span>"
                        f",<br>主通道 1 配对 PIN 码长度是<span style='color:red;'>{channel_1_pin_length}</span>"
                        f",<br>主通道 1 配对 PIN 码是<span style='color:red;'>{channel_1_pin_str}</span>"
                        f",<br>主通道 1 配对 PIN 码加密密文长度是<span style='color:red;'>{channel_1_encrypted_pin_length}</span>"
                        f",<br>主通道 1 配对 PIN 码密文广播数据是<span style='color:red;'>{channel_1_encrypted_pin_str}</span>"
                        f",<br>主通道 2 配对 PIN 码长度是<span style='color:red;'>{channel_2_pin_length}</span>"
                        f",<br>主通道 2 配对 PIN 码是<span style='color:red;'>{channel_2_pin_str}</span>"
                        f",<br>主通道 2 配对 PIN 码加密密文长度是<span style='color:red;'>{channel_2_encrypted_pin_length}</span>"
                        f",<br>主通道 2 配对 PIN 码密文广播数据是<span style='color:red;'>{channel_2_encrypted_pin_str}</span>")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == 'F20B0009':
                if type == '82':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    print(f"data_field: {data_field}")
                    if data_field == '00':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，参数配置成功!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，参数配置成功!!!")
                    elif data_field == 'FF':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，参数配置非法（参数超过最大长度）!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>参数配置非法（参数超过最大长度）!!!</span>")
                    else:
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，参数配置非法（请检查）!!!")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>参数配置非法（请检查）!!!</span>")
                elif type == '83':
                    # 从机 1 MAC 地址
                    slave_1_mac = data[0:6]
                    slave_1_mac_str = ':'.join([f"{b:02X}" for b in slave_1_mac])
                    print(f"Slave 1 MAC: {slave_1_mac_str}")

                    # 从机 1 配对 PIN 码长度，6 字节
                    channel_1_pin_length = data[6]
                    print(f"channel_1_pin_length: {channel_1_pin_length}")
                    # 从机 1 配对 PIN 码
                    channel_1_pin = data[7:13]
                    channel_1_pin_str = ''.join([f"{b:02X}" for b in channel_1_pin])
                    print(f"channel_1_pin_str: {channel_1_pin_str}")
                    # 从机 2 MAC 地址
                    slave_2_mac = data[13:19]
                    slave_2_mac_str = ':'.join([f"{b:02X}" for b in slave_2_mac])
                    print(f"Slave 2 MAC: {slave_2_mac_str}")
                    # 从机 2 配对 PIN 码长度，6 字节
                    channel_2_pin_length = data[20]
                    print(f"channel_2_pin_length: {channel_2_pin_length}")
                    # 从机 2 配对 PIN 码
                    channel_2_pin = data[21:27]
                    channel_2_pin_str = ''.join([f"{b:02X}" for b in channel_2_pin])
                    print(f"channel_2_pin_str: {channel_2_pin_str}")
                    # 从机 3 MAC 地址
                    slave_3_mac = data[28:34]
                    slave_3_mac_str = ':'.join([f"{b:02X}" for b in slave_3_mac])
                    print(f"Slave 3 MAC: {slave_3_mac_str}")
                    # 从机 3 配对 PIN 码长度，6 字节
                    slave_3_pin_length = data[35]
                    print(f"slave_3_pin_length: {slave_3_pin_length}")
                    # 从机 3 配对 PIN 码
                    slave_3_pin = data[36:42]
                    slave_3_pin_str = ''.join([f"{b:02X}" for b in slave_3_pin])
                    print(f"slave_3_pin_str: {slave_3_pin_str}")
                    if debug == True:
                        self.log.logger.debug(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>从机 1 MAC 地址是<span style='color:red;'>{slave_1_mac_str}</span>"
                        f",<br>从机 1 配对 PIN 码长度是<span style='color:red;'>{channel_1_pin_length}</span>"
                        f",<br>从机 1 配对 PIN 码是<span style='color:red;'>{channel_1_pin_str}</span>"
                        f",<br>从机 2 MAC 地址是<span style='color:red;'>{slave_2_mac_str}</span>"
                        f",<br>从机 2 配对 PIN 码长度是<span style='color:red;'>{channel_2_pin_length}</span>"
                        f",<br>从机 2 配对 PIN 码是<span style='color:red;'>{channel_2_pin_str}</span>"
                        f",<br>从机 3 MAC 地址是<span style='color:red;'>{slave_3_mac_str}</span>"
                        f",<br>从机 3 配对 PIN 码长度是<span style='color:red;'>{slave_3_pin_length}</span>"
                        f",<br>从机 3 配对 PIN 码是<span style='color:red;'>{slave_3_pin_str}</span>")

                    self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>从机 1 MAC 地址是<span style='color:red;'>{slave_1_mac_str}</span>"
                        f",<br>从机 1 配对 PIN 码长度是<span style='color:red;'>{channel_1_pin_length}</span>"
                        f",<br>从机 1 配对 PIN 码是<span style='color:red;'>{channel_1_pin_str}</span>"
                        f",<br>从机 2 MAC 地址是<span style='color:red;'>{slave_2_mac_str}</span>"
                        f",<br>从机 2 配对 PIN 码长度是<span style='color:red;'>{channel_2_pin_length}</span>"
                        f",<br>从机 2 配对 PIN 码是<span style='color:red;'>{channel_2_pin_str}</span>"
                        f",<br>从机 3 MAC 地址是<span style='color:red;'>{slave_3_mac_str}</span>"
                        f",<br>从机 3 配对 PIN 码长度是<span style='color:red;'>{slave_3_pin_length}</span>"
                        f",<br>从机 3 配对 PIN 码是<span style='color:red;'>{slave_3_pin_str}</span>")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == '00000000':

                if type == '81':
                    mac_Address = self.format_mac(macAddress[::-1])
                    macAddress_str = ''.join([f"{b:02X}" for b in macAddress[::-1]])
                    print(f"mac_Address: {macAddress_str}")
                    print(f"masterMac: {self.mac_info['masterMac']}")
                    print(f"slaveMac: {self.mac_info['slaveMac']}")
                    omd = data[17:21]
                    omd_str = ''.join([f"{b:02X}" for b in omd])
                    print(f"omd_str: {omd_str}")
                    if omd_str == 'F20B0200':
                        data_hex = "FEFEFEFE68710001000000001DA594BCD9F70000000068FEFEFEFE686B00C30501000000000000459E850102F20B02000101010205110102020A2042545F4D455445520000000000000000000000000000000000000000000000000906C100000000010A0631323334353616020914FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000D0BA16B516"
                        command = [int(data_hex[i:i + 2], 16) for i in
                                              range(0, len(data_hex), 2)]
                        if debug == True:
                            self.log.logger.debug(
                                f"检定模式测试，透传指令{code}解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml(
                            f"检定模式测试，透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml("<br>")
                        self.send_command(command)
                    elif omd_str == 'F20B0B00':
                        data_hex = "FEFEFEFE68350001000000001DA594BCD9F70000000068FEFEFEFE682F00C30501000000000000150D850103F20B0B00010914D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D90000E60B160C16"
                        command = [int(data_hex[i:i + 2], 16) for i in
                                   range(0, len(data_hex), 2)]
                        if debug == True:
                            self.log.logger.debug(
                                f"检定模式测试，透传指令{code}解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml(
                            f"检定模式测试，透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml("<br>")
                        self.send_command(command)
                    elif omd_str == 'F20B8000':
                        parsed_result = self.parse_FFFF0005_packet(data)
                        print(parsed_result)
                        # pulse_type = parsed_result['pulse_type']
                        # channel_interval = parsed_result['channel_interval']
                        # transmit_power = parsed_result['transmit_power']
                        # comm_address = parsed_result['comm_address']
                        # frequency_points_1 = parsed_result['frequency_points_1']
                        # frequency_points_2 = parsed_result['frequency_points_2']
                        # frequency_points_3 = parsed_result['frequency_points_3']
                        # frequency_points_4 = parsed_result['frequency_points_4']
                        # frequency_points_5 = parsed_result['frequency_points_5']
                        # 将 pulse_type 转换为整数
                        pulse_type = int(parsed_result['pulse_type'], 16)

                        # 定义一个字典来映射不同的 pulse_type 对应的解释
                        pulse_type_dict = {
                            0: "秒脉冲",
                            1: "需量周期",
                            2: "时段投切",
                            3: "正向谐波脉冲",
                            4: "反向谐波脉冲",
                            5: "无功脉冲",
                            6: "有功脉冲",
                            255: "关闭/退出检定"
                        }

                        # 判断 pulse_type 对应的解释
                        pulse_type_desc = pulse_type_dict.get(pulse_type, "未知脉冲类型")
                        # 输出结果
                        print(f"脉冲类型: {pulse_type_desc}")
                        # 将 channel_interval 转换为整数，单位为 ms
                        channel_interval = int(parsed_result['channel_interval'], 16)  # 16进制转换为整数

                        # transmit_power 的取值范围：0≤tx_power≤4
                        transmit_power = int(parsed_result['transmit_power'], 16)

                        # 判断发射功率并返回相应的值
                        transmit_power_dict = {
                            0: "4 dBm",
                            1: "0 dBm",
                            2: "-4 dBm",
                            3: "-8 dBm",
                            4: "-20 dBm"
                        }

                        # 获取 transmit_power 的对应功率
                        transmit_power_desc = transmit_power_dict.get(transmit_power, "无效的发射功率")
                        comm_address = parsed_result['comm_address']
                        comm_address_str = ' '.join([f"{b:02X}" for b in comm_address])
                        print(f"mac_Address: {comm_address_str}")
                        # 输出结果
                        print(f"信道发射间隔: {channel_interval} ms")
                        print(f"发射功率: {transmit_power_desc}")
                        if debug == True:
                            self.log.logger.debug(
                            f"检定模式测试，透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",<br>脉冲值：{pulse_type}，类型: <span style='color:red;'>{pulse_type_desc}</span>"
                            f",<br>信道发射间隔: <span style='color:red;'>{channel_interval}</span> ms"
                            f",<br>发射功率: <span style='color:red;'>{transmit_power_desc}</span>"
                            f",<br>检定通信地址 A5~A0是<span style='color:red;'>{comm_address_str}</span>")
                        self.textBrowserReceive.insertHtml(
                            f"检定模式测试，透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",<br>脉冲值：{pulse_type}，类型: <span style='color:red;'>{pulse_type_desc}</span>"
                            f",<br>信道发射间隔: <span style='color:red;'>{channel_interval}</span> ms"
                            f",<br>发射功率: <span style='color:red;'>{transmit_power_desc}</span>"
                            f",<br>检定通信地址 A5~A0是<span style='color:red;'>{comm_address_str}</span>")
                        for i in range(1, 6):
                            point_key = f'frequency_points_{i}'
                            frequency_value = self.parse_frequency(parsed_result[point_key])
                            print(f"frequency_value: {frequency_value}")
                            if frequency_value == 0xFFFF:
                                if debug == True:
                                    self.log.logger.debug(
                                    f"<br><span style='color:red;'>频点 {i}: 未配置 (FF FF)</span>")
                                self.textBrowserReceive.insertHtml(
                                    f"<br><span style='color:red;'>频点 {i}: 未配置 (FF FF)</span>")
                            elif 2360 <= frequency_value <= 2510:
                                if debug == True:
                                    self.log.logger.debug(
                                    f"<br>频点 {i}: <span style='color:red;'>{frequency_value}</span> MHz")
                                self.textBrowserReceive.insertHtml(
                                    f"<br>频点 {i}: <span style='color:red;'>{frequency_value}</span> MHz")
                            else:
                                if debug == True:
                                    self.log.logger.debug(
                                    f"<br><span style='color:red;'>频点 {i}: {frequency_value} MHz (无效频点)</span>")
                                self.textBrowserReceive.insertHtml(
                                    f"<br><span style='color:red;'>频点 {i}: {frequency_value} MHz (无效频点)</span>")
                        self.textBrowserReceive.insertHtml("<br>")
                        data_hex = "FEFEFEFE68200001000000001DA594BCD9F70000000068FEFEFEFE681A00C305010000000000001E95870100F20B800000000000E5EA16B316"
                        command = [int(data_hex[i:i + 2], 16) for i in
                                   range(0, len(data_hex), 2)]
                        self.send_command(command)
                        sleep(0.5)
                        self.send_command(self.utils.send_commands_FFFF0005(parsed_result))
                    else:
                        if debug == True:
                            self.log.logger.debug(f"透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",<br>报文类型是<span style='color:red;'>{type}</span>"
                            f",<br>A5~A0 源端 MAC 地址是<span style='color:red;'>{mac_Address}</span>")
                        self.textBrowserReceive.insertHtml(
                        f"透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",<br>报文类型是<span style='color:red;'>{type}</span>"
                            f",<br>A5~A0 源端 MAC 地址是<span style='color:red;'>{mac_Address}</span>")
                        self.textBrowserReceive.insertHtml("<br>")
                        self.insert_text_with_separator()
                        slaveMacList = []
                        for i in range(self.slaveMac.count()):
                            slaveMacList.append(self.slaveMac.itemText(i))
                        print(f"slaveMacList-------------------- {slaveMacList}")
                        if macAddress_str not in slaveMacList:
                            self.slaveMac.addItem(macAddress_str)
                        command_bytes = list(self.__RcvBuff)
                        # 检查第八个字节是否是 81
                        if command_bytes[7] == 0x81:
                            print("第八个字节是 81，将其替换为 01")
                            command_bytes[7] = 0x01
                        else:
                            print(f"第八个字节不是 81，是 {hex(command_bytes[7])}")
                        length_bytes = command_bytes[5:7][::-1]
                        length_s = length_bytes[0] * 256 + length_bytes[1]

                        data_field = command_bytes[23:23 + length_s]
                        header = data_field[:4]
                        if header != [0xFE, 0xFE, 0xFE, 0xFE]:
                            header = [0xFE, 0xFE, 0xFE, 0xFE]
                            data_field_n = header + data_field
                            length_s = length_s + 4
                            L = list(struct.pack('<H', length_s))
                            command_bytes[5:7] = L
                            command_bytes[23:23 + length_s] = data_field_n
                            print(f"length_s，是 {length_s}")
                            print(f"command_bytes[5:7]，是 {self.format_mac(command_bytes[5:7])}")
                            calculated_checksum = sum(command_bytes[4:23 + length_s]) % 256
                            print(f"calculated_checksum，是 {calculated_checksum}")
                            command_bytes.append(calculated_checksum)
                            command_bytes += [0x16]
                            print(f"command_bytes: {self.format_mac(command_bytes)}")
                            self.send_command(command_bytes)
                        else:
                            calculated_checksum = sum(command_bytes[4:23 + length_s]) % 256
                            print(f"calculated_checksum，是 {calculated_checksum}")
                            command_bytes[23 + length_s] = calculated_checksum
                            print(f"command_bytes: {self.format_mac(command_bytes)}")
                            self.send_command(command_bytes)


                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml("<br>")
            elif code == 'FFFF0005':
                if type == '82':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    print(f"data_field: {data_field}")
                    if data_field == '00':
                        if debug == True:
                            self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，检定模式,电能表管理 MCU,下发给蓝牙模块,配置成功!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，检定模式,电能表管理 MCU,下发给蓝牙模块,配置成功!!!")
                    elif data_field == 'FF':
                        if debug == True:
                            self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，检定模式,电能表管理 MCU,下发给蓝牙模块,配置失败!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>检定模式,电能表管理 MCU,下发给蓝牙模块,配置失败!!!</span>")
                    else:
                        if debug == True:
                            self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，检定模式,电能表管理 MCU,下发给蓝牙模块,配置失败!!!")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>检定模式,电能表管理 MCU,下发给蓝牙模块,配置失败!!!</span>")
                    self.textBrowserReceive.insertHtml("<br>")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml("<br>")
            elif code == '0000002E':
                if type == '83':
                    if len(data) == 8:
                        local_platform_major = data[0] + (data[1] << 8)
                        local_platform_minor = data[2]
                        local_platform_patch = data[3]
                        self.localPlatformVersion = f"{local_platform_major}.{local_platform_minor}.{local_platform_patch}"
                        local_app_major = data[4] + (data[5] << 8)
                        local_app_minor = data[6]
                        local_app_patch = data[7]
                        self.localAppVersion = f"{local_app_major}.{local_app_minor}.{local_app_patch}"
                        if debug == True:
                            self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<br><span style='color:red;'>Local: app:{self.localAppVersion} | platform:{self.localPlatformVersion}  </span>")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<br><span style='color:red;'>Local: app:{self.localAppVersion} | platform:{self.localPlatformVersion}  </span>")
                        self.textBrowserReceive.insertHtml("<br>")
                        self.label_Local.setText(f"Local: app:{self.localAppVersion} | platform:{self.localPlatformVersion}")
                        self.label_Local.show()
                        self.plan = self.build_update_plan()
                    else:
                        if len(data) == 1:
                            self.CheckDevStatus = data[0]
                        print(f"self.CheckDevStatus: {self.CheckDevStatus}")
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml("<br>")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml("<br>")
            else:
                if debug == True:
                    self.log.logger.debug(
                        f"指令{code}解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            self.insert_text_with_separator()
            self.success_count += 1
            if self.timeout_timer:
                self.timeout_timer.cancel()
            print(f"self.success_count: {self.success_count}")
            print(f"self.__except_commands: {self.__except_commands}")
            self.process_command_queue()  # 解析成功后继续发送下一条指令"


        else:
            self.insert_text_with_separator()
            if debug == True:
                self.log.logger.debug("Failed to parse response.")
            # logging.debug("Failed to parse response.")

    def parsed_result(self,parsed_result):
        if parsed_result:
            self.response_received = True
            # logging.debug("Response parsed successfully.")
            code = parsed_result['code']
            # logging.debug("Parsed code:{}".format(code))
            length = parsed_result['length']
            type = parsed_result['type']
            data = parsed_result['data']
            macAddress = parsed_result['address']
            data_field_str = ' '.join([f"{byte:02X}" for byte in data])
            if debug == True:
                self.log.logger.debug("开始进行数据解析......\r\n")
            # logging.debug("Parsed D0~Dn_str:{}".format(data_field_str))
            self.textBrowserReceive.insertPlainText("开始进行数据解析......\r\n")
            self.textBrowserReceive.insertPlainText("\r\n")
            self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)  # 将坐标移动到文本结尾，
            if code == '00000007' and length == '1B':
                last_six_data = data[-6:]  # 获取最后六个字节

                # 反向读取地址
                address = last_six_data[::-1]  # 反转地址字节序列

                # 打印结果
                # logging.debug("Last six bytes of data: {}".format(last_six_data))
                # logging.debug("Reversed address: {}".format(address))

                # 如果想以十六进制格式打印：
                last_six_data_hex = ''.join([f"{byte:02X}" for byte in last_six_data])
                address_hex = ''.join([f"{byte:02X}" for byte in address])

                # logging.debug(f"Last six bytes (hex): {last_six_data_hex}")
                # logging.debug(f"Reversed address (hex): {address_hex}")

                # 输出
                # print(f"Last six bytes (hex): {last_six_data_hex}")
                # print(f"Reversed address (hex): {address_hex}")
                if debug == True:
                    self.log.logger.debug("Last six bytes of data: {}".format(last_six_data))
                    self.log.logger.debug("Reversed address: {}".format(address))
                    self.log.logger.debug(f"Last six bytes (hex): {last_six_data_hex}")
                    self.log.logger.debug(f"Reversed address (hex): {address_hex}")
                    self.log.logger.debug(f"指令{code}解析成功，<br>数据域是{data_field_str}")

                self.textBrowserReceive.insertHtml(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
                self.send_command(self.utils.send_commands_00000007())
            elif code == '00000008':
                # 初始化 platform 数组
                version = [0, 0, 0]
                v = data[::-1]
                # logging.debug("version_data: {}".format(v))
                # 解析字节并进行位移操作
                version[0] = v[0]   # 第一个元素
                version[1] = v[1]  # 第二个元素，v[2]
                version[2] = v[3] + (v[2] << 8)   # 第三个元素，v[3]
                # print(f"version: {version}")
                version_DEC = '.'.join([f"{byte}" for byte in version])
                # print(f"version: {version_DEC}")
                if debug == True:
                    self.log.logger.debug(f"指令{code}解析成功，<br>数据域是{data_field_str},版本号是{version_DEC}")
                self.textBrowserReceive.insertHtml(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str},<br>版本号是<span style='color:red;'>{version_DEC}</span>")
                self.textBrowserReceive.insertHtml("<br>")

            elif code == 'F20B000A':
                if debug == True:
                    self.log.logger.debug(f"指令{code}解析成功，<br>数据域是{data_field_str},序列号是{data_field_str}")
                self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<br>序列号是<span style='color:red;'>{data_field_str}</span>")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == 'F20B0000':

                if type == '82':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    # print(f"Master MAC: {data_field}")
                    if data_field == '00':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str},配置成功!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，配置成功!!!")
                    elif data_field == '05':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str},检验失败，需要检查参数累加和校验字节!!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>检验失败，需要检查参数累加和校验字节!!!</span>")
                    elif data_field == 'FF':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str},配置的模块 MAC 地址参数为非法值!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>配置的模块 MAC 地址参数为非法值!!!</span>")
                    else:
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str},配置的模块 MAC 地址参数为非法值!!!")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>配置的模块 MAC 地址参数为非法值!!!</span>")
                elif type == '83':
                    # 本机 MAC 地址
                    master_mac = data[0:6]
                    print(f"Master MAC: {self.format_mac(master_mac)}")

                    # 从机 1 MAC 地址
                    slave_1_mac = data[6:12]
                    print(f"Slave 1 MAC: {self.format_mac(slave_1_mac)}")

                    # 从机 2 MAC 地址
                    slave_2_mac = data[12:18]
                    print(f"Slave 2 MAC: {self.format_mac(slave_2_mac)}")

                    # 从机 3 MAC 地址
                    slave_3_mac = data[18:24]
                    print(f"Slave 3 MAC: {self.format_mac(slave_3_mac)}")

                    # 厂商 ID
                    manufacturer_id = data[24:26]
                    print(f"Manufacturer ID: {''.join([f'{b:02X}' for b in manufacturer_id])}")

                    # 设备类型
                    device_type = data[26]
                    print(f"Device Type: 0x{device_type:02X}")

                    # 特征校验码
                    feature_code = data[27:29]
                    print(f"Feature Code: {''.join([f'{b:02X}' for b in feature_code])}")

                    # 主通道配对 PIN 码密文
                    master_pin = data[29:45]
                    print(f"Master Channel PIN: {''.join([f'{b:02X}' for b in master_pin])}")

                    # 主通道配对码
                    master_pairing_code = data[45:51]
                    print(f"Master Channel Pairing Code: {''.join([f'{b:02X}' for b in master_pairing_code])}")

                    # 从通道配对码
                    slave_pairing_code = data[51:69]
                    print(f"Slave Channel Pairing Code: {''.join([f'{b:02X}' for b in slave_pairing_code])}")

                    # 校验和
                    checksum = data[-1]
                    print(f"Checksum: 0x{checksum:02X}")
                    # 计算校验和
                    calculated_checksum = sum(data[:-3]) % 256
                    print(f"calculated_checksum: 0x{calculated_checksum:02X}")
                    if debug == True:
                        self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>本机 MAC 地址是<span style='color:red;'>{self.format_mac(master_mac)}</span>"
                        f",<br>从机1MAC 地址是<span style='color:red;'>{self.format_mac(slave_1_mac)}</span>"
                        f",<br>从机2MAC 地址是<span style='color:red;'>{self.format_mac(slave_2_mac)}</span>"
                        f",<br>从机3MAC 地址是<span style='color:red;'>{self.format_mac(slave_3_mac)}</span>"
                        f",<br>厂商 ID是<span style='color:red;'>{''.join([f'{b:02X}' for b in manufacturer_id])}</span>"
                        f",<br>设备类型是<span style='color:red;'>{device_type:02X}</span>"
                        f",<br>特征校验码是<span style='color:red;'>{''.join([f'{b:02X}' for b in feature_code])}</span>"
                        f",<br>主通道配对 PIN 码加密后的密文(明文 模式)是<span style='color:red;'>{''.join([f'{b:02X}' for b in master_pin])}</span>"
                        f",<br>主通道配对码是<span style='color:red;'>{''.join([f'{b:02X}' for b in master_pairing_code])}</span>"
                        f",<br>从通道配对码是<span style='color:red;'>{''.join([f'{b:02X}' for b in slave_pairing_code])}</span>")
                    # 校验校验和
                    # if checksum != calculated_checksum:
                    self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>本机 MAC 地址是<span style='color:red;'>{self.format_mac(master_mac)}</span>"
                        f",<br>从机1MAC 地址是<span style='color:red;'>{self.format_mac(slave_1_mac)}</span>"
                        f",<br>从机2MAC 地址是<span style='color:red;'>{self.format_mac(slave_2_mac)}</span>"
                        f",<br>从机3MAC 地址是<span style='color:red;'>{self.format_mac(slave_3_mac)}</span>"
                        f",<br>厂商 ID是<span style='color:red;'>{''.join([f'{b:02X}' for b in manufacturer_id])}</span>"
                        f",<br>设备类型是<span style='color:red;'>{device_type:02X}</span>"
                        f",<br>特征校验码是<span style='color:red;'>{''.join([f'{b:02X}' for b in feature_code])}</span>"
                        f",<br>主通道配对 PIN 码加密后的密文(明文 模式)是<span style='color:red;'>{''.join([f'{b:02X}' for b in master_pin])}</span>"
                        f",<br>主通道配对码是<span style='color:red;'>{''.join([f'{b:02X}' for b in master_pairing_code])}</span>"
                        f",<br>从通道配对码是<span style='color:red;'>{''.join([f'{b:02X}' for b in slave_pairing_code])}</span>")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == 'F20B0002':
                if type == '82':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    # print(f"Master MAC: {data_field}")
                    if data_field == '00':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，设置参数成功!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，设置参数成功!!!")
                    elif data_field == 'FF':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，设置失败（参数不符合允许设定范围）!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>设置失败（参数不符合允许设定范围）!!!</span>")
                    else:
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，设置失败（参数不符合允许设定范围）!!!")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>设置失败（参数不符合允许设定范围）!!!</span>")
                elif type == '83':
                    # 解析发射功率档位
                    power_level = data[0]  # 0x00
                    if power_level == 0x00:
                        power_dbm = 4  # 发射功率档位 0 代表 4dBm
                    elif power_level == 0x01:
                        power_dbm = 0
                    elif power_level == 0x02:
                        power_dbm = -4
                    elif power_level == 0x03:
                        power_dbm = -20
                    else:
                        power_dbm = "Unknown"
                        # 解析广播间隔
                    broadcast_interval = data[2] << 8 | data[1]  # 0x28 00 -> 40
                    broadcast_interval_ms = broadcast_interval * 1.0  # 单位是毫秒

                    # 解析扫描间隔
                    scan_interval = data[4] << 8 | data[3]  # 0xA0 00 -> 160
                    scan_interval_ms = scan_interval * 1.0  # 单位是毫秒
                    if debug == True:
                        self.log.logger.debug(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>发射功率是<span style='color:red;'>{power_dbm}</span> dBm"
                        f",<br>广播间隔是<span style='color:red;'>{broadcast_interval_ms}</span>ms,允许设定范围： 40~ 1000ms"
                        f",<br>扫描间隔是<span style='color:red;'>{scan_interval_ms}</span>ms,允许设定范 围：55~ 110ms")
                    self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>发射功率是<span style='color:red;'>{power_dbm}</span> dBm"
                        f",<br>广播间隔是<span style='color:red;'>{broadcast_interval_ms}</span>ms,允许设定范围： 40~ 1000ms"
                        f",<br>扫描间隔是<span style='color:red;'>{scan_interval_ms}</span>ms,允许设定范 围：55~ 110ms")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
                self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)  # 将坐标移动到文本结尾，
            elif code == 'F20B0003':
                if type == '84':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    print(f"Master MAC: {data_field}")
                    if data_field == '00':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，通知上报接收成功!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，通知上报接收成功!!!")
                    elif data_field == 'FF':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，通知上报接收失败!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>通知上报接收失败!!!</span>")
                    else:
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，通知上报接收失败!!!")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>通知上报接收失败!!!</span>")
                elif type == '04' or type == '83':
                    self.connection_status = data[0]
                    print(f"Connection Status: 0x{self.connection_status:02X} ({bin(self.connection_status)})")
                    status_dict = self.parse_connection_status(self.connection_status)
                    print(f"status_dict: {status_dict}")
                    # 用来存储解析后的结果
                    mac_addresses = {}
                    start_index = 1  # 数据的起始位置
                    for key in status_dict:
                        end_index = start_index + 6  # 计算当前key对应数据的结束位置
                        value = data[start_index:end_index][::-1]  # 截取数据
                        value_str = ':'.join([f"{b:02X}" for b in value])  # 转换为十六进制字符串
                        mac_addresses[key] = value_str
                        start_index = end_index  # 更新起始位置
                    # # 主机 1 MAC 地址
                    # master_1_mac = data[1:7][::-1]
                    # master_1_mac_str = ':'.join([f"{b:02X}" for b in master_1_mac])
                    # print(f"Master 1 MAC: {master_1_mac_str}")
                    #
                    # # 主机 2 MAC 地址
                    # master_2_mac = data[7:13]
                    # master_2_mac_str = ':'.join([f"{b:02X}" for b in master_2_mac])
                    # print(f"Master 2 MAC: {master_2_mac_str}")
                    #
                    # # 从机 1 MAC 地址
                    # slave_1_mac = data[13:19]
                    # slave_1_mac_str = ':'.join([f"{b:02X}" for b in slave_1_mac])
                    # print(f"Slave 1 MAC: {slave_1_mac_str}")
                    #
                    # # 从机 2 MAC 地址
                    # slave_2_mac = data[19:25]
                    # slave_2_mac_str = ':'.join([f"{b:02X}" for b in slave_2_mac])
                    # print(f"Slave 2 MAC: {slave_2_mac_str}")
                    #
                    # # 从机 3 MAC 地址
                    # slave_3_mac = data[25:31]
                    # slave_3_mac_str = ':'.join([f"{b:02X}" for b in slave_3_mac])
                    # print(f"Slave 3 MAC: {slave_3_mac_str}")
                    if debug == True:
                        log_message = (
                            f"指令{code}解析成功，<br>数据域是{data_field_str}"
                            f",连接状态标识是<span style='color:red;'>{self.connection_status:02X}</span>"
                        )
                        for name, mac in mac_addresses.items():
                            log_message += f", <br>{name} MAC 地址是<span style='color:red;'> {mac}</span>"
                        self.log.logger.debug(log_message)
                    self.textBrowserReceive.insertHtml(log_message)
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == 'F20B0008':
                if type == '82':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    print(f"Master MAC: {data_field}")
                    if data_field == '00':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，参数配置成功!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，参数配置成功!!!")
                    elif data_field == 'FF':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，参数非法（参数长度超长）!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>参数非法（参数长度超长）!!!</span>")
                    else:
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，参数非法（请检查）!!!")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>参数非法（请检查）!!!</span>")
                elif type == '83':
                    # 主机 1 MAC 地址
                    local_mac = data[0:6]
                    master_1_mac_str = ':'.join([f"{b:02X}" for b in local_mac])
                    print(f"Master 1 MAC: {master_1_mac_str}")

                    # 主通道 1 配对 PIN 码长度（第 7 字节）
                    channel_1_pin_length = data[6]
                    print(f"channel_1_pin_length: {channel_1_pin_length}")
                    # 主通道 1 配对 PIN 码（第 8-13 字节）
                    channel_1_pin = data[7:13]
                    channel_1_pin_str = ''.join([f"{b:02X}" for b in channel_1_pin])
                    print(f"channel_1_pin_str: {channel_1_pin_str}")
                    # 主通道 1 配对 PIN 码加密密文长度（第 14 字节）
                    channel_1_encrypted_pin_length = data[13]
                    print(f"channel_1_encrypted_pin_length: {channel_1_encrypted_pin_length}")
                    # 主通道 1 配对 PIN 码密文广播数据（第 15-30 字节）
                    channel_1_encrypted_pin = data[14:30]
                    channel_1_encrypted_pin_str = ''.join([f"{b:02X}" for b in channel_1_encrypted_pin])
                    print(f"channel_1_encrypted_pin_str: {channel_1_encrypted_pin_str}")
                    # 主通道 2 配对 PIN 码长度（第 31 字节）
                    channel_2_pin_length = data[30]
                    print(f"channel_2_pin_length: {channel_2_pin_length}")
                    # 主通道 2 配对 PIN 码（第 32-37 字节）
                    channel_2_pin = data[31:37]
                    channel_2_pin_str = ''.join([f"{b:02X}" for b in channel_2_pin])
                    print(f"channel_2_pin_str: {channel_2_pin_str}")
                    # 主通道 2 配对 PIN 码加密密文长度（第 38 字节）
                    channel_2_encrypted_pin_length = data[37]
                    print(f"channel_2_encrypted_pin_length: {channel_2_encrypted_pin_length}")
                    # 主通道 2 配对 PIN 码密文广播数据（第 39-54 字节）
                    channel_2_encrypted_pin = data[38:54]
                    channel_2_encrypted_pin_str = ''.join([f"{b:02X}" for b in channel_2_encrypted_pin])
                    print(f"channel_2_encrypted_pin_str: {channel_2_encrypted_pin_str}")
                    if debug == True:
                        self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>模块本地 MAC 地址是<span style='color:red;'>{master_1_mac_str}</span>"
                        f",<br>主通道 1 配对 PIN 码长度是<span style='color:red;'>{channel_1_pin_length}</span>"
                        f",<br>主通道 1 配对 PIN 码是<span style='color:red;'>{channel_1_pin_str}</span>"
                        f",<br>主通道 1 配对 PIN 码加密密文长度是<span style='color:red;'>{channel_1_encrypted_pin_length}</span>"
                        f",<br>主通道 1 配对 PIN 码密文广播数据是<span style='color:red;'>{channel_1_encrypted_pin_str}</span>"
                        f",<br>主通道 2 配对 PIN 码长度是<span style='color:red;'>{channel_2_pin_length}</span>"
                        f",<br>主通道 2 配对 PIN 码是<span style='color:red;'>{channel_2_pin_str}</span>"
                        f",<br>主通道 2 配对 PIN 码加密密文长度是<span style='color:red;'>{channel_2_encrypted_pin_length}</span>"
                        f",<br>主通道 2 配对 PIN 码密文广播数据是<span style='color:red;'>{channel_2_encrypted_pin_str}</span>")
                    self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>模块本地 MAC 地址是<span style='color:red;'>{master_1_mac_str}</span>"
                        f",<br>主通道 1 配对 PIN 码长度是<span style='color:red;'>{channel_1_pin_length}</span>"
                        f",<br>主通道 1 配对 PIN 码是<span style='color:red;'>{channel_1_pin_str}</span>"
                        f",<br>主通道 1 配对 PIN 码加密密文长度是<span style='color:red;'>{channel_1_encrypted_pin_length}</span>"
                        f",<br>主通道 1 配对 PIN 码密文广播数据是<span style='color:red;'>{channel_1_encrypted_pin_str}</span>"
                        f",<br>主通道 2 配对 PIN 码长度是<span style='color:red;'>{channel_2_pin_length}</span>"
                        f",<br>主通道 2 配对 PIN 码是<span style='color:red;'>{channel_2_pin_str}</span>"
                        f",<br>主通道 2 配对 PIN 码加密密文长度是<span style='color:red;'>{channel_2_encrypted_pin_length}</span>"
                        f",<br>主通道 2 配对 PIN 码密文广播数据是<span style='color:red;'>{channel_2_encrypted_pin_str}</span>")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == 'F20B0009':
                if type == '82':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    print(f"data_field: {data_field}")
                    if data_field == '00':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，参数配置成功!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，参数配置成功!!!")
                    elif data_field == 'FF':
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，参数配置非法（参数超过最大长度）!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>参数配置非法（参数超过最大长度）!!!</span>")
                    else:
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}，参数配置非法（请检查）!!!")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>参数配置非法（请检查）!!!</span>")
                elif type == '83':
                    # 从机 1 MAC 地址
                    slave_1_mac = data[0:6]
                    slave_1_mac_str = ':'.join([f"{b:02X}" for b in slave_1_mac])
                    print(f"Slave 1 MAC: {slave_1_mac_str}")

                    # 从机 1 配对 PIN 码长度，6 字节
                    channel_1_pin_length = data[6]
                    print(f"channel_1_pin_length: {channel_1_pin_length}")
                    # 从机 1 配对 PIN 码
                    channel_1_pin = data[7:13]
                    channel_1_pin_str = ''.join([f"{b:02X}" for b in channel_1_pin])
                    print(f"channel_1_pin_str: {channel_1_pin_str}")
                    # 从机 2 MAC 地址
                    slave_2_mac = data[13:19]
                    slave_2_mac_str = ':'.join([f"{b:02X}" for b in slave_2_mac])
                    print(f"Slave 2 MAC: {slave_2_mac_str}")
                    # 从机 2 配对 PIN 码长度，6 字节
                    channel_2_pin_length = data[20]
                    print(f"channel_2_pin_length: {channel_2_pin_length}")
                    # 从机 2 配对 PIN 码
                    channel_2_pin = data[21:27]
                    channel_2_pin_str = ''.join([f"{b:02X}" for b in channel_2_pin])
                    print(f"channel_2_pin_str: {channel_2_pin_str}")
                    # 从机 3 MAC 地址
                    slave_3_mac = data[28:34]
                    slave_3_mac_str = ':'.join([f"{b:02X}" for b in slave_3_mac])
                    print(f"Slave 3 MAC: {slave_3_mac_str}")
                    # 从机 3 配对 PIN 码长度，6 字节
                    slave_3_pin_length = data[35]
                    print(f"slave_3_pin_length: {slave_3_pin_length}")
                    # 从机 3 配对 PIN 码
                    slave_3_pin = data[36:42]
                    slave_3_pin_str = ''.join([f"{b:02X}" for b in slave_3_pin])
                    print(f"slave_3_pin_str: {slave_3_pin_str}")
                    if debug == True:
                        self.log.logger.debug(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>从机 1 MAC 地址是<span style='color:red;'>{slave_1_mac_str}</span>"
                        f",<br>从机 1 配对 PIN 码长度是<span style='color:red;'>{channel_1_pin_length}</span>"
                        f",<br>从机 1 配对 PIN 码是<span style='color:red;'>{channel_1_pin_str}</span>"
                        f",<br>从机 2 MAC 地址是<span style='color:red;'>{slave_2_mac_str}</span>"
                        f",<br>从机 2 配对 PIN 码长度是<span style='color:red;'>{channel_2_pin_length}</span>"
                        f",<br>从机 2 配对 PIN 码是<span style='color:red;'>{channel_2_pin_str}</span>"
                        f",<br>从机 3 MAC 地址是<span style='color:red;'>{slave_3_mac_str}</span>"
                        f",<br>从机 3 配对 PIN 码长度是<span style='color:red;'>{slave_3_pin_length}</span>"
                        f",<br>从机 3 配对 PIN 码是<span style='color:red;'>{slave_3_pin_str}</span>")

                    self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                        f",<br>从机 1 MAC 地址是<span style='color:red;'>{slave_1_mac_str}</span>"
                        f",<br>从机 1 配对 PIN 码长度是<span style='color:red;'>{channel_1_pin_length}</span>"
                        f",<br>从机 1 配对 PIN 码是<span style='color:red;'>{channel_1_pin_str}</span>"
                        f",<br>从机 2 MAC 地址是<span style='color:red;'>{slave_2_mac_str}</span>"
                        f",<br>从机 2 配对 PIN 码长度是<span style='color:red;'>{channel_2_pin_length}</span>"
                        f",<br>从机 2 配对 PIN 码是<span style='color:red;'>{channel_2_pin_str}</span>"
                        f",<br>从机 3 MAC 地址是<span style='color:red;'>{slave_3_mac_str}</span>"
                        f",<br>从机 3 配对 PIN 码长度是<span style='color:red;'>{slave_3_pin_length}</span>"
                        f",<br>从机 3 配对 PIN 码是<span style='color:red;'>{slave_3_pin_str}</span>")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            elif code == '00000000':

                if type == '81':
                    mac_Address = self.format_mac(macAddress[::-1])
                    macAddress_str = ''.join([f"{b:02X}" for b in macAddress[::-1]])
                    print(f"mac_Address: {macAddress_str}")
                    print(f"masterMac: {self.mac_info['masterMac']}")
                    print(f"slaveMac: {self.mac_info['slaveMac']}")
                    omd = data[17:21]
                    omd_str = ''.join([f"{b:02X}" for b in omd])
                    print(f"omd_str: {omd_str}")
                    if omd_str == 'F20B0200':
                        data_hex = "FEFEFEFE68710001000000001DA594BCD9F70000000068FEFEFEFE686B00C30501000000000000459E850102F20B02000101010205110102020A2042545F4D455445520000000000000000000000000000000000000000000000000906C100000000010A0631323334353616020914FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000D0BA16B516"
                        command = [int(data_hex[i:i + 2], 16) for i in
                                              range(0, len(data_hex), 2)]
                        if debug == True:
                            self.log.logger.debug(
                                f"检定模式测试，透传指令{code}解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml(
                            f"检定模式测试，透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml("<br>")
                        self.send_command(command)
                    elif omd_str == 'F20B0B00':
                        data_hex = "FEFEFEFE68350001000000001DA594BCD9F70000000068FEFEFEFE682F00C30501000000000000150D850103F20B0B00010914D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D9D90000E60B160C16"
                        command = [int(data_hex[i:i + 2], 16) for i in
                                   range(0, len(data_hex), 2)]
                        if debug == True:
                            self.log.logger.debug(
                                f"检定模式测试，透传指令{code}解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml(
                            f"检定模式测试，透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml("<br>")
                        self.send_command(command)
                    elif omd_str == 'F20B8000':
                        parsed_result = self.parse_FFFF0005_packet(data)
                        print(parsed_result)
                        # pulse_type = parsed_result['pulse_type']
                        # channel_interval = parsed_result['channel_interval']
                        # transmit_power = parsed_result['transmit_power']
                        # comm_address = parsed_result['comm_address']
                        # frequency_points_1 = parsed_result['frequency_points_1']
                        # frequency_points_2 = parsed_result['frequency_points_2']
                        # frequency_points_3 = parsed_result['frequency_points_3']
                        # frequency_points_4 = parsed_result['frequency_points_4']
                        # frequency_points_5 = parsed_result['frequency_points_5']
                        # 将 pulse_type 转换为整数
                        pulse_type = int(parsed_result['pulse_type'], 16)

                        # 定义一个字典来映射不同的 pulse_type 对应的解释
                        pulse_type_dict = {
                            0: "秒脉冲",
                            1: "需量周期",
                            2: "时段投切",
                            3: "正向谐波脉冲",
                            4: "反向谐波脉冲",
                            5: "无功脉冲",
                            6: "有功脉冲",
                            255: "关闭/退出检定"
                        }

                        # 判断 pulse_type 对应的解释
                        pulse_type_desc = pulse_type_dict.get(pulse_type, "未知脉冲类型")
                        # 输出结果
                        print(f"脉冲类型: {pulse_type_desc}")
                        # 将 channel_interval 转换为整数，单位为 ms
                        channel_interval = int(parsed_result['channel_interval'], 16)  # 16进制转换为整数

                        # transmit_power 的取值范围：0≤tx_power≤4
                        transmit_power = int(parsed_result['transmit_power'], 16)

                        # 判断发射功率并返回相应的值
                        transmit_power_dict = {
                            0: "4 dBm",
                            1: "0 dBm",
                            2: "-4 dBm",
                            3: "-8 dBm",
                            4: "-20 dBm"
                        }

                        # 获取 transmit_power 的对应功率
                        transmit_power_desc = transmit_power_dict.get(transmit_power, "无效的发射功率")
                        comm_address = parsed_result['comm_address']
                        comm_address_str = ' '.join([f"{b:02X}" for b in comm_address])
                        print(f"mac_Address: {comm_address_str}")
                        # 输出结果
                        print(f"信道发射间隔: {channel_interval} ms")
                        print(f"发射功率: {transmit_power_desc}")
                        if debug == True:
                            self.log.logger.debug(
                            f"检定模式测试，透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",<br>脉冲值：{pulse_type}，类型: <span style='color:red;'>{pulse_type_desc}</span>"
                            f",<br>信道发射间隔: <span style='color:red;'>{channel_interval}</span> ms"
                            f",<br>发射功率: <span style='color:red;'>{transmit_power_desc}</span>"
                            f",<br>检定通信地址 A5~A0是<span style='color:red;'>{comm_address_str}</span>")
                        self.textBrowserReceive.insertHtml(
                            f"检定模式测试，透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",<br>脉冲值：{pulse_type}，类型: <span style='color:red;'>{pulse_type_desc}</span>"
                            f",<br>信道发射间隔: <span style='color:red;'>{channel_interval}</span> ms"
                            f",<br>发射功率: <span style='color:red;'>{transmit_power_desc}</span>"
                            f",<br>检定通信地址 A5~A0是<span style='color:red;'>{comm_address_str}</span>")
                        for i in range(1, 6):
                            point_key = f'frequency_points_{i}'
                            frequency_value = self.parse_frequency(parsed_result[point_key])
                            print(f"frequency_value: {frequency_value}")
                            if frequency_value == 0xFFFF:
                                if debug == True:
                                    self.log.logger.debug(
                                    f"<br><span style='color:red;'>频点 {i}: 未配置 (FF FF)</span>")
                                self.textBrowserReceive.insertHtml(
                                    f"<br><span style='color:red;'>频点 {i}: 未配置 (FF FF)</span>")
                            elif 2360 <= frequency_value <= 2510:
                                if debug == True:
                                    self.log.logger.debug(
                                    f"<br>频点 {i}: <span style='color:red;'>{frequency_value}</span> MHz")
                                self.textBrowserReceive.insertHtml(
                                    f"<br>频点 {i}: <span style='color:red;'>{frequency_value}</span> MHz")
                            else:
                                if debug == True:
                                    self.log.logger.debug(
                                    f"<br><span style='color:red;'>频点 {i}: {frequency_value} MHz (无效频点)</span>")
                                self.textBrowserReceive.insertHtml(
                                    f"<br><span style='color:red;'>频点 {i}: {frequency_value} MHz (无效频点)</span>")
                        self.textBrowserReceive.insertHtml("<br>")
                        data_hex = "FEFEFEFE68200001000000001DA594BCD9F70000000068FEFEFEFE681A00C305010000000000001E95870100F20B800000000000E5EA16B316"
                        command = [int(data_hex[i:i + 2], 16) for i in
                                   range(0, len(data_hex), 2)]
                        self.send_command(command)
                        sleep(0.5)
                        self.send_command(self.utils.send_commands_FFFF0005(parsed_result))
                    else:
                        if debug == True:
                            self.log.logger.debug(f"透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",<br>报文类型是<span style='color:red;'>{type}</span>"
                            f",<br>A5~A0 源端 MAC 地址是<span style='color:red;'>{mac_Address}</span>")
                        self.textBrowserReceive.insertHtml(
                        f"透传指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}"
                            f",<br>报文类型是<span style='color:red;'>{type}</span>"
                            f",<br>A5~A0 源端 MAC 地址是<span style='color:red;'>{mac_Address}</span>")
                        self.textBrowserReceive.insertHtml("<br>")
                        self.insert_text_with_separator()
                        slaveMacList = []
                        for i in range(self.slaveMac.count()):
                            slaveMacList.append(self.slaveMac.itemText(i))
                        print(f"slaveMacList-------------------- {slaveMacList}")
                        if macAddress_str not in slaveMacList:
                            self.slaveMac.addItem(macAddress_str)
                        command_bytes = list(self.__RcvBuff)
                        # 检查第八个字节是否是 81
                        if command_bytes[7] == 0x81:
                            print("第八个字节是 81，将其替换为 01")
                            command_bytes[7] = 0x01
                        else:
                            print(f"第八个字节不是 81，是 {hex(command_bytes[7])}")
                        length_bytes = command_bytes[5:7][::-1]
                        length_s = length_bytes[0] * 256 + length_bytes[1]

                        data_field = command_bytes[23:23 + length_s]
                        header = data_field[:4]
                        if header != [0xFE, 0xFE, 0xFE, 0xFE]:
                            header = [0xFE, 0xFE, 0xFE, 0xFE]
                            data_field_n = header + data_field
                            length_s = length_s + 4
                            L = list(struct.pack('<H', length_s))
                            command_bytes[5:7] = L
                            command_bytes[23:23 + length_s] = data_field_n
                            print(f"length_s，是 {length_s}")
                            print(f"command_bytes[5:7]，是 {self.format_mac(command_bytes[5:7])}")
                            calculated_checksum = sum(command_bytes[4:23 + length_s]) % 256
                            print(f"calculated_checksum，是 {calculated_checksum}")
                            command_bytes.append(calculated_checksum)
                            command_bytes += [0x16]
                            print(f"command_bytes: {self.format_mac(command_bytes)}")
                            self.send_command(command_bytes)
                        else:
                            calculated_checksum = sum(command_bytes[4:23 + length_s]) % 256
                            print(f"calculated_checksum，是 {calculated_checksum}")
                            command_bytes[23 + length_s] = calculated_checksum
                            print(f"command_bytes: {self.format_mac(command_bytes)}")
                            self.send_command(command_bytes)

                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml("<br>")
            elif code == 'FFFF0005':
                if type == '82':
                    data_field = ''.join([f"{byte:02X}" for byte in data])
                    print(f"data_field: {data_field}")
                    if data_field == '00':
                        if debug == True:
                            self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，检定模式,电能表管理 MCU,下发给蓝牙模块,配置成功!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，检定模式,电能表管理 MCU,下发给蓝牙模块,配置成功!!!")
                    elif data_field == 'FF':
                        if debug == True:
                            self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，检定模式,电能表管理 MCU,下发给蓝牙模块,配置失败!!!")
                        self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>检定模式,电能表管理 MCU,下发给蓝牙模块,配置失败!!!</span>")
                    else:
                        if debug == True:
                            self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，检定模式,电能表管理 MCU,下发给蓝牙模块,配置失败!!!")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<span style='color:red;'>检定模式,电能表管理 MCU,下发给蓝牙模块,配置失败!!!</span>")
                    self.textBrowserReceive.insertHtml("<br>")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml("<br>")
            elif code == '0000002E':
                if type == '83':
                    if len(data) == 8:
                        local_platform_major = data[0] + (data[1] << 8)
                        local_platform_minor = data[2]
                        local_platform_patch = data[3]
                        self.localPlatformVersion = f"{local_platform_major}.{local_platform_minor}.{local_platform_patch}"
                        local_app_major = data[4] + (data[5] << 8)
                        local_app_minor = data[6]
                        local_app_patch = data[7]
                        self.localAppVersion = f"{local_app_major}.{local_app_minor}.{local_app_patch}"
                        if debug == True:
                            self.log.logger.debug(f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<br><span style='color:red;'>Local: app:{self.localAppVersion} | platform:{self.localPlatformVersion}  </span>")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}，<br><span style='color:red;'>Local: app:{self.localAppVersion} | platform:{self.localPlatformVersion}  </span>")
                        self.textBrowserReceive.insertHtml("<br>")
                        self.label_Local.setText(f"Local: app:{self.localAppVersion} | platform:{self.localPlatformVersion}")
                        self.label_Local.show()
                        self.plan = self.build_update_plan()
                    else:
                        if len(data) == 1:
                            self.CheckDevStatus = data[0]
                        print(f"self.CheckDevStatus: {self.CheckDevStatus}")
                        if debug == True:
                            self.log.logger.debug(
                                f"指令{code}解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml(
                            f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                        self.textBrowserReceive.insertHtml("<br>")
                else:
                    if debug == True:
                        self.log.logger.debug(
                            f"指令{code}解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml(
                        f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                    self.textBrowserReceive.insertHtml("<br>")
            else:
                if debug == True:
                    self.log.logger.debug(
                        f"指令{code}解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml(
                    f"指令<b>{code}</b>解析成功，<br>数据域是{data_field_str}")
                self.textBrowserReceive.insertHtml("<br>")
            self.insert_text_with_separator()
            self.success_count += 1
            if self.timeout_timer:
                self.timeout_timer.cancel()
            print(f"self.success_count: {self.success_count}")
            print(f"self.__except_commands: {self.__except_commands}")
            self.process_command_queue()  # 解析成功后继续发送下一条指令"


        else:
            self.insert_text_with_separator()
            if debug == True:
                self.log.logger.debug("Failed to parse response.")
            # logging.debug("Failed to parse response.")
    def parse_FFFF0005_packet(self, byte_list):

        pulse_type = byte_list[29]
        print(f"pulse_type: {pulse_type}")
        channel_interval = byte_list[31]
        print(f"channel_interval: {channel_interval}")
        transmit_power = byte_list[33]
        print(f"transmit_power: {transmit_power}")
        comm_address = byte_list[36:42]
        comm_address_str = ''.join([f"{byte:02X}" for byte in comm_address])
        # logging.debug("comm_address_str:{}".format(comm_address_str))

        frequency_points_1 = byte_list[45:47]
        print(f"frequency_points_1: {self.format_mac(frequency_points_1)}")
        # logging.debug("frequency_points_1: {}".format([hex(b) for b in frequency_points_1]))
        frequency_points_2 = byte_list[48:50]
        print(f"frequency_points_2: {self.format_mac(frequency_points_2)}")
        # logging.debug("frequency_points_2: {}".format([hex(b) for b in frequency_points_2]))
        frequency_points_3 = byte_list[51:53]
        print(f"frequency_points_3: {self.format_mac(frequency_points_3)}")
        # logging.debug("frequency_points_3: {}".format([hex(b) for b in frequency_points_3]))
        frequency_points_4 = byte_list[54:56]
        print(f"frequency_points_4: {self.format_mac(frequency_points_4)}")
        # logging.debug("frequency_points_4: {}".format([hex(b) for b in frequency_points_4]))
        frequency_points_5 = byte_list[57:59]
        print(f"frequency_points_5: {self.format_mac(frequency_points_5)}")
        # logging.debug("frequency_points_5: {}".format([hex(b) for b in frequency_points_5]))
        if debug == True:
            self.log.logger.debug(f"pulse_type: {pulse_type}")
            self.log.logger.debug(f"channel_interval: {channel_interval}")
            self.log.logger.debug(f"transmit_power: {transmit_power}")
            self.log.logger.debug("comm_address_str:{}".format(comm_address_str))
            self.log.logger.debug("frequency_points_1: {}".format([hex(b) for b in frequency_points_1]))
            self.log.logger.debug("frequency_points_2: {}".format([hex(b) for b in frequency_points_2]))
            self.log.logger.debug("frequency_points_3: {}".format([hex(b) for b in frequency_points_3]))
            self.log.logger.debug("frequency_points_4: {}".format([hex(b) for b in frequency_points_4]))
            self.log.logger.debug("frequency_points_5: {}".format([hex(b) for b in frequency_points_5]))
        # 打印解析结果
        return {
            "pulse_type": f"{pulse_type:02X}",
            "channel_interval": f"{channel_interval:02X}",
            "transmit_power": f"{transmit_power:02X}",
            "comm_address": comm_address,
            "frequency_points_1": frequency_points_1,
            "frequency_points_2": frequency_points_2,
            "frequency_points_3": frequency_points_3,
            "frequency_points_4": frequency_points_4,
            "frequency_points_5": frequency_points_5
        }

    def parse_frequency(self,point):
        """将低字节和高字节组合为频率值"""
        low_byte, high_byte = point
        hex_value = (low_byte << 8) | high_byte
        # 转成十进制
        decimal_value = hex_value
        # 打印结果
        print(f"0x{hex_value:04X} 转成十进制: {decimal_value}")
        return decimal_value
    # 格式化 MAC 地址
    def format_mac(self, mac_bytes):
        return ':'.join([f'{b:02X}' for b in mac_bytes])
    @QtCore.pyqtSlot(str)
    def on_com_signalRcvError(self,txt):
        if debug == True:
            self.log.logger.error("串口异常关闭:{}".format(txt))
            # logging.error("串口异常关闭:{}".format(txt))
        #
        # self.on_pushButtonOpen_toggled(False)
        # 更新串口列表
        newportlistbuf = userSerial.getPortsList()
        self.__update_comboBoxPortList(newportlistbuf)  # 更新系统支持的串口设备并更新端口组合框内容

        pass

#     发送历史区
#     self.comboBoxSndHistory
#     def on_comboBoxSndHistory_currentIndexChanged(self, text):
        # self.textEditSend.setText(text)
        # self.textEditSend.moveCursor(self.textEditSend.textCursor().End)
    @QtCore.pyqtSlot(str)
    def on_comboBoxSndHistory_activated(self, text):
        if isinstance(text,str):
            self.textEditSend.setText(text)
            self.textEditSend.moveCursor(self.textEditSend.textCursor().End)

    def save_log_to_file(self):
        # 获取当前时间，生成当天的文件名
        current_date = datetime.now().strftime("%Y-%m-%d")
        file_name = f"test-{current_date}.log"

        # 获取 QTextBrowser 中的内容
        text_content = self.textBrowserReceive.toPlainText()

        # 如果文件存在，追加内容；否则，创建新文件并写入内容
        with open(file_name, 'a', encoding='utf-8') as file:
            file.write(f"\n\n--- 日志记录时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ---\n")
            file.write(text_content)

        print(f"日志已保存到: {file_name}")
    def process_command_queue(self):
        """处理命令队列"""

        if not self.command_queue:
            # logging.debug("All commands processed.")
            if debug == True:
                self.log.logger.debug("All commands processed.")
            self.pushButtonSend.setEnabled(True)
            self.singleButtonSend.setEnabled(True)
            print(f"__txPeriodEnable: {self.__txPeriodEnable}")
            if self.__txPeriodEnable == True:
                self.singleButtonSend.setEnabled(False)

            else:
                if self.__except_commands:
                    if debug == True:
                        self.log.logger.debug(f"\n\n---时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},异常指令测试,收到响应!!!---\n")
                    self.textBrowserReceive.insertPlainText(
                        f"\n\n---时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},异常指令测试,收到响应!!!---\n")
                    self.textBrowserReceive.insertPlainText("\r\n")
                else:
                    if debug == True:
                        self.log.logger.debug(f"\n\n---时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},指令测试结束!!!---\n")
                    self.textBrowserReceive.insertPlainText(
                        f"\n\n---时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},指令测试结束!!!---\n")
                    self.textBrowserReceive.insertPlainText("\r\n")
                # self.save_log_to_file()
            return
        if debug == True:
            self.log.logger.debug(
                "All commands processed end...............")
        # logging.debug("All commands processed end...............")
        self.current_command = self.command_queue.pop(0)
        print(f"self.current_command----------------: {self.current_command}")
        sleep(0.5)
        self.send_command(self.current_command)
        # 设置一个定时器检测回调是否超时 (假设超时时间为2秒)
        self.timeout_timer = threading.Timer(2.0, self.handle_timeout)
        self.timeout_timer.start()

    def send_count_timeout(self):
        print(f"定时测试指令总次数: {self.send_count} \r\n")
        if self.send_count > 0:
            self.__com.update_signal.emit(
                f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},定时测试指令总次数：<span style='color:red;'>{self.send_count}</span>，发送失败次数: <span style='color:red;'>{self.send_count - self.success_count}</span>，发送成功次数:<span style='color:red;'> {self.success_count}</span>")
            self.fail_count = 0
            self.send_count = 0
            self.success_count = 0
    def handle_timeout(self):
        if debug == True:
            self.log.logger.debug(
                f"指令 {self.current_command}响应超时，请检查该指令是否正确！！！\r\n")
        print(f"指令 {self.current_command} 超时，重新发送或跳过\r\n")
        hex_string_no_prefix = ' '.join(f'{byte:02X}' for byte in self.current_command)
        data_string = f"<span style='color:red;'>指令 {hex_string_no_prefix} 响应超时，请检查该指令是否正确！！！</span>"
        self.__com.update_signal.emit(data_string)
        # self.textBrowserReceive.insertPlainText(f"指令 {hex_string_no_prefix} 响应超时，请检查该指令是否正确！！！")
        # self.textBrowserReceive.insertPlainText("\r\n")
        # self.insert_text_with_separator()
        if self.__txPeriodEnable == True:
            print("超时未收到数据，记录为失败")
            self.fail_count += 1
        else:
            self.command_queue = []
            self.pushButtonSend.setEnabled(True)
            self.singleButtonSend.setEnabled(True)
            self.eButtonSend.setEnabled(True)


    def insert_text_with_separator(self):
        # 获取当前窗口的宽度（以像素为单位）
        viewport_width = self.textBrowserReceive.viewport().width()

        # 获取字符 "-" 的宽度，以便计算分割线的长度
        font_metrics = self.textBrowserReceive.fontMetrics()
        dash_width = font_metrics.horizontalAdvance('-')

        # 计算可以容纳的最大字符数
        max_chars = viewport_width // dash_width -2
        # 插入分割线
        separator = '-' * max_chars

        self.textBrowserReceive.insertPlainText(f"{separator}\n")

        # self.textBrowserReceive.insertPlainText("------------------------------------------------------------------------------------\r\n")
        self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)  # 将坐标移动到文本结尾，
    def send_command(self, command):
        """发送单条指令"""
        try:
            if self.__com.getPortState() == True:
                # logging.debug("send_command")
                # logging.debug(f"Sending command: {command.hex()}")
                hex_string_no_prefix = ' '.join(f'{byte:02X}' for byte in command)
                print(f"Sending command: {hex_string_no_prefix}")

                data_string = f"开始发送测试指令,{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}: <b>{hex_string_no_prefix}</b>"
                self.__com.update_signal.emit(data_string)
                # self.textBrowserReceive.insertHtml(f"开始发送测试指令: <b>{hex_string_no_prefix}</b>\r\n")
                # self.insert_text_with_separator()
                self.__com.send(command)
        except Exception as e:
            QMessageBox.critical(
                self, "Port Error", "串口被拔出或参数错误！请先检查好再重新打开串口！")
            if debug == True:
                print(f"串口发送数据时出错: {str(e)}")
                self.log.logger.error(
                    "串口发送数据失败:{}".format(e))
                # logging.error("串口发送数据失败:{}".format(e))
    def add_commands_to_queue(self, commands):
        """将多条命令加入队列"""
        self.command_queue.extend(commands)
        # print(self.command_queue)
        self.process_command_queue()
#     # 发送按钮
#     self.pushButtonSend
    # 超时回调函数
    def timeout_callback(self,current_command):
        print(f"指令 {current_command} 超时！未收到响应，继续发送下一条指令\r\n")

        hex_string_no_prefix = ' '.join(f'{byte:02X}' for byte in current_command)
        data_string = f"<span style='color:red;'>当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},指令 {hex_string_no_prefix} 响应超时，请检查该指令是否正确！！！</span>"
        self.__com.update_signal.emit(data_string)

    def except_commands(self):
        if self.__com.getPortState() == True:
            self.__except_commands = True
            self.response_received = False
            self.current_command = self.__commands[self.comboBoxCommand.currentText()]
            test_parts = self.utils.parse_except_packet(self.current_command)
            if self.comboBoxCommand.currentText() == 'F20B0000-set':

                hex_string_1 = "FE FE FE FF 68 46 00 02 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 68 C1 00 00 00 00 01 C3 00 00 00 00 01 C3 00 00 00 00 02 C3 00 00 00 00 03 FF FF C1 00 00 31 32 33 34 35 36 FF FF FF FF FF FF FF FF FF FF 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 CF AD 16"
                # 转换为字节列表
                byte_list_1 = [int(byte, 16) for byte in hex_string_1.split()]
                test_parts.append((byte_list_1, "异常指令: 前导码错误 FE FE FE FF 68 46 00 02...", True))

                hex_string_2 = "FE FE FE FE 69 46 00 02 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 68 C1 00 00 00 00 01 C3 00 00 00 00 01 C3 00 00 00 00 02 C3 00 00 00 00 03 FF FF C1 00 00 31 32 33 34 35 36 FF FF FF FF FF FF FF FF FF FF 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 CF AE 16"
                # 转换为字节列表
                byte_list_2 = [int(byte, 16) for byte in hex_string_2.split()]
                test_parts.append((byte_list_2, "异常指令: 帧起始符错误 FE FE FE FE 69 46 00 02...", True))

                hex_string_3 = "FE FE FE FE 68 66 00 02 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 68 C1 00 00 00 00 01 C3 00 00 00 00 01 C3 00 00 00 00 02 C3 00 00 00 00 03 FF FF C1 00 00 31 32 33 34 35 36 FF FF FF FF FF FF FF FF FF FF 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 CF CD 16"
                # 转换为字节列表
                byte_list_3 = [int(byte, 16) for byte in hex_string_3.split()]
                test_parts.append((byte_list_3, "异常指令: 数据长度错误 FE FE FE FE 68 66 00 02...", True))

                hex_string_4 = "FE FE FE FE 68 46 00 FF 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 68 C1 00 00 00 00 01 C3 00 00 00 00 01 C3 00 00 00 00 02 C3 00 00 00 00 03 FF FF C1 00 00 31 32 33 34 35 36 FF FF FF FF FF FF FF FF FF FF 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 CF AE 16"
                # 转换为字节列表
                byte_list_4 = [int(byte, 16) for byte in hex_string_4.split()]
                test_parts.append((byte_list_4, "异常指令: 报文类型错误 FE FE FE FE 68 46 00 FF 00 00...", True))

                hex_string_5 = "FE FE FE FE 68 46 00 02 FF FF 0B F2 FF FF FF FF FF FF 00 00 00 00 68 C1 00 00 00 00 01 C3 00 00 00 00 01 C3 00 00 00 00 02 C3 00 00 00 00 03 FF FF C1 00 00 31 32 33 34 35 36 FF FF FF FF FF FF FF FF FF FF 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 CF AB 16"
                # 转换为字节列表
                byte_list_5 = [int(byte, 16) for byte in hex_string_5.split()]
                test_parts.append((byte_list_5, "异常指令: 控制命令错误 FE FE FE FE 68 46 00 02 FF FF 0B F2...", True))

                hex_string_6 = "FE FE FE FE 68 46 00 02 00 00 0B F2 FF FF FF FF FF 12 00 00 00 00 68 C1 00 00 00 00 01 C3 00 00 00 00 01 C3 00 00 00 00 02 C3 00 00 00 00 03 FF FF C1 00 00 31 32 33 34 35 36 FF FF FF FF FF FF FF FF FF FF 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 CF C0 16"
                # 转换为字节列表
                byte_list_6 = [int(byte, 16) for byte in hex_string_6.split()]
                test_parts.append(
                    (byte_list_6, "异常指令: 设备地址错误 FE FE FE FE 68 46 00 02 00 00 0B F2 FF FF FF FF FF 12...", True))
                hex_string_7 = "FE FE FE FE 68 46 00 02 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 78 C1 00 00 00 00 01 C3 00 00 00 00 01 C3 00 00 00 00 02 C3 00 00 00 00 03 FF FF C1 00 00 31 32 33 34 35 36 FF FF FF FF FF FF FF FF FF FF 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 CF BD 16"
                # 转换为字节列表
                byte_list_7 = [int(byte, 16) for byte in hex_string_7.split()]
                test_parts.append(
                    (byte_list_7,
                     "异常指令: 数据域前的帧起始符错误 FE FE FE FE 68 46 00 02 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 78...", True))

                hex_string_8 = "FE FE FE FE 68 46 00 02 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 68 C1 00 00 00 00 01 C3 00 00 00 00 01 C3 00 00 00 00 02 C3 00 00 00 00 03 FF FF C1 00 00 31 32 33 34 35 36 FF FF FF FF FF FF FF FF FF FF 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 CF AF 16"
                # 转换为字节列表
                byte_list_8 = [int(byte, 16) for byte in hex_string_8.split()]
                test_parts.append(
                    (byte_list_8,
                     "异常指令: 校验码错误 FE FE FE FE 68 ...CF AF 16", True))

                hex_string_9 = "FE FE FE FE 68 46 00 02 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 68 C1 00 00 00 00 01 C3 00 00 00 00 01 C3 00 00 00 00 02 C3 00 00 00 00 03 FF FF C1 00 00 31 32 33 34 35 36 FF FF FF FF FF FF FF FF FF FF 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 CF AD 1F"
                # 转换为字节列表
                byte_list_9 = [int(byte, 16) for byte in hex_string_9.split()]
                test_parts.append(
                    (byte_list_9,
                     "异常指令: 结束符错误 FE FE FE FE 68 46 ...CF AD 1F", True))

                hex_string_10 = "FE FE FE FE 68 FF 00 02 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 68 C1 00 00 00 00 01 C3 00 00 00 00 01 C3 00 00 00 00 02 C3 00 00 00 00 03 FF FF C1 00 00 31 32 33 34 35 36 FF FF FF FF FF FF FF FF FF FF 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 CF 66 16"
                # 转换为字节列表
                byte_list_10 = [int(byte, 16) for byte in hex_string_10.split()]
                test_parts.append(
                    (byte_list_10,
                     "异常指令: 数据域长度太长大于len，立刻跟着第二帧 FE FE FE FE 68 FF 00 02 00 00 0B...", True))
                hex_string_11 = "FE FE FE FE 68 46 00 02 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 68 FE FE FE FE 00 01 C3 00 00 00 00 01 C3 00 00 00 00 02 C3 00 00 00 00 03 FF FF C1 00 00 31 32 33 34 35 36 FF FF FF FF FF FF FF FF FF FF 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 CF E4 16"
                # 转换为字节列表
                byte_list_11 = [int(byte, 16) for byte in hex_string_11.split()]
                test_parts.append(
                    (byte_list_11,
                     "异常指令: 数据域包含前导码 FE FE FE FE 68 46 00 02 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 68 FE FE FE FE...", False))
                hex_string_12 = "FE FE FE FE 68 46 00 02 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 68 FE FE FE FE 68 01 C3 00 00 00 00 01 C3 00 00 00 00 02 C3 00 00 00 00 03 FF FF C1 00 00 31 32 33 34 35 36 FF FF FF FF FF FF FF FF FF FF 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 CF 4C 16"
                # 转换为字节列表
                byte_list_12 = [int(byte, 16) for byte in hex_string_12.split()]
                test_parts.append(
                    (byte_list_12,
                     "异常指令: 数据域包含前导码和起始符 FE FE FE FE 68 46 00 02 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 68 FE FE FE FE 68...", False))
                hex_string_13 = "FE FE FE FE 68 46 00 02 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 68 FE FE FE FE 68 01 C3 00 00 00 00 01 C3 00 00 00 00 02 C3 00 00 00 00 03 FF FF C1 00 00 31 32 33 34 35 36 FF FF FF FF FF FF FF FF FF FF 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34 35 16 CF 2C 16"
                # 转换为字节列表
                byte_list_13 = [int(byte, 16) for byte in hex_string_13.split()]
                test_parts.append(
                    (byte_list_13,
                     "异常指令: 数据域包含前导码和起始符和结束符 FE FE FE FE 68 46 00 02 00 00 0B F2 FF FF FF FF FF FF 00 00 00 00 68 FE FE FE FE 68 01...", False))
                for part, description, should_send in test_parts:
                    # 设置超时计时器，200ms超时
                    self.response_received = False
                    hex_string_no_prefix = ' '.join(f'{byte:02X}' for byte in part)
                    data_string = f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},<span style='color:red;'>{description}</span>，发送内容：<b>{hex_string_no_prefix}</b>"
                    print(f"{data_string}\r\n")
                    self.__com.update_signal.emit(data_string)
                    try:
                        self.__com.send(part)
                    except BaseException:
                        if debug == True:
                            self.log.logger.error(
                                "串口被拔出或参数错误！请先检查好再重新打开串口！")
                        QMessageBox.critical(
                            self, "Port Error", "串口被拔出或参数错误！请先检查好再重新打开串口！")
                    timer = threading.Timer(1, self.timeout_callback, args=(part,))
                    timer.start()
                    # 等待 200ms 或者直到接收到响应
                    start_time = datetime.now()
                    while True:
                        # 计算已经过去的时间
                        elapsed_time = (datetime.now() - start_time).total_seconds()
                        # print(f"等待时间：{elapsed_time:.3f}秒")
                        # 如果收到响应，退出循环
                        if self.response_received == True:
                            print("收到异常指令响应，停止等待")
                            timer.cancel()
                            if should_send:
                                self.send_with_retries(self.current_command, max_retries=2, interval_ms=1.5)
                            self.response_received = False  # 重置状态
                            break
                        # 如果等待时间超过1秒，退出循环
                        if elapsed_time >= 1.5:
                            print("未收到响应，超时退出，发送一条正常指令")
                            if should_send:
                                self.send_with_retries(self.current_command, max_retries=2, interval_ms=1.5)
                            break
                    sleep(1.5)
                print("\n间隔 10ms 发送正常帧:")
                self.send_commands_with_intervals(self.current_command,10)
                sleep(1.5)
                print("\n间隔 50ms 发送正常帧:")
                self.send_commands_with_intervals(self.current_command, 50)
                sleep(1.5)
                print("\n间隔 100ms 发送正常帧:")
                self.send_commands_with_intervals(self.current_command, 100)
                self.eButtonSend.setEnabled(True)
                self.pushButtonSend.setChecked(True)
                self.singleButtonSend.setChecked(True)
                self.__except_commands = False
            elif self.comboBoxCommand.currentText() == '00000000-set-698':
                test_parts = self.utils.parse_except_00000000_698(self.current_command)
                for part, description, should_send in test_parts:
                    # 设置超时计时器，200ms超时
                    self.response_received = False
                    hex_string_no_prefix = ' '.join(f'{byte:02X}' for byte in part)
                    data_string = f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},<span style='color:red;'>{description}</span>，发送内容：<b>{hex_string_no_prefix}</b>"
                    print(f"{data_string}\r\n")
                    self.__com.update_signal.emit(data_string)
                    timer = threading.Timer(1, self.timeout_callback, args=(part,))
                    timer.start()
                    try:
                        self.__com.send(part)
                    except BaseException:
                        if debug == True:
                            self.log.logger.error(
                                "串口被拔出或参数错误！请先检查好再重新打开串口！")
                        QMessageBox.critical(
                            self, "Port Error", "串口被拔出或参数错误！请先检查好再重新打开串口！")

                    # 等待 200ms 或者直到接收到响应
                    start_time = datetime.now()
                    print(f"start_time时间：{start_time}秒")
                    while True:
                        # 计算已经过去的时间
                        elapsed_time = (datetime.now() - start_time).total_seconds()
                        # print(f"等待时间：{elapsed_time:.3f}秒")
                        # 如果收到响应，退出循环
                        if self.response_received == True:
                            print("收到异常指令响应，停止等待")
                            timer.cancel()
                            if should_send:
                                self.send_with_retries(self.current_command, max_retries=2, interval_ms=1.5)
                            self.response_received = False  # 重置状态
                            break
                        # 如果等待时间超过1秒，退出循环
                        if elapsed_time >= 1.5:
                            print("未收到响应，超时退出，发送一条正常指令")
                            if should_send:
                                self.send_with_retries(self.current_command, max_retries=2, interval_ms=1.5)
                            break
                    sleep(1.5)
                self.eButtonSend.setEnabled(True)
                self.pushButtonSend.setChecked(True)
                self.singleButtonSend.setChecked(True)
                self.__except_commands = False
            elif self.comboBoxCommand.currentText() == '00000000-set-645':
                test_parts = self.utils.parse_except_00000000_645(self.current_command)
                for part, description, should_send in test_parts:
                    # 设置超时计时器，200ms超时
                    self.response_received = False
                    hex_string_no_prefix = ' '.join(f'{byte:02X}' for byte in part)
                    data_string = f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},<span style='color:red;'>{description}</span>，发送内容：<b>{hex_string_no_prefix}</b>"
                    print(f"{data_string}\r\n")
                    self.__com.update_signal.emit(data_string)
                    timer = threading.Timer(1, self.timeout_callback, args=(part,))
                    timer.start()
                    try:
                        self.__com.send(part)
                    except BaseException:
                        if debug == True:
                            self.log.logger.error(
                                "串口被拔出或参数错误！请先检查好再重新打开串口！")
                        QMessageBox.critical(
                            self, "Port Error", "串口被拔出或参数错误！请先检查好再重新打开串口！")

                    # 等待 200ms 或者直到接收到响应
                    start_time = datetime.now()
                    while True:
                        # 计算已经过去的时间
                        elapsed_time = (datetime.now() - start_time).total_seconds()
                        # print(f"等待时间：{elapsed_time:.3f}秒")
                        # 如果收到响应，退出循环
                        if self.response_received == True:
                            print("收到异常指令响应，停止等待")
                            timer.cancel()
                            if should_send:
                                self.send_with_retries(self.current_command, max_retries=2, interval_ms=1.5)
                            self.response_received = False  # 重置状态
                            break
                        # 如果等待时间超过1秒，退出循环
                        if elapsed_time >= 1.5:
                            print("未收到响应，超时退出，发送一条正常指令")
                            if should_send:
                                self.send_with_retries(self.current_command, max_retries=2, interval_ms=1.5)
                            break
                    sleep(1)
                self.eButtonSend.setEnabled(True)
                self.pushButtonSend.setChecked(True)
                self.singleButtonSend.setChecked(True)
                self.__except_commands = False
            else:

                for part, description, should_send in test_parts:
                    # 设置超时计时器，200ms超时
                    self.response_received = False
                    hex_string_no_prefix = ' '.join(f'{byte:02X}' for byte in part)
                    data_string = f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},<span style='color:red;'>{description}</span>，发送内容：<b>{hex_string_no_prefix}</b>"
                    print(f"{data_string}\r\n")
                    self.__com.update_signal.emit(data_string)
                    try:
                        self.__com.send(part)
                    except BaseException:
                        if debug == True:
                            self.log.logger.error(
                                "串口被拔出或参数错误！请先检查好再重新打开串口！")
                        QMessageBox.critical(
                            self, "Port Error", "串口被拔出或参数错误！请先检查好再重新打开串口！")
                    timer = threading.Timer(1, self.timeout_callback, args=(part,))
                    timer.start()
                    # 等待 200ms 或者直到接收到响应
                    start_time = datetime.now()
                    while True:
                        # 计算已经过去的时间
                        elapsed_time = (datetime.now() - start_time).total_seconds()
                        # print(f"等待时间：{elapsed_time:.3f}秒")
                        # 如果收到响应，退出循环
                        if self.response_received == True:
                            print("收到异常指令响应，停止等待")
                            timer.cancel()
                            if should_send:
                                self.send_with_retries(self.current_command, max_retries=2, interval_ms=1.5)
                            self.response_received = False  # 重置状态
                            break
                        # 如果等待时间超过1秒，退出循环
                        if elapsed_time >= 1.5:
                            print("未收到响应，超时退出，发送一条正常指令")
                            if should_send:
                                self.send_with_retries(self.current_command, max_retries=2, interval_ms=1.5)
                            break
                    sleep(1)
                self.eButtonSend.setEnabled(True)
                self.pushButtonSend.setChecked(True)
                self.singleButtonSend.setChecked(True)
                self.__except_commands = False

    # 模拟连续发送正常帧，间隔时间可调整为10ms, 50ms, 100ms
    def send_commands_with_intervals(self, command, interval_ms):
        for i in range(3):  # 假设连续发送5次
            print(f"\n发送第 {i + 1} 条正常指令:间隔时间:{interval_ms}ms")
            hex_string_no_prefix = ' '.join(f'{byte:02X}' for byte in command)
            self.__com.update_signal.emit(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},间隔时间:{interval_ms}ms,发送第 {i + 1} 条正常指令: {hex_string_no_prefix}")

            # 发送命令，模拟等待接收响应
            self.send_command(command)
            # 根据 interval_ms 设置不同的间隔时间
            time.sleep(interval_ms / 1000.0)

    def send_with_retries(self, command, max_retries, interval_ms):
        retries = 0
        response_received_flag = False  # 用来标识是否收到响应
        while retries <= max_retries:

            hex_string_no_prefix = ' '.join(f'{byte:02X}' for byte in command)
            print(f"Sending command: {hex_string_no_prefix}")
            data_string = f"异常测试过程中，开始发送正常测试指令,{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}: <b>{hex_string_no_prefix}</b>"
            self.__com.update_signal.emit(data_string)
            # self.textBrowserReceive.insertHtml(f"开始发送测试指令: <b>{hex_string_no_prefix}</b>\r\n")
            # self.insert_text_with_separator()
            try:
                self.__com.send(command)
            except BaseException:
                if debug == True:
                    self.log.logger.error(
                        "串口被拔出或参数错误！请先检查好再重新打开串口！")
                QMessageBox.critical(
                    self, "Port Error", "串口被拔出或参数错误！请先检查好再重新打开串口！")
            # 发送正常指令
            # self.send_command(command)

            # 设置 200ms 超时计时器
            timer = threading.Timer(1, self.timeout_callback, args=(command,))
            timer.start()

            # 等待 200ms 或者直到接收到响应
            start_time = datetime.now()
            while True:
                # 计算已经过去的时间
                elapsed_time = (datetime.now() - start_time).total_seconds()
                # print(f"等待时间：{elapsed_time:.3f}秒")
                # 如果收到响应，退出循环
                if self.response_received:
                    print("收到正常指令响应，停止等待")
                    self.response_received = False  # 重置状态
                    timer.cancel()
                    print(f"正常指令指令响应成功: {command}\r\n")
                    response_received_flag = True  # 设置标志为 True
                    break
                # 如果等待时间超过1秒，退出循环
                if elapsed_time >= interval_ms:
                    print("未收到正常指令响应，超时退出")
                    break

                # 如果收到响应，跳出外层循环
            if response_received_flag:
                break
            # 如果超时，增加重试计数
            retries += 1
            print(f"异常测试过程中，重试第 {retries} 次发送正常指令-------------------")
            if retries <= max_retries:
                self.__com.update_signal.emit(f"异常测试过程中，当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},重试第 {retries} 次发送正常指令！！")
        # 超过重试次数后，处理失败逻辑
        if not response_received_flag:  # 仅在未成功接收到响应时处理失败逻辑
            sleep(interval_ms)
            print(f"指令发送失败，超出重试次数: {command}")
            self.__com.update_signal.emit(
                f"异常测试过程中，当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},正常指令发送响应失败，超出重试{max_retries}次: {hex_string_no_prefix}")
    @QtCore.pyqtSlot()
    def on_eButtonSend_clicked(self):

        if self.__com.getPortState() == True:
            if debug == True:
                self.log.logger.debug(
                    "开始进行自动化异常发送测试")
                # logging.debug("开始进行自动化异常发送测试")
                self.textBrowserReceive.insertPlainText(
                    f"\n\n---异常发送测试 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ---\n")
                self.textBrowserReceive.insertPlainText("\r\n")
                self.insert_text_with_separator()
            self.eButtonSend.setEnabled(False)
            # self.pushButtonSend.setChecked(False)
            # self.singleButtonSend.setChecked(False)
            self.send_count = 0
            self.command_queue = []
            print("mac_commands:", self.utils.mac_commands)
            threading.Thread(target=self.except_commands, args=(), daemon=True).start()


        else:
            if debug == True:
                self.log.logger.error(
                    "串口未打开！")
            QMessageBox.critical(self, "Port Error", "串口未打开，请先打开串口！")
            self.__pushButtonSend_State_Reset()
    @QtCore.pyqtSlot()
    def on_singleButtonSend_clicked(self):

        if self.__com.getPortState() == True:
            if debug == True:
                self.log.logger.debug(
                    "开始进行自动化单次发送测试")
                # logging.debug("开始进行自动化单次发送测试")
                self.textBrowserReceive.insertPlainText(
                    f"\n\n---单次发送测试 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ---\n")
                self.textBrowserReceive.insertPlainText("\r\n")
                self.insert_text_with_separator()
            self.__except_commands = False
            self.singleButtonSend.setEnabled(False)
            self.send_count = 0
            self.command_queue = []
            if self.comboBoxCommand.currentText() == '0000001C-read' and self.project_name == '泰瑞捷':
                self.current_command = self.utils.send_commands_trj0000001C(self.rssiData)
            elif '00000000' in self.comboBoxCommand.currentText() :
                self.current_command = self.__commands[self.comboBoxCommand.currentText()]
                length_bytes = self.current_command[5:7][::-1]
                length_s = length_bytes[0] * 256 + length_bytes[1]
                a_field_str = self.slaveMac.currentText()
                if a_field_str:
                    a_field = [int(a_field_str.replace(" ", "")[i:i + 2], 16) for i in
                                              range(0, len(a_field_str.replace(" ", "")), 2)][::-1]
                    self.current_command[12:18] = a_field
                print(f"on_singleButtonSend_clicked self.current_command，是 {self.current_command}")
                calculated_checksum = sum(self.current_command[4:23 + length_s]) % 256
                print(f"on_singleButtonSend_clicked calculated_checksum，是 {calculated_checksum}")
                self.current_command[23 + length_s] = calculated_checksum

            else:
                self.current_command = self.__commands[self.comboBoxCommand.currentText()]
            hex_string_no_prefix = ' '.join(f'{byte:02X}' for byte in self.current_command)
            data_string = f"单次发送 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}，内容：{hex_string_no_prefix}"
            print(f"{data_string}\r\n")
            self.textBrowserReceive.insertPlainText(data_string)
            self.textBrowserReceive.insertPlainText("\r\n")
            self.insert_text_with_separator()
            try:
                self.__com.send(self.current_command)
            except BaseException:
                if debug == True:
                    self.log.logger.error(
                        "串口被拔出或参数错误！请先检查好再重新打开串口！！")
                QMessageBox.critical(
                    self, "Port Error", "串口被拔出或参数错误！请先检查好再重新打开串口！")
            # self.__com.send(self.current_command)
            self.timeout_timer = threading.Timer(1.0, self.handle_timeout)
            self.timeout_timer.start()

        else:
            if debug == True:
                self.log.logger.error(
                    "串口未打开！")
                # logging.debug("串口未打开")
            QMessageBox.critical(self, "Port Error", "串口未打开，请先打开串口！")
            self.__pushButtonSend_State_Reset()
    @QtCore.pyqtSlot()
    def on_pushButtonSend_clicked(self):


        if self.__com.getPortState() == True:
            if debug == True:
                self.log.logger.debug(
                    "开始进行自动化测试！")
                # logging.debug("开始进行自动化测试")
                self.textBrowserReceive.insertPlainText(
                    f"\n\n---开始进行自动化测试 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ---\n")
                self.textBrowserReceive.insertPlainText("\r\n")
                self.insert_text_with_separator()
            self.pushButtonSend.setEnabled(False)

            self.send_count = 0
            self.command_queue = []
            self.add_commands_to_queue(self.command_list)
            self.__except_commands = False
            # 单次发送  端口已被打开时开始发送

            # if self.utils.check_and_load_ini():
            #
            # self.add_commands_to_queue(self.command_list)
            # else:
            #     commands = [
            #         self.utils.send_commands_00000008(),
            #         self.utils.send_commands_F20B000A(),
            #         self.utils.send_commands_get_F20B0000(),
            #         self.utils.send_commands_set_F20B0002(),
            #         self.utils.send_commands_get_F20B0002(),
            #         self.utils.send_commands_set_F20B0000(),
            #         # self.send_commands_set_F20B0003(),
            #         self.utils.send_commands_get_F20B0003()
            #
            #     ]

                # self.add_commands_to_queue(commands)

        else:
            if debug == True:
                self.log.logger.error("串口未打开!!!")
                # logging.debug("串口未打开")
            QMessageBox.critical(self, "Port Error", "串口未打开，请先打开串口！")
            self.__pushButtonSend_State_Reset()

    @QtCore.pyqtSlot()
    def on_pushButtonOTA_clicked(self):
        if self.__com.getPortState() == True:
            if debug == True:
                self.log.logger.debug(
                    "开始进行串口升级测试！")
                # logging.debug("开始进行串口升级测试")
                self.textBrowserReceive.insertPlainText(
                    f"\n\n---开始进行串口升级测试 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ---\n")
                self.textBrowserReceive.insertPlainText("\r\n")
                self.insert_text_with_separator()
            try:
                if len(self.localAppVersion) > 0:
                    if len(self.plan) < 1:
                        QMessageBox.critical(self, "OTA Error", "错误: 不需要更新！")
                        return
                    threading.Thread(target=self.doUpdate, args=(), daemon=True).start()

                else:
                    self.pushButtonOTA.setEnabled(True)
                    QMessageBox.critical(self, "OTA Error", "请先检查版本！")
                    return
            except Exception as e:
                print(f"OTA时出错: {str(e)}")
                self.pushButtonOTA.setEnabled(True)
                QMessageBox.critical(self, "OTA Error", "OTA时出错: 请先获取版本号！")

        else:
            self.pushButtonOTA.setEnabled(True)
            if debug == True:
                self.log.logger.error("串口未打开!!!")
                # logging.debug("串口未打开")
            QMessageBox.critical(self, "Port Error", "串口未打开，请先打开串口！")
    def doUpdate(self):
        self.pushButtonOTA.setEnabled(False)
        self.current_command = self.utils.send_commands_OTA_CTRL_START_0000002E()
        self.send_command(self.current_command)
        timer = threading.Timer(1, self.timeout_callback, args=(self.current_command,))
        timer.start()
        # 等待 200ms 或者直到接收到响应
        start_time = datetime.now()
        while True:
            # 计算已经过去的时间
            elapsed_time = (datetime.now() - start_time).total_seconds()
            # print(f"等待时间：{elapsed_time:.3f}秒")
            # 如果收到响应，退出循环
            if self.CheckDevStatus == 1:
                print("收到OTA_CTRL_START指令响应，停止等待", self.CheckDevStatus)
                timer.cancel()
                self.burnFiles()
                sleep(int(self.lineEdit_MTU.text()) / 1000)
                self.burnMetaData()
                self.CheckDevStatus = 0  # 重置状态
                break
            # 如果等待时间超过1秒，退出循环
            if elapsed_time >= 1.5:
                self.pushButtonOTA.setEnabled(True)
                print("未收到响应，超时退出!!!")
                break
    def burnMetaData(self):
        meta = self.build_meta_data()
        command = self.utils.send_commands_OTA_CTRL_METADATA_0000002E(list(meta))
        self.send_command(command)
        sleep(int(self.lineEdit_MTU.text()) / 1000)
        command = self.utils.send_commands_OTA_CTRL_REBOOT_0000002E()
        self.send_command(command)
        self.__com.label_progress_signal.emit('FOTA 烧录完成，重启设备...')
        # self.showProgress('FOTA 烧录完成，重启设备...')
        sleep(5)
        # self.showProgress('读取最新版本号...')
        # self.__com.label_progress_signal.emit('读取最新版本号...')
        self.send_command(self.utils.send_commands_get_version_0000002E())
        self.pushButtonOTA.setEnabled(True)

    def showProgress(self, message):
        # QCoreApplication.processEvents()
        self.label_progress.setText(message)
        self.label_progress.show()
    def emitProgress(self, size):
        # QCoreApplication.processEvents()
        sum_length = sum(len(item["data"]) for item in self.plan)
        print("sum_length--------:", sum_length)
        self.progressBar_ota.setValue(size * 100 / sum_length)
    def burnFiles(self):
        # self.showProgress('开始串口烧录...')
        self.__com.label_progress_signal.emit('开始串口烧录...')
        written = 0
        acc_size = 0
        page_size = self.flashInfo["page_size"]
        ble_mtu = 200
        for item in self.plan:
            offset = 0
            errors = 0

            while offset < len(item["data"]):
                block = min(page_size, len(item["data"]) - offset)
                page = item["data"][offset:offset + block]
                self.__com.label_progress_signal.emit(f'正在烧录 {item["name"]} (重试 #{errors})' if errors > 0 else f'正在烧录 {item["name"]}')
                # self.showProgress(f'正在烧录 {item["name"]} (重试 #{errors})' if errors > 0 else f'正在烧录 {item["name"]}')
                # print("page--------:", page)
                if self.burnPage(acc_size + offset, item["write_addr"] + offset, page) == 1:
                    offset += block
                    written += block
                    errors = 0
                    self.CheckDevStatus = 0
                else:
                    errors += 1
                    if errors > 5:
                        if written == 0 and ble_mtu > 20:
                            print("回退到 MTU 最小值(23)")
                            self.__com.label_progress_signal.emit('回退到 MTU 最小值(23)')
                            # self.showProgress("回退到 MTU 最小值(23)")
                            ble_mtu = 20
                            errors = 0
                            sleep(0.1)
                            continue
                        return False
                    else:
                        print("出现错误，重试...")
                        self.__com.label_progress_signal.emit('出现错误，重试...')
                        # self.showProgress("出现错误，重试...")
                        self.pushButtonOTA.setEnabled(True)

            acc_size += len(item["data"])
        return True

    def burnPage(self, acc_size, addr, page):
        ble_mtu = 200
        current = 0
        sig = None

        packed_data = struct.pack("<I", addr)
        print("Packed Data:", packed_data)
        print("list(packed_data):", list(packed_data))
        command = self.utils.send_commands_OTA_CTRL_PAGE_BEGIN_0000002E(list(packed_data))
        self.send_command(command)
        sleep(int(self.lineEdit_MTU.text())/1000)
        while current < len(page):
            size = min(ble_mtu, len(page) - current)
            print("page[current:current + size]--------:", list(page[current:current + size]))
            command = self.utils.send_commands_OTA_WriteData_0000002E(size,list(page[current:current + size]))
            self.send_command(command)

            current += size
            print("acc_size + current--------:", acc_size + current)
            self.__com.progress_signal.emit(acc_size + current)
            # self.emitProgress(acc_size + current)
            sleep(int(self.lineEdit_MTU.text())/1000)

        crc = self.crc16(list(page), 0, len(page))
        print("crc:", crc)
        command = self.utils.send_commands_OTA_CTRL_PAGE_END_0000002E(len(page), crc)
        self.send_command(command)
        sleep(int(self.lineEdit_MTU.text())/1000)
        return self.CheckDevStatus

    def build_meta_data(self):
        # 计算缓冲区大小
        buffer_size = 2 + 4 + len(self.plan) * 3 * 4
        buffer = bytearray(buffer_size)
        c = 2  # 初始位置
        struct.pack_into('<I', buffer, c, self.update_plan_builder.data['manifest']['entry'])
        c += 4
        for item in self.plan:
            print("item-----------:", item)
            # 写入 item.write_addr (4字节)
            struct.pack_into('<I', buffer, c, item['write_addr'])
            c += 4

            # 写入 item.addr (4字节)
            struct.pack_into('<I', buffer, c, item['address'])
            c += 4

            # 写入 item.data.length (4字节)
            struct.pack_into('<I', buffer, c, len(item['data']))
            c += 4

            # 打印日志
            print(" =======>>>>>> item.write_addr=", hex(item['write_addr']))
            print(" =======>>>>>> item.addr=", hex(item['address']))
            print(" =======>>>>>> item.data.length=", hex(len(item['data'])))
        # 将 bytearray 转换为 Hex 格式并打印
        u8data = buffer
        print(" u8data=======", binascii.hexlify(u8data).decode())
        # 计算 CRC16 (从索引 2 开始到倒数第2个字节)
        crc = self.crc16(u8data, 2, len(u8data)-2)
        struct.pack_into('<H', u8data, 0, crc)
        print(" u8data 2=======", binascii.hexlify(u8data).decode())
        return u8data
    def crc16(self, data, start, length):
        hex_data = ' '.join([f"{byte:02X}" for byte in data[start:start + length]])
        print("Data in Hex: =====", hex_data)
        auchCRCHi = [
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40
        ]

        auchCRCLo = [
            0x00, 0xC0, 0xC1, 0x01, 0xC3, 0x03, 0x02, 0xC2, 0xC6, 0x06, 0x07, 0xC7, 0x05, 0xC5, 0xC4, 0x04,
            0xCC, 0x0C, 0x0D, 0xCD, 0x0F, 0xCF, 0xCE, 0x0E, 0x0A, 0xCA, 0xCB, 0x0B, 0xC9, 0x09, 0x08, 0xC8,
            0xD8, 0x18, 0x19, 0xD9, 0x1B, 0xDB, 0xDA, 0x1A, 0x1E, 0xDE, 0xDF, 0x1F, 0xDD, 0x1D, 0x1C, 0xDC,
            0x14, 0xD4, 0xD5, 0x15, 0xD7, 0x17, 0x16, 0xD6, 0xD2, 0x12, 0x13, 0xD3, 0x11, 0xD1, 0xD0, 0x10,
            0xF0, 0x30, 0x31, 0xF1, 0x33, 0xF3, 0xF2, 0x32, 0x36, 0xF6, 0xF7, 0x37, 0xF5, 0x35, 0x34, 0xF4,
            0x3C, 0xFC, 0xFD, 0x3D, 0xFF, 0x3F, 0x3E, 0xFE, 0xFA, 0x3A, 0x3B, 0xFB, 0x39, 0xF9, 0xF8, 0x38,
            0x28, 0xE8, 0xE9, 0x29, 0xEB, 0x2B, 0x2A, 0xEA, 0xEE, 0x2E, 0x2F, 0xEF, 0x2D, 0xED, 0xEC, 0x2C,
            0xE4, 0x24, 0x25, 0xE5, 0x27, 0xE7, 0xE6, 0x26, 0x22, 0xE2, 0xE3, 0x23, 0xE1, 0x21, 0x20, 0xE0,
            0xA0, 0x60, 0x61, 0xA1, 0x63, 0xA3, 0xA2, 0x62, 0x66, 0xA6, 0xA7, 0x67, 0xA5, 0x65, 0x64, 0xA4,
            0x6C, 0xAC, 0xAD, 0x6D, 0xAF, 0x6F, 0x6E, 0xAE, 0xAA, 0x6A, 0x6B, 0xAB, 0x69, 0xA9, 0xA8, 0x68,
            0x78, 0xB8, 0xB9, 0x79, 0xBB, 0x7B, 0x7A, 0xBA, 0xBE, 0x7E, 0x7F, 0xBF, 0x7D, 0xBD, 0xBC, 0x7C,
            0xB4, 0x74, 0x75, 0xB5, 0x77, 0xB7, 0xB6, 0x76, 0x72, 0xB2, 0xB3, 0x73, 0xB1, 0x71, 0x70, 0xB0,
            0x50, 0x90, 0x91, 0x51, 0x93, 0x53, 0x52, 0x92, 0x96, 0x56, 0x57, 0x97, 0x55, 0x95, 0x94, 0x54,
            0x9C, 0x5C, 0x5D, 0x9D, 0x5F, 0x9F, 0x9E, 0x5E, 0x5A, 0x9A, 0x9B, 0x5B, 0x99, 0x59, 0x58, 0x98,
            0x88, 0x48, 0x49, 0x89, 0x4B, 0x8B, 0x8A, 0x4A, 0x4E, 0x8E, 0x8F, 0x4F, 0x8D, 0x4D, 0x4C, 0x8C,
            0x44, 0x84, 0x85, 0x45, 0x87, 0x47, 0x46, 0x86, 0x82, 0x42, 0x43, 0x83, 0x41, 0x81, 0x80, 0x40
        ]

        crc_hi = 0xFF
        crc_lo = 0xFF
        hex_string = []
        data_string = []
        for i in range(length):
            x = self.byte_as_u8(data[start + i]) & 0xff
            data_string.append(f"{x:02X}")
            uIndex = (crc_hi ^ x) & 0xff
            # hex_string.append(f"{uIndex:02X}")
            crc_hi = (crc_lo ^ auchCRCHi[uIndex])
            # print(f"crc_lo (before): {crc_lo}")
            crc_lo = auchCRCLo[uIndex]
            # print(f"Value at index {uIndex}: {auchCRCLo[uIndex]}")
            # 打印每步计算的 hi、lo 和 uIndex 值
            # print(f"Step {i + 1}: x = {x:02X}, uIndex = {uIndex:02X},auchCRCHi[uIndex] = {auchCRCHi[uIndex]:02X}, hi = {crc_hi:02X}, lo = {crc_lo:02X}")
            # if i==60:
            #     break
        # hex_data1 = " ".join(data_string)
        # print("hex_data1 in Hex: =====", hex_data1)
        # hex_data = " ".join(hex_string)
        # # Split the hex data into chunks for logging
        # for j in range(0, len(hex_data), 3000):
        #     print(f"Hex Data Part: {hex_data[j:j + 3000]}")
        crc = (crc_hi << 8) | crc_lo
        print("Final CRC Result in Hex: =====", hex(crc))
        return crc


    def byte_as_u8(self, v):
        return v if v >= 0 else 256 + v
    @QtCore.pyqtSlot()
    def on_pushButtonStop_clicked(self):
        self.__txPeriodEnable = False

    def format_hex_list(self, list):
        return ' '.join([f"0x{item:02X}" for item in list])
    def __pushButtonSend_State_Reset(self):
        self.pushButtonSend.setEnabled(True)
        self.comboBoxCommand.setEnabled(True)
        self.lineEditPeriodMs.setEnabled(True)
        self.singleButtonSend.setEnabled(True)
        self.eButtonSend.setEnabled(True)

        # 用于更新 UI 标签的槽函数

    def update_label(self, command):
        if debug == True:
            self.log.logger.debug(
                f"{command}")
        self.textBrowserReceive.insertHtml(f"{command}")
        self.textBrowserReceive.insertHtml("<br>")
        self.insert_text_with_separator()
    def periodSendThread(self):

        if debug == True:
            self.log.logger.debug(
                "周期发送线程开启！")
            # logging.debug("周期发送线程开启")
        if self.__txPeriodEnable == True and self.__com.getPortState() == True:
            try:
                self.send_count += 1  # 每发送一次命令，计数加1
                self.current_command = self.__commands[self.comboBoxCommand.currentText()]
                hex_string_no_prefix =' '.join(f'{byte:02X}' for byte in self.current_command)
                data_string = f"第{self.send_count}次发送,当前时间:{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}，内容：{hex_string_no_prefix}"
                print(f"Sending command: {data_string}\r\n")
                self.textBrowserReceive.insertPlainText(f"定时发送测试指令: {data_string}\r\n")
                self.insert_text_with_separator()

                # if self.__txPeriod > 0:
                #     print(f"定时: {self.__txPeriod/ 1000}")
                #     sleep(self.__txPeriod / 1000)
                # start = time.time()
                # print("睡眠时间:{}".format(start - stop))
                self.__com.send(self.current_command)
                # 开始2秒超时检测
                self.timeout_timer = threading.Timer(2.0, self.handle_timeout)
                self.timeout_timer.start()
                # stop =time.time()
                # print("发送时间:{}".format(stop-start))
                # self.__sndTotal += len(self.__periodSendBuf)
                if debug == True:
                    self.log.logger.debug(
                        "周期发送:{}".format(self.current_command))
                    # logging.debug("周期发送:{}".format(self.current_command))


            except Exception as e:
                QMessageBox.critical(
                    self, "Port Error", "串口被拔出或参数错误！请先检查好再重新打开串口！")
                if debug == True:
                    self.log.logger.error(
                        f"发送第 {self.send_count} 次指令时出错: {str(e)}")
                    print(f"发送第 {self.send_count} 次指令时出错: {str(e)}")
        else:
            self.checkBoxTxPeriodEnable.setChecked(False)
            self.timer_send.stop()
            if debug == True:
                self.log.logger.error(
                    f"串口未打开")
                # logging.debug("串口未打开")
            QMessageBox.critical(self, "Port Error", "串口未打开，请先打开串口！")


#     # 清除记录按钮
#     self.pushButtonClear
    @QtCore.pyqtSlot()
    def on_pushButtonClear_pressed(self):
        self.textBrowserReceive.clear()
        if debug == True:
            self.log.logger.debug(
                f"清除接收区以及发送区")
            # logging.debug("清除接收区以及发送区")




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.resize(300, 800)
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.setWindowTitle("串口自动化测试工具")
        self.setWindowIcon(QIcon(':/icon.ico'))
        # 主窗口布局
        self.main_layout = QHBoxLayout()


        # 右侧布局使用 QSplitter 来支持多窗口展示
        self.splitter = QSplitter()

        # 默认添加第一个子界面
        self.subwindow_count = 0

        self.add_new_subwindow()

        # 将 splitter 添加到主布局
        self.main_layout.addWidget(self.splitter)

        # 设置主布局到 central_widget
        central_widget.setLayout(self.main_layout)

        # 初始化菜单栏
        self.initMenuBar()

    def initMenuBar(self):
        # 创建菜单栏
        menubar = self.menuBar()

        # 创建一个菜单
        view_menu = menubar.addMenu('多窗口')

        # 创建菜单项
        add_subwindow_action = QAction('新增一个界面', self)

        add_subwindow_action.triggered.connect(self.add_new_subwindow)  # 绑定点击事件

        # 将菜单项添加到菜单
        view_menu.addAction(add_subwindow_action)

    def add_new_subwindow(self):
        print(f"self.subwindow_count: {self.subwindow_count}\r\n")
        # 确定当前子界面应读取的部分
        mac_section = f'MAC_{self.subwindow_count}' if self.subwindow_count > 0 else 'MAC'
        # 创建一个新的子界面
        new_subwindow = userMain(mac_section)

        # 将子界面添加到 splitter 中
        self.splitter.addWidget(new_subwindow)
        # 每次添加新子界面后，调整主窗口的大小
        current_width = self.width()  # 获取当前窗口宽度
        new_width = current_width + 800  # 增加宽度（例如，增加800）
        self.resize(new_width, self.height())  # 调整窗口大小
        # 更新子界面数量
        self.subwindow_count += 1
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 设置窗口风格
    app.setStyle("Fusion")  # 选项包括: "Fusion", "Windows", "WindowsVista", 等
    win = MainWindow()
    win.show()
    app.exec_()

# pyinstaller --onefile --icon=icon.ico --name autoTest2.0 -w main.py