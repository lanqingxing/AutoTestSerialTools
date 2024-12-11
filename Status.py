class Status:
    # 定义状态和对应的值
    SUCCESS = 0
    UNDEFINED_COMMAND = 1
    DEVICE_NOT_FOUND = 2
    CONNECTION_FAILED = 3
    BLUETOOTH_TRANSMISSION_FAILED = 4
    EXCEEDS_LINK_LIMIT = 5
    PARAMETER_ERROR = 6
    NO_PAIRING_INFO = 16
    MEMORY_ALLOCATION_FAILED = 17
    STRUCTURE_CHANGED = 18
    ILLEGAL_OPERATION_WHILE_BT_AUTH_CLOSED = 252
    ILLEGAL_OPERATION_DURING_CHECK = 253
    EXECUTION_FAILED = 254
    OTHER_ERROR = 255

    # 状态码与名称的映射
    _status_map = {
        SUCCESS: "成功状态",
        UNDEFINED_COMMAND: "控制命令未定义",
        DEVICE_NOT_FOUND: "设备地址不存在",
        CONNECTION_FAILED: "目标设备连接失败",
        BLUETOOTH_TRANSMISSION_FAILED: "蓝牙链路透传失败",
        EXCEEDS_LINK_LIMIT: "蓝牙链路数超过设置值",
        PARAMETER_ERROR: "数据报文参数错误",
        NO_PAIRING_INFO: "无设备配对信息",
        MEMORY_ALLOCATION_FAILED: "申请内存失败",
        STRUCTURE_CHANGED: "广播结构已变化",
        ILLEGAL_OPERATION_WHILE_BT_AUTH_CLOSED: "蓝牙授权关闭中非法操作蓝牙",
        ILLEGAL_OPERATION_DURING_CHECK: "检表过程中非法操作蓝牙",
        EXECUTION_FAILED: "执行失败",
        OTHER_ERROR: "其它错误",
    }

    @classmethod
    def get_status_name(cls, code):
        """
        根据状态码获取状态名称。
        :param code: 状态码
        :return: 状态名称字符串
        """
        return cls._status_map.get(code, "未定义状态")

    @classmethod
    def is_valid_status(cls, code):
        """
        检查状态码是否有效。
        :param code: 状态码
        :return: 是否有效
        """
        return code in cls._status_map

