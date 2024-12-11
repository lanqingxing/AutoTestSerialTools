import threading

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot


class SerialWorker(QThread):
    serial_connection_made = pyqtSignal()
    serial_connection_lost = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, com, comBoxPortBuf):
        super().__init__()
        self.__com = com
        self.__comBoxPortBuf = comBoxPortBuf
        self.port_opened = False
        self.lock = threading.Lock()  # 添加互斥锁

    def run(self):
        with self.lock:  # 确保只有一个串口操作在执行
            if self.port_opened:
                self.close_serial_port()
            else:
                self.open_serial_port()

    def open_serial_port(self):
        try:
            portBuf = self.__comBoxPortBuf
            print(f"portBuf: {portBuf}")
            if portBuf != "":
                # 尝试打开串口
                self.__com.open(portBuf)
                self.port_opened = True
                self.serial_connection_made.emit()
        except Exception as e:
            print(f"端口打开出错: {e}")
            self.error_occurred.emit(f"端口打开出错: {e}")

    def close_serial_port(self):
        try:
            # 关闭串口
            self.__com.close()
            self.port_opened = False
            self.serial_connection_lost.emit()
        except Exception as e:
            self.error_occurred.emit(f"端口关闭出错: {e}")
