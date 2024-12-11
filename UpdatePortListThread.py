from PyQt5.QtCore import QThread, pyqtSignal
import time

from userSerial import userSerial


class UpdatePortListThread(QThread):
    # 定义一个信号，用来通知主线程更新 comboBox
    update_ports_signal = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        start = time.time()

        # 获取可用串口号列表
        newportlistbuf = userSerial.getPortsList()  # 假设这是获取串口的函数

        stop = time.time()

        # if debug:
        #     logging.debug("更新串口列表时间{}s".format(stop - start))

        # 通过信号将串口列表传递到主线程
        self.update_ports_signal.emit(newportlistbuf)
