import configparser
import logging
import os
import struct

from PyQt5.QtWidgets import QMessageBox

mac_section_project = {}  # 存储所有子界面下拉框对象

class CommandUtils:
    def __init__(self, mac_section, project_name):
        self.fcstab = [
            0x0000, 0x1189, 0x2312, 0x329b, 0x4624, 0x57ad, 0x6536, 0x74bf,
            0x8c48, 0x9dc1, 0xaf5a, 0xbed3, 0xca6c, 0xdbe5, 0xe97e, 0xf8f7,
            0x1081, 0x0108, 0x3393, 0x221a, 0x56a5, 0x472c, 0x75b7, 0x643e,
            0x9cc9, 0x8d40, 0xbfdb, 0xae52, 0xdaed, 0xcb64, 0xf9ff, 0xe876,
            0x2102, 0x308b, 0x0210, 0x1399, 0x6726, 0x76af, 0x4434, 0x55bd,
            0xad4a, 0xbcc3, 0x8e58, 0x9fd1, 0xeb6e, 0xfae7, 0xc87c, 0xd9f5,
            0x3183, 0x200a, 0x1291, 0x0318, 0x77a7, 0x662e, 0x54b5, 0x453c,
            0xbdcb, 0xac42, 0x9ed9, 0x8f50, 0xfbef, 0xea66, 0xd8fd, 0xc974,
            0x4204, 0x538d, 0x6116, 0x709f, 0x0420, 0x15a9, 0x2732, 0x36bb,
            0xce4c, 0xdfc5, 0xed5e, 0xfcd7, 0x8868, 0x99e1, 0xab7a, 0xbaf3,
            0x5285, 0x430c, 0x7197, 0x601e, 0x14a1, 0x0528, 0x37b3, 0x263a,
            0xdecd, 0xcf44, 0xfddf, 0xec56, 0x98e9, 0x8960, 0xbbfb, 0xaa72,
            0x6306, 0x728f, 0x4014, 0x519d, 0x2522, 0x34ab, 0x0630, 0x17b9,
            0xef4e, 0xfec7, 0xcc5c, 0xddd5, 0xa96a, 0xb8e3, 0x8a78, 0x9bf1,
            0x7387, 0x620e, 0x5095, 0x411c, 0x35a3, 0x242a, 0x16b1, 0x0738,
            0xffcf, 0xee46, 0xdcdd, 0xcd54, 0xb9eb, 0xa862, 0x9af9, 0x8b70,
            0x8408, 0x9581, 0xa71a, 0xb693, 0xc22c, 0xd3a5, 0xe13e, 0xf0b7,
            0x0840, 0x19c9, 0x2b52, 0x3adb, 0x4e64, 0x5fed, 0x6d76, 0x7cff,
            0x9489, 0x8500, 0xb79b, 0xa612, 0xd2ad, 0xc324, 0xf1bf, 0xe036,
            0x18c1, 0x0948, 0x3bd3, 0x2a5a, 0x5ee5, 0x4f6c, 0x7df7, 0x6c7e,
            0xa50a, 0xb483, 0x8618, 0x9791, 0xe32e, 0xf2a7, 0xc03c, 0xd1b5,
            0x2942, 0x38cb, 0x0a50, 0x1bd9, 0x6f66, 0x7eef, 0x4c74, 0x5dfd,
            0xb58b, 0xa402, 0x9699, 0x8710, 0xf3af, 0xe226, 0xd0bd, 0xc134,
            0x39c3, 0x284a, 0x1ad1, 0x0b58, 0x7fe7, 0x6e6e, 0x5cf5, 0x4d7c,
            0xc60c, 0xd785, 0xe51e, 0xf497, 0x8028, 0x91a1, 0xa33a, 0xb2b3,
            0x4a44, 0x5bcd, 0x6956, 0x78df, 0x0c60, 0x1de9, 0x2f72, 0x3efb,
            0xd68d, 0xc704, 0xf59f, 0xe416, 0x90a9, 0x8120, 0xb3bb, 0xa232,
            0x5ac5, 0x4b4c, 0x79d7, 0x685e, 0x1ce1, 0x0d68, 0x3ff3, 0x2e7a,
            0xe70e, 0xf687, 0xc41c, 0xd595, 0xa12a, 0xb0a3, 0x8238, 0x93b1,
            0x6b46, 0x7acf, 0x4854, 0x59dd, 0x2d62, 0x3ceb, 0x0e70, 0x1ff9,
            0xf78f, 0xe606, 0xd49d, 0xc514, 0xb1ab, 0xa022, 0x92b9, 0x8330,
            0x7bc7, 0x6a4e, 0x58d5, 0x495c, 0x3de3, 0x2c6a, 0x1ef1, 0x0f78
        ]
        self.ini_file = f"{project_name}.ini"
        self.project_name = project_name
        self.PPPINITFCS16 = 0xffff  # Initial FCS value
        self.PPPGOODFCS16 = 0xf0b8
        self.config = configparser.ConfigParser()
        self.mac_commands = []
        mac_section_project[mac_section] = self.project_name
        self.mac_section = mac_section
        if self.check_and_load_ini(self.ini_file):
            # 使用 open 指定编码为 UTF-8 读取 ini 文件
            with open(self.ini_file, 'r', encoding='utf-8') as f:
                self.config.read_file(f)
            self.mac_info = self.parse_mac_info()  # 初始化时解析 MAC 信息

        else:
            self.write_ini_file()
            with open(self.ini_file, 'r', encoding='utf-8') as f:
                self.config.read_file(f)
            self.mac_info = self.parse_mac_info()  # 初始化时解析 MAC 信息

    def write_ini_file(self):
        if self.project_name == "威胜":
            # 定义要写入的内容
            ini_content = """
# 这是 MAC 地址和 PIN 码配置
[MAC]
# 本机 MAC 地址 （全 0 或全 FF 为无效的蓝牙 MAC 地址）
masterMac = C10000000009
# 主机1 MAC 地址 （全 0 或全 FF 为无效的蓝牙 MAC 地址）
masterMac_1 = FFFFFFFFFFFF
# 从机 1MAC 地址（全 0 或 FFFFFFFFFFF1 为无效从机 MAC[1]， 若为全 FF 则为自动配对模式）
slaveMac = C30000001112
# 从机 2MAC 地址（全 0 ，全 FF 或 FFFFFFFFFFF1 为无效从机 MAC
slaveMac_2 = C30000000002
# 从机 3MAC 地址（全 0 ，全 FF 或 FFFFFFFFFFF1 为无效从机 MAC）
slaveMac_3 = C30000000003
# 主通道配对 PIN 码加密后的密文（明 文模式）
masterPin_pw = 313233343536FFFFFFFFFFFFFFFFFFFF
 # 主通道配对码（配对 PIN 码固定为 6 字节 ASCII 字符，若不启 用 PIN 则配置为 6 字节全 FF）
masterPin = 313233343536
 # 从通道配对码（配对 PIN 码固定为 6 字节 ASCII 字符，若不启用 PIN 则配置为 6 字节全 FF）。
slavePin = 313233343536313233343536313233343536

[MAC_1]
# 本机 MAC 地址 （全 0 或全 FF 为无效的蓝牙 MAC 地址）
masterMac = C30000000091
# 主机1 MAC 地址 （全 0 或全 FF 为无效的蓝牙 MAC 地址）
masterMac_1 = FFFFFFFFFFFF
# 从机 1MAC 地址（全 0 或 FFFFFFFFFFF1 为无效从机 MAC[1]， 若为全 FF 则为自动配对模式）
slaveMac = C10000000009
# 从机 2MAC 地址（全 0 ，全 FF 或 FFFFFFFFFFF1 为无效从机 MAC
slaveMac_2 = C30000000002
# 从机 3MAC 地址（全 0 ，全 FF 或 FFFFFFFFFFF1 为无效从机 MAC）
slaveMac_3 = C30000000003
# 主通道配对 PIN 码加密后的密文（明 文模式）
masterPin_pw = 313233343536FFFFFFFFFFFFFFFFFFFF
 # 主通道配对码（配对 PIN 码固定为 6 字节 ASCII 字符，若不启 用 PIN 则配置为 6 字节全 FF）
masterPin = 313233343536
 # 从通道配对码（配对 PIN 码固定为 6 字节 ASCII 字符，若不启用 PIN 则配置为 6 字节全 FF）。
slavePin = 313233343536313233343536313233343536

#注意：指令中只要带有data_field并且不为空的情况，那么其他字段参数无效
# 这是命令部分,type报文类型,占用一个字节(01H：透传；02H：配置 SET 蓝牙模块参数；03H：获取 GET 蓝牙模块参数；04H：蓝牙主动上报/通知事件。),
#length数据域的字节数，占用两个字节,a_field传输设备地址,占用六个字节,r_field预留， 占用四个字节,data_field数据域
[00000008-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

[F20B000A-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

[F20B0000-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

#power_level发射功率档位[1] ， 0 档位代表 4dBm；
#broadcast_interval广播间隔 40ms，低字节在前，高字节在后，单位为毫秒，允许设定范围： 40~ 1000ms ，默认 40ms；
#scan_interval扫描间隔 160ms ，低字节在前，高字节在后，单位为毫秒，允许设定范 围：55~ 110ms ，默认 100ms
[F20B0002-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
power_level = 00
broadcast_interval = 2800
scan_interval  = A000

[F20B0002-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

;[F20B0008-set]
;type = 02
;length = 3600
;a_field = FFFFFFFFFFFF
;r_field = 00000000
;# 主通道 1 配对 PIN 码长度，6 字节（若长度为 0，则配对 PIN 码字段为空[1] )
;masterPin_1_length = 06
;#323232323232——主通道 1 配对 PIN 码“222222 ”
;masterPin_1_pin = 323232323232
;# 主通道 1 配对 PIN 码加密密文长度，16 字节
;masterPin_1_encrypted_pin_length = 10
;# 主通道 1 配对 PIN 码密文广播数据
;masterPin_1_encrypted_pin = 000102030405060708090A0B0C0D0E0F
;
;# 主通道 2 配对 PIN 码长度，6 字节（若长度为 0，则配对 PIN 码字段为空[1] )
;masterPin_2_length = 06
;#主通道 2 配对 PIN 码“222222 ”
;masterPin_2_pin = 323232323232
;# 主通道 2 配对 PIN 码加密密文长度，16 字节
;masterPin_2_encrypted_pin_length = 10
;# 主通道 2 配对 PIN 码密文广播数据
;masterPin_2_encrypted_pin = 000102030405060708090A0B0C0D0E0F
;
;[F20B0008-read]
;type = 03
;length = 0000
;a_field = FFFFFFFFFFFF
;r_field = 00000000
;data_field =
;
;[F20B0009-set]
;type = 02
;length = 2700
;a_field = FFFFFFFFFFFF
;r_field = 00000000
;# 从机 1 配对 PIN 码长度，6 字节（若为 0 时，配对 PIN 码数据字段为空[1]）
;slave_1_length = 06
;#从机 1 配对 PIN 码，“ 111111 ”
;slave_1_pin = 313131313131
;# 从机 2 配对 PIN 码长度，6 字节（若为 0 时，配对 PIN 码数据字段为空）
;slave_2_length = 06
;#从机 2 配对 PIN 码
;slave_2_pin = 323232323232
;# 从机 3 配对 PIN 码长度，6 字节（若为 0 时，配对 PIN 码数据字段为空）
;slave_3_length = 06
;#从机 3 配对 PIN 码
;slave_3_pin = 313131313131

;[F20B0009-read]
;type = 03
;length = 0000
;a_field = FFFFFFFFFFFF
;r_field = 00000000
;data_field =

[F20B0000-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
# 厂商 ID（2 字节，盲样送检缺省为 FFFF ，批量生产时配置为各厂商在电 网系统中的公司代码）
manufacturer_id = FFFF
# 设备类型，根据电表技术规范要求配置
device_type = C1
# 特征校验码[2] ，在断路器应用中采用它作为校验作用。在电表应用中，配 置为缺省 FFFF 则代表电能表不启用链路 PIN 加密，广播 16 字节为全 FF。为 0000 时，代表广播 16 字节中包含明文 PIN 。为 0001 时，代表广播 16 字节为加密后的密文313233343536FFFFFFFFFFFFFFFFFFFF ——主通道配对 PIN 码加密后的密文（明 文模式），用于广播中，方便链接主机进行扫描和链接
feature_code = 0000

[F20B0003-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =


[00000000-set-698]
type = 01
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =FEFEFEFE685A00C305436509112120A1B97B820058585858585858583138303330355858585831383033303500000000000000000000FFFFFFFFFFFFFFF0FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000C800130100C80000070800000000762916

[00000000-set-645]
type = 01
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =FEFEFEFE6801000000000068110433333333B216
 """
        elif self.project_name == "泰瑞捷":
            # 定义要写入的内容
            ini_content = """
# 这是 MAC 地址和 PIN 码配置
[MAC]
# 本机 MAC 地址 （全 0 或全 FF 为无效的蓝牙 MAC 地址）
masterMac = C10000000019
# 主机1 MAC 地址 （全 0 或全 FF 为无效的蓝牙 MAC 地址）
masterMac_1 = FFFFFFFFFFFF
# 从机 1MAC 地址（全 0 或 FFFFFFFFFFF1 为无效从机 MAC[1]， 若为全 FF 则为自动配对模式）
slaveMac = C30000000091
# 从机 2MAC 地址（全 0 ，全 FF 或 FFFFFFFFFFF1 为无效从机 MAC
slaveMac_2 = FFFFFFFFFFFF
# 从机 3MAC 地址（全 0 ，全 FF 或 FFFFFFFFFFF1 为无效从机 MAC）
slaveMac_3 = FFFFFFFFFFFF
# 主通道配对 PIN 码加密后的密文（明 文模式）
masterPin_pw = 313233343536FFFFFFFFFFFFFFFFFFFF
 # 主通道配对码（配对 PIN 码固定为 6 字节 ASCII 字符，若不启 用 PIN 则配置为 6 字节全 FF）
masterPin = 313233343536
 # 从通道配对码（配对 PIN 码固定为 6 字节 ASCII 字符，若不启用 PIN 则配置为 6 字节全 FF）。
slavePin = 313233343536313233343536313233343536

[MAC_1]
# 本机 MAC 地址 （全 0 或全 FF 为无效的蓝牙 MAC 地址）
masterMac = C30000000091
# 主机1 MAC 地址 （全 0 或全 FF 为无效的蓝牙 MAC 地址）
masterMac_1 = FFFFFFFFFFFF
# 从机 1MAC 地址（全 0 或 FFFFFFFFFFF1 为无效从机 MAC[1]， 若为全 FF 则为自动配对模式）
slaveMac = C10000000009
# 从机 2MAC 地址（全 0 ，全 FF 或 FFFFFFFFFFF1 为无效从机 MAC
slaveMac_2 = C30000000002
# 从机 3MAC 地址（全 0 ，全 FF 或 FFFFFFFFFFF1 为无效从机 MAC）
slaveMac_3 = C30000000003
# 主通道配对 PIN 码加密后的密文（明 文模式）
masterPin_pw = 313233343536FFFFFFFFFFFFFFFFFFFF
 # 主通道配对码（配对 PIN 码固定为 6 字节 ASCII 字符，若不启 用 PIN 则配置为 6 字节全 FF）
masterPin = 313233343536
 # 从通道配对码（配对 PIN 码固定为 6 字节 ASCII 字符，若不启用 PIN 则配置为 6 字节全 FF）。
slavePin = 313233343536313233343536313233343536

#注意：指令中只要带有data_field并且不为空的情况，那么其他字段参数无效
[F20B0000-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
# 本机蓝牙配对方式,0x01(Just Work),0x02(Passkey Entry),0x00(预留，暂不支持),0x03(OOB,预留，暂不支持)，可以根据需求注释或者值置空，代表不配置该主机
master_dev_pair_mode = 01
#本机蓝牙配对参数长度,Just work 模式下 pair len 为 0，pair data 应为空,Passkey Entry 模式下 pair len 为 6
master_pair_len = 00
# 本机蓝牙配对参数 123456(十进制设置),Just work 模式下 pair len 为 0，pair data 应为空,
master_pair_data =

# 从 1蓝牙配对方式,0x01(Just Work),0x02(Passkey Entry),0x00(预留，暂不支持),0x03(OOB,预留，暂不支持)，可以根据需求注释或者值置空，代表不配置该主机
slave_1_dev_pair_mode = 01
#从 1蓝牙配对参数长度,Just work 模式下 pair len 为 0，pair data 应为空,Passkey Entry 模式下 pair len 为 6
slave_1_pair_len = 00
# 从 1蓝牙配对参数 123456(十进制设置),Just work 模式下 pair len 为 0，pair data 应为空,
slave_1_pair_data =

# 从 2蓝牙配对方式,0x01(Just Work),0x02(Passkey Entry),0x00(预留，暂不支持),0x03(OOB,预留，暂不支持)，可以根据需求注释或者值置空，代表不配置该主机
slave_2_dev_pair_mode = 01
#从 2蓝牙配对参数长度,Just work 模式下 pair len 为 0，pair data 应为空,Passkey Entry 模式下 pair len 为 6
slave_2_pair_len = 00
# 从 2蓝牙配对参数 123456(十进制设置),Just work 模式下 pair len 为 0，pair data 应为空,
slave_2_pair_data =

# 从 3蓝牙配对方式,0x01(Just Work),0x02(Passkey Entry),0x00(预留，暂不支持),0x03(OOB,预留，暂不支持)，可以根据需求注释或者值置空，代表不配置该主机
slave_3_dev_pair_mode = 02
#从 3蓝牙配对参数长度,Just work 模式下 pair len 为 0，pair data 应为空,Passkey Entry 模式下 pair len 为 6
slave_3_pair_len = 06
# 从 3蓝牙配对参数 123456(十进制设置),Just work 模式下 pair len 为 0，pair data 应为空,
slave_3_pair_data = 313233343536
#设备配对信息标识位: 包含本机， 从 1，从 2，从 3 的配对信息不置位，不启用配对,如果是选择不启用配对，则去掉data_field注释，去掉注释后，以上参数配置无效
;data_field =00

[F20B0000-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

# 这是命令部分,type报文类型,占用一个字节(01H：透传；02H：配置 SET 蓝牙模块参数；03H：获取 GET 蓝牙模块参数；04H：蓝牙主动上报/通知事件。),
#length数据域的字节数，占用两个字节,a_field传输设备地址,占用六个字节,r_field预留， 占用四个字节,data_field数据域
[00000008-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

[0000001B-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =
[0000001D-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =



[F20B0001-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

[F20B0001-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

[F20B0003-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

[0000001C-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

#power_level发射功率档位[1] ， 0 档位代表 4dBm；
#broadcast_interval广播间隔 40ms，数据大端存储格式， 参数取值范围为 0x20~ 0x4000，单位：0.625ms
#scan_interval扫描间隔 100ms ，数据大端存储格式， 参数取值范围为 0x04~ 0x4000，单位：0.625ms
[F20B0002-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
power_level = 00
broadcast_interval = 0040
scan_interval  = 00A0

[F20B0002-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

[00000006-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
#设置或读取蓝牙链路数据接收模式,0x00(未定义),0x01(缓存模式),0x02(直接传输模式)
data_field =02

[00000006-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
#设置或读取蓝牙链路数据接收模式,0x00(未定义),0x01(缓存模式),0x02(直接传输模式)
data_field =

[00000009-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
#用于扫描功能的控制,0x00(关闭),0x01(打开)
data_field =01

[0000000A-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
#设备地址的数量
dev_num =01
#6 字节连接设备地址数组,如果需要新增地址，按照dev_addr_添加序号
dev_addr_1 = C30000000091
;dev_addr_2 = 0200000000C5

[0000000B-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
#设备类型的数量
signature_num =01
#设备类型数组，N 取决于 signature num 的取值,如果需要新增地址，按照signature_type_添加序号
signature_type_1 = C3

[0000000C-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

[0000000E-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
#广播数据标志 ,长度-类型-值
adv_flag =02 01 06
#厂商指定数据标志(长度-类型)
manufacturer_flag = 16 FF
#设备类别码（1byte）
device_category =C3
#厂商代码（2bytes）
manufacturer_code = FFFF
#断 路 器 自 动 配 对 校 验 码（2bytes）
auto_pair_code =E212
#连接 PIN 码密文（ 16bytes）
pin_code_cipher = 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46
#广播设备名称标志(长度-类型)
device_flag =04 09
#设备名称（3 字节 ASCII）
device_name = 32 35 38

[0000000F-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
#服务 UIID ,长度-类型
UIID_flag =11 05
#6E4000001-B5A3-F393- E0A9-E50E24DC4179（举例，具体参照对 UUID 约定）
UUID(LSB) = 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26
#ManufactorySpecify Data,长度-类型
ManufactorySpecify_Data =09 FF
#Company ID(2bytes)
Company_ID = AA BB
#MAC Address（6bytes）
MAC_Address =C1 C2 C3 C4 C5 C6


[00000010-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
#广播过滤信息主动上报功能,0x00(关闭),0x01(打开)
report_status =01
#广播过滤信息上报周期值为，0x01-0x14(上报周期值，单位是秒),0x00, 0x015-0xFF(上报周期值固定为两秒)
report_interval = 02

[00000013-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
#特征码/断路器自动配对校验码，BIT0 置位，adv data[M]中 M 取值为 2；可以根据需求注释或者值置空，代表不配置该选项参数
;auto_pairing_verification_code = 1234
#连接 PIN 码报文，BIT1 置位，adv data[M]中 M 取值为 16；可以根据需求注释或者值置空，代表不配置该选项参数
;connection_pin_code_message =00112233445566778899AABBCCDDEEFF
#设备名称的信息标识位，BIT2 置位，adv data[M]中 M 取值为 1~3；可以根据需求注释或者值置空，代表不配置该选项参数
device_name_info_flag =444444
#厂商代码 (厂家国网 ID 编号)，BIT3 置位，adv data[M]中 M 取值为 2；可以根据需求注释或者值置空，代表不配置该选项参数
manufacturer_code_id =2233

[00000013-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
#读特征码\断路器自动配对校验，连接 PIN 码报文， 设备名称，厂商代码,0x00-0x0F
data_field =0C

[00000019-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
# 连接或断开主机1,0x01(连接),0x00(断开)，可以根据需求注释或者值置空，代表不配置该主机
master_1_opcode = 01
#主机1 6 字节设备地址，小端存储模式
master_1_addr = C30000000091

# 连接或断开主机2,0x01(连接),0x00(断开)，可以根据需求注释或者值置空，代表不配置该主机
master_2_opcode = 01
#主机2 6 字节设备地址，小端存储模式
master_2_addr = C30000000071

#连接或断开从1,0x01(连接),0x00(断开)，可以根据需求注释或者值置空，代表不配置该主机
slave_1_opcode = 01
#从 1 6 字节设备地址，小端存储模式
slave_1_addr = C30000000051
#连接或断开从2,0x01(连接),0x00(断开)，可以根据需求注释或者值置空，代表不配置该主机
slave_2_opcode = 01
#从 2 6 字节设备地址，小端存储模式
slave_2_addr= C30000000061
#连接或断开从3,0x01(连接),0x00(断开)，可以根据需求注释或者值置空，代表不配置该主机
slave_3_opcode = 01
#从 3 6 字节设备地址，小端存储模式
slave_3_addr = C30000000041

[0000001A-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
#用于启动或停止本设备广播,0x00(停止广播),0x01(启动广播)
data_field =01

[0000001E-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
#蓝牙授权开启、关闭,0x00(关闭),0x01~0xFE(开启蓝牙 1~254 分钟),0xFF(无限时长开启蓝牙)
data_field =FF

[00000000-set-698]
type = 01
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =FE FE FE FE 68 19 00 43 05 01 00 00 00 00 00 20 78 8E 06 01 00 AAAA 02 00 01 00 00 A0 2C 16

[00000000-set-645]
type = 01
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =FE FE FE FE 68 01 00 00 00 00 00 68 11 04 33 33 33 33 B2 16


;[F20B0201-set]
;type = 02
;a_field = FFFFFFFFFFFF
;r_field = 00000000
;#设备类型的数量,0x00--秒脉冲、 0x01--需量、 0x02--时段投切、0x03--正向谐波、0x04--反向谐波、0x05--无功、0x06--有功、 0xFF--关闭
;pulse_type =00
;#信道发送间隔，单位是 ms，默认值为 2
;interval = 02
;#发射功率档位：0 代表 4dBm、1 代表 0dBm、2 代表-4dBm、3 代表-8dBm、4 代表最小档-20dBm
;tx_power = 00
;#通信地址
;comm_addr =112233445566
;#通道数目
;ch_num = 05
;#通道频点，双字节，小端模式存储,根据通道数目定义freq_频点序号
;freq_1 = BE09
;freq_2 = B809
;freq_3 = BB09
;freq_4 = B509
;freq_5 = Bf09


         """
        else:
            # 定义要写入的内容
            ini_content = """
# 这是 MAC 地址和 PIN 码配置
[MAC]
# 本机 MAC 地址 （全 0 或全 FF 为无效的蓝牙 MAC 地址）
masterMac = C10000000009
# 主机1 MAC 地址 （全 0 或全 FF 为无效的蓝牙 MAC 地址）
masterMac_1 = FFFFFFFFFFFF
# 从机 1MAC 地址（全 0 或 FFFFFFFFFFF1 为无效从机 MAC[1]， 若为全 FF 则为自动配对模式）
slaveMac = C30000001112
# 从机 2MAC 地址（全 0 ，全 FF 或 FFFFFFFFFFF1 为无效从机 MAC
slaveMac_2 = C30000000002
# 从机 3MAC 地址（全 0 ，全 FF 或 FFFFFFFFFFF1 为无效从机 MAC）
slaveMac_3 = C30000000003
# 主通道配对 PIN 码加密后的密文（明 文模式）
masterPin_pw = 313233343536FFFFFFFFFFFFFFFFFFFF
 # 主通道配对码（配对 PIN 码固定为 6 字节 ASCII 字符，若不启 用 PIN 则配置为 6 字节全 FF）
masterPin = 313233343536
 # 从通道配对码（配对 PIN 码固定为 6 字节 ASCII 字符，若不启用 PIN 则配置为 6 字节全 FF）。
slavePin = 313233343536313233343536313233343536

[MAC_1]
# 本机 MAC 地址 （全 0 或全 FF 为无效的蓝牙 MAC 地址）
masterMac = C30000000091
# 主机1 MAC 地址 （全 0 或全 FF 为无效的蓝牙 MAC 地址）
masterMac_1 = FFFFFFFFFFFF
# 从机 1MAC 地址（全 0 或 FFFFFFFFFFF1 为无效从机 MAC[1]， 若为全 FF 则为自动配对模式）
slaveMac = C10000000009
# 从机 2MAC 地址（全 0 ，全 FF 或 FFFFFFFFFFF1 为无效从机 MAC
slaveMac_2 = C30000000002
# 从机 3MAC 地址（全 0 ，全 FF 或 FFFFFFFFFFF1 为无效从机 MAC）
slaveMac_3 = C30000000003
# 主通道配对 PIN 码加密后的密文（明 文模式）
masterPin_pw = 313233343536FFFFFFFFFFFFFFFFFFFF
 # 主通道配对码（配对 PIN 码固定为 6 字节 ASCII 字符，若不启 用 PIN 则配置为 6 字节全 FF）
masterPin = 313233343536
 # 从通道配对码（配对 PIN 码固定为 6 字节 ASCII 字符，若不启用 PIN 则配置为 6 字节全 FF）。
slavePin = 313233343536313233343536313233343536

#注意：指令中只要带有data_field并且不为空的情况，那么其他字段参数无效
# 这是命令部分,type报文类型,占用一个字节(01H：透传；02H：配置 SET 蓝牙模块参数；03H：获取 GET 蓝牙模块参数；04H：蓝牙主动上报/通知事件。),
#length数据域的字节数，占用两个字节,a_field传输设备地址,占用六个字节,r_field预留， 占用四个字节,data_field数据域
[00000008-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

[F20B000A-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

[F20B0000-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

#power_level发射功率档位[1] ， 0 档位代表 4dBm；
#broadcast_interval广播间隔 40ms，低字节在前，高字节在后，单位为毫秒，允许设定范围： 40~ 1000ms ，默认 40ms；
#scan_interval扫描间隔 160ms ，低字节在前，高字节在后，单位为毫秒，允许设定范 围：55~ 110ms ，默认 100ms
[F20B0002-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
power_level = 00
broadcast_interval = 2800
scan_interval  = A000

[F20B0002-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =

;[F20B0008-set]
;type = 02
;length = 3600
;a_field = FFFFFFFFFFFF
;r_field = 00000000
;# 主通道 1 配对 PIN 码长度，6 字节（若长度为 0，则配对 PIN 码字段为空[1] )
;masterPin_1_length = 06
;#323232323232——主通道 1 配对 PIN 码“222222 ”
;masterPin_1_pin = 323232323232
;# 主通道 1 配对 PIN 码加密密文长度，16 字节
;masterPin_1_encrypted_pin_length = 10
;# 主通道 1 配对 PIN 码密文广播数据
;masterPin_1_encrypted_pin = 000102030405060708090A0B0C0D0E0F
;
;# 主通道 2 配对 PIN 码长度，6 字节（若长度为 0，则配对 PIN 码字段为空[1] )
;masterPin_2_length = 06
;#主通道 2 配对 PIN 码“222222 ”
;masterPin_2_pin = 323232323232
;# 主通道 2 配对 PIN 码加密密文长度，16 字节
;masterPin_2_encrypted_pin_length = 10
;# 主通道 2 配对 PIN 码密文广播数据
;masterPin_2_encrypted_pin = 000102030405060708090A0B0C0D0E0F
;
;[F20B0008-read]
;type = 03
;length = 0000
;a_field = FFFFFFFFFFFF
;r_field = 00000000
;data_field =
;
;[F20B0009-set]
;type = 02
;length = 2700
;a_field = FFFFFFFFFFFF
;r_field = 00000000
;# 从机 1 配对 PIN 码长度，6 字节（若为 0 时，配对 PIN 码数据字段为空[1]）
;slave_1_length = 06
;#从机 1 配对 PIN 码，“ 111111 ”
;slave_1_pin = 313131313131
;# 从机 2 配对 PIN 码长度，6 字节（若为 0 时，配对 PIN 码数据字段为空）
;slave_2_length = 06
;#从机 2 配对 PIN 码
;slave_2_pin = 323232323232
;# 从机 3 配对 PIN 码长度，6 字节（若为 0 时，配对 PIN 码数据字段为空）
;slave_3_length = 06
;#从机 3 配对 PIN 码
;slave_3_pin = 313131313131

;[F20B0009-read]
;type = 03
;length = 0000
;a_field = FFFFFFFFFFFF
;r_field = 00000000
;data_field =

[F20B0000-set]
type = 02
a_field = FFFFFFFFFFFF
r_field = 00000000
# 厂商 ID（2 字节，盲样送检缺省为 FFFF ，批量生产时配置为各厂商在电 网系统中的公司代码）
manufacturer_id = FFFF
# 设备类型，根据电表技术规范要求配置
device_type = C1
# 特征校验码[2] ，在断路器应用中采用它作为校验作用。在电表应用中，配 置为缺省 FFFF 则代表电能表不启用链路 PIN 加密，广播 16 字节为全 FF。为 0000 时，代表广播 16 字节中包含明文 PIN 。为 0001 时，代表广播 16 字节为加密后的密文313233343536FFFFFFFFFFFFFFFFFFFF ——主通道配对 PIN 码加密后的密文（明 文模式），用于广播中，方便链接主机进行扫描和链接
feature_code = 0000

[F20B0003-read]
type = 03
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =


[00000000-set-698]
type = 01
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =FEFEFEFE685A00C305436509112120A1B97B820058585858585858583138303330355858585831383033303500000000000000000000FFFFFFFFFFFFFFF0FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000C800130100C80000070800000000762916

[00000000-set-645]
type = 01
a_field = FFFFFFFFFFFF
r_field = 00000000
data_field =FEFEFEFE6801000000000068110433333333B216
         """
        # 检查文件是否存在，如果不存在则创建并写入内容
        if not os.path.exists(self.ini_file):
            with open(self.ini_file, 'w', encoding='utf-8') as ini_file:
                ini_file.write(ini_content.strip())
                print(f"{self.ini_file} 已创建并写入内容")
        else:
            print(f"{self.ini_file} 已经存在，无需创建")
    def parse_mac_info(self):
        # 解析 MAC 信息
        mac_info = {}
        # 解析 MAC 信息
        print(f"mac_section_project--xxxxxx--: {mac_section_project}\r\n")
        print(f"mac_section_project----: {mac_section_project[self.mac_section]}\r\n")
        if self.mac_section in self.config:
            if mac_section_project['MAC'] != mac_section_project[self.mac_section]:
                mac_info['masterMac'] = self.config['MAC'].get('masterMac', 'FFFFFFFFFFFF')
                mac_info['masterMac_1'] = self.config['MAC'].get('masterMac_1', 'FFFFFFFFFFFF')
                mac_info['slaveMac'] = self.config['MAC'].get('slaveMac', 'FFFFFFFFFFF1')
                mac_info['slaveMac_2'] = self.config['MAC'].get('slaveMac_2', 'FFFFFFFFFFF1')
                mac_info['slaveMac_3'] = self.config['MAC'].get('slaveMac_3', 'FFFFFFFFFFF1')
                mac_info['masterPin_pw'] = self.config['MAC'].get('masterPin_pw',
                                                                  'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
                mac_info['masterPin'] = self.config['MAC'].get('masterPin', 'FFFFFFFFFFFF')
                mac_info['slavePin'] = self.config['MAC'].get('slavePin', 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
            else:
                mac_info['masterMac'] = self.config[self.mac_section].get('masterMac', 'FFFFFFFFFFFF')
                mac_info['masterMac_1'] = self.config[self.mac_section].get('masterMac_1', 'FFFFFFFFFFFF')
                mac_info['slaveMac'] = self.config[self.mac_section].get('slaveMac', 'FFFFFFFFFFF1')
                mac_info['slaveMac_2'] = self.config[self.mac_section].get('slaveMac_2', 'FFFFFFFFFFF1')
                mac_info['slaveMac_3'] = self.config[self.mac_section].get('slaveMac_3', 'FFFFFFFFFFF1')
                mac_info['masterPin_pw'] = self.config[self.mac_section].get('masterPin_pw', 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
                mac_info['masterPin'] = self.config[self.mac_section].get('masterPin', 'FFFFFFFFFFFF')
                mac_info['slavePin'] = self.config[self.mac_section].get('slavePin', 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
        else:
            mac_info['masterMac'] = self.config['MAC'].get('masterMac', 'FFFFFFFFFFFF')
            mac_info['masterMac_1'] = self.config['MAC'].get('masterMac_1', 'FFFFFFFFFFFF')
            mac_info['slaveMac'] = self.config['MAC'].get('slaveMac', 'FFFFFFFFFFF1')
            mac_info['slaveMac_2'] = self.config['MAC'].get('slaveMac_2', 'FFFFFFFFFFF1')
            mac_info['slaveMac_3'] = self.config['MAC'].get('slaveMac_3', 'FFFFFFFFFFF1')
            mac_info['masterPin_pw'] = self.config['MAC'].get('masterPin_pw',
                                                                         'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
            mac_info['masterPin'] = self.config['MAC'].get('masterPin', 'FFFFFFFFFFFF')
            mac_info['slavePin'] = self.config['MAC'].get('slavePin', 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

        for section in self.config.sections():
            if 'MAC' in section:
                for key, value in self.config.items(section):
                    if 'mac' in key.lower() and value not in self.mac_commands:
                        self.mac_commands.append(value)
        return mac_info
    def check_and_load_ini(self, ini_file='commands.ini'):
        """
        检查是否存在 .ini 文件，如果存在则加载，否则使用默认命令
        :param ini_file: ini 文件路径
        """
        if os.path.exists(ini_file):
            logging.debug(f"{ini_file} found, loading commands from file.")
            return True
        else:
            logging.debug(f"{ini_file} not found, using default commands.")
            return False

    def get_command_name(self, section):
        # 检查 section 是否包含 '-'
        if '-' in section:
            # 通过 '-' 分割 section，并返回前半部分
            return section.split('-')[0]
        return section

    def load_commands_from_ini(self):

        commands = {}
        for section in self.config.sections():
            command = {}
            print(f"Section: {self.mac_section}\r\n")
            if 'MAC' in section:
                continue
            for key, value in self.config.items(section):
                print(f"  {key} = {value}")

            command_name = self.get_command_name(section)
            command['type'] = int(self.config.get(section, 'type').strip(), 16)
            command['length'] = [int(self.config.get(section, 'length').strip()[i:i + 2], 16) for i in
                                 range(0, len(self.config.get(section, 'length').strip()), 2)]
            command['A_field'] = [int(self.config.get(section, 'A_field').strip()[i:i + 2], 16) for i in
                                  range(0, len(self.config.get(section, 'A_field').strip()), 2)]
            command['R_field'] = [int(self.config.get(section, 'R_field')[i:i + 2], 16) for i in
                                  range(0, len(self.config.get(section, 'R_field').strip()), 2)]
            # 从 name 中提取控制域
            control_field_str = command_name
            command['control_field'] = [int(control_field_str[i:i + 2], 16) for i in
                                        range(0, len(control_field_str), 2)][::-1]
            if 'set' in section:
                if command_name == 'F20B0002':
                    power_level = int(self.config.get(section, 'power_level').strip(), 16)
                    broadcast_interval = [int(self.config.get(section, 'broadcast_interval').strip()[i:i + 2], 16) for i
                                          in
                                          range(0, len(self.config.get(section, 'broadcast_interval').strip()), 2)]
                    scan_interval = [int(self.config.get(section, 'scan_interval').strip()[i:i + 2], 16) for i in
                                     range(0, len(self.config.get(section, 'scan_interval').strip()), 2)]
                    # 拼接到 data_field 中
                    data_field = [power_level] + broadcast_interval + scan_interval
                    command['data_field'] = data_field
                elif command_name == 'F20B0001':
                    command['data_field'] = [int(self.mac_info['masterMac'][i:i + 2], 16) for i in
                                             range(0, len(self.mac_info['masterMac']), 2)]
                    # 将 Slave MAC 地址转换为十六进制列表并添加到 D 后面
                    command['data_field'] += [int(self.mac_info['slaveMac'][i:i + 2], 16) for i in
                                              range(0, len(self.mac_info['slaveMac']), 2)]

                    command['data_field'] += [int(self.mac_info['slaveMac_2'][i:i + 2], 16) for i in
                                              range(0, len(self.mac_info['slaveMac_2']), 2)]
                    command['data_field'] += [int(self.mac_info['slaveMac_3'][i:i + 2], 16) for i in
                                              range(0, len(self.mac_info['slaveMac_3']), 2)]

                elif command_name == 'F20B0000':
                    if self.project_name == '威胜':
                        device_type = self.config.get(section, 'device_type').strip()
                        manufacturer_id = self.config.get(section, 'manufacturer_id').strip()
                        feature_code = self.config.get(section, 'feature_code').strip()
                        command['data_field'] = [int(self.mac_info['masterMac'][i:i + 2], 16) for i in
                                                 range(0, len(self.mac_info['masterMac']), 2)]
                        # 将 Slave MAC 地址转换为十六进制列表并添加到 D 后面
                        command['data_field'] += [int(self.mac_info['slaveMac'][i:i + 2], 16) for i in
                                                  range(0, len(self.mac_info['slaveMac']), 2)]

                        command['data_field'] += [int(self.mac_info['slaveMac_2'][i:i + 2], 16) for i in
                                                  range(0, len(self.mac_info['slaveMac_2']), 2)]
                        command['data_field'] += [int(self.mac_info['slaveMac_3'][i:i + 2], 16) for i in
                                                  range(0, len(self.mac_info['slaveMac_3']), 2)]

                        command['data_field'] += [int(manufacturer_id[i:i + 2], 16) for i in
                                                  range(0, len(manufacturer_id), 2)]
                        command['data_field'] += [int(device_type[i:i + 2], 16) for i in range(0, len(device_type), 2)]

                        command['data_field'] += [int(feature_code[i:i + 2], 16) for i in
                                                  range(0, len(feature_code), 2)]
                        # 将 Master PIN 转换为十六进制列表并添加到D 后面
                        command['data_field'] += [int(self.mac_info['masterPin_pw'][i:i + 2], 16) for i in
                                                  range(0, len(self.mac_info['masterPin_pw']), 2)]
                        command['data_field'] += [int(self.mac_info['masterPin'][i:i + 2], 16) for i in
                                                  range(0, len(self.mac_info['masterPin']), 2)]
                        command['data_field'] += [int(self.mac_info['slavePin'][i:i + 2], 16) for i in
                                                  range(0, len(self.mac_info['slavePin']), 2)]
                        calculated_checksum = sum(command['data_field']) % 256
                        print(f"所有参数部分的累加和校验码: 0x{calculated_checksum:02X}")
                        # 将校验和添加到 D 列表
                        command['data_field'].append(calculated_checksum)
                    elif self.project_name == '泰瑞捷':
                        data_field = self.config.get(section, 'data_field', fallback="").strip()
                        if data_field:

                            command['data_field'] = [int(data_field[i:i + 2], 16) for i in range(0, len(data_field), 2)]
                            command['length'] = [0x01, 0x00]
                        else:
                            status_mapping = {
                                "master_dev_pair_mode": 0,  # 主机 1
                                "slave_1_dev_pair_mode": 1,  # 从机 1
                                "slave_2_dev_pair_mode": 2,  # 从机 2
                                "slave_3_dev_pair_mode": 3,  # 从机 3
                            }
                            status = self.generate_status_from_config(status_mapping, section)
                            command['data_field'] = [status]
                            mapping = [
                                "master_dev_pair_mode",  # 主机 1
                                "slave_1_dev_pair_mode",  # 从机 1
                                "slave_2_dev_pair_mode",  # 从机 2
                                "slave_3_dev_pair_mode",  # 从机 3
                            ]
                            for key in mapping:
                                if self.config.has_option(section, key):
                                    pair_mode = self.config.get(section, key).strip()  # 获取配对模式，去除空格
                                    print(f"generate_status_from_config pair_mode:{pair_mode}")
                                    pair_len_key = key.replace("dev_pair_mode", "pair_len")  # 对应的参数长度键
                                    # print(f"generate_status_from_config pair_len_key:{pair_len_key}")
                                    pair_len = self.config.get(section, pair_len_key).strip()

                                    pair_data_key = key.replace("dev_pair_mode", "pair_data")  # 对应的参数长度键
                                    # print(f"generate_status_from_config pair_data_key:{pair_data_key}")
                                    if pair_mode == '01':
                                        pair_len = '00'
                                        pair_data = ''
                                    else:
                                        pair_data = self.config.get(section, pair_data_key).strip()
                                    print(f"generate_status_from_config pair_len:{pair_len}")
                                    print(f"generate_status_from_config pair_data:{pair_data}")
                                    # 如果配对方式或长度或者配对数据存在且非空
                                    if pair_mode and pair_len:
                                        command['data_field'] += [int(pair_mode[i:i + 2], 16) for i in
                                                                  range(0, len(pair_mode), 2)]
                                        command['data_field'] += [int(pair_len[i:i + 2], 16) for i in
                                                                  range(0, len(pair_len), 2)]
                                        if pair_data:
                                            command['data_field'] += [int(pair_data[i:i + 2], 16) for i in
                                                                      range(0, len(pair_data), 2)]

                    else:
                        data_field = self.config.get(section, 'data_field').strip()
                        if data_field:
                            command['data_field'] = [int(data_field[i:i + 2], 16) for i in range(0, len(data_field), 2)]
                        else:
                            command['data_field'] = []
                elif command_name == 'F20B0008':
                    masterPin_1_length = [int(self.config.get(section, 'masterPin_1_length').strip(), 16)]
                    masterPin_1_pin = [int(self.config.get(section, 'masterPin_1_pin').strip()[i:i + 2], 16) for i in
                                       range(0, len(self.config.get(section, 'masterPin_1_pin').strip()), 2)]
                    masterPin_1_encrypted_pin_length = [
                        int(self.config.get(section, 'masterPin_1_encrypted_pin_length').strip(), 16)]
                    masterPin_1_encrypted_pin = [
                        int(self.config.get(section, 'masterPin_1_encrypted_pin').strip()[i:i + 2], 16) for i in
                        range(0, len(self.config.get(section, 'masterPin_1_encrypted_pin').strip()), 2)]

                    masterPin_2_length = [int(self.config.get(section, 'masterPin_2_length').strip(), 16)]
                    masterPin_2_pin = [int(self.config.get(section, 'masterPin_2_pin').strip()[i:i + 2], 16) for i in
                                       range(0, len(self.config.get(section, 'masterPin_2_pin').strip()), 2)]
                    masterPin_2_encrypted_pin_length = [
                        int(self.config.get(section, 'masterPin_2_encrypted_pin_length').strip(),
                            16)]
                    masterPin_2_encrypted_pin = [
                        int(self.config.get(section, 'masterPin_2_encrypted_pin').strip()[i:i + 2], 16)
                        for i in
                        range(0, len(self.config.get(section, 'masterPin_2_encrypted_pin').strip()),
                              2)]
                    command['data_field'] = [int(self.mac_info['masterMac'][i:i + 2], 16) for i in
                                             range(0, len(self.mac_info['masterMac']), 2)]
                    command['data_field'] += masterPin_1_length
                    command['data_field'] += masterPin_1_pin
                    command['data_field'] += masterPin_1_encrypted_pin_length
                    command['data_field'] += masterPin_1_encrypted_pin
                    command['data_field'] += masterPin_2_length
                    command['data_field'] += masterPin_2_pin
                    command['data_field'] += masterPin_2_encrypted_pin_length
                    command['data_field'] += masterPin_2_encrypted_pin
                elif command_name == 'F20B0009':
                    slave_1_length = [int(self.config.get(section, 'slave_1_length').strip(), 16)]
                    slave_1_pin = [int(self.config.get(section, 'slave_1_pin').strip()[i:i + 2], 16) for i in
                                   range(0, len(self.config.get(section, 'slave_1_pin').strip()), 2)]
                    slave_2_length = [int(self.config.get(section, 'slave_2_length').strip(), 16)]
                    slave_2_pin = [int(self.config.get(section, 'slave_2_pin').strip()[i:i + 2], 16) for i in
                                   range(0, len(self.config.get(section, 'slave_2_pin').strip()), 2)]

                    slave_3_length = [int(self.config.get(section, 'slave_3_length').strip(), 16)]
                    slave_3_pin = [int(self.config.get(section, 'slave_3_pin').strip()[i:i + 2], 16) for i in
                                   range(0, len(self.config.get(section, 'slave_3_pin').strip()), 2)]

                    command['data_field'] = [int(self.mac_info['slaveMac'][i:i + 2], 16) for i in
                                             range(0, len(self.mac_info['slaveMac']), 2)]
                    command['data_field'] += slave_1_length
                    command['data_field'] += slave_1_pin
                    command['data_field'] += [int(self.mac_info['slaveMac_2'][i:i + 2], 16) for i in
                                              range(0, len(self.mac_info['slaveMac_2']), 2)]
                    command['data_field'] += slave_2_length
                    command['data_field'] += slave_2_pin
                    command['data_field'] += [int(self.mac_info['slaveMac_3'][i:i + 2], 16) for i in
                                              range(0, len(self.mac_info['slaveMac_3']), 2)]
                    command['data_field'] += slave_3_length
                    command['data_field'] += slave_3_pin
                elif command_name == '00000000':
                    command['A_field'] = [int(self.mac_info['slaveMac'][i:i + 2], 16) for i in
                                          range(0, len(self.mac_info['slaveMac']), 2)][::-1]

                    data_field = self.config.get(section, 'data_field').strip()
                    if data_field:
                        command['data_field'] = [int(data_field[i:i + 2], 16) for i in range(0, len(data_field), 2)]

                    else:
                        command['data_field'] = []
                elif command_name == '0000000A':
                    data_field = self.config.get(section, 'data_field', fallback="").strip()
                    if data_field:
                        command['data_field'] = [int(data_field[i:i + 2], 16) for i in range(0, len(data_field), 2)]

                    else:
                        command['data_field'] = [int(self.config.get(section, "dev_num").strip()[i:i + 2], 16) for i in
                                                 range(0, len(self.config.get(section, "dev_num").strip()), 2)]
                        # print(f"command['data_field']----:{command['data_field']}")
                        for key in self.config[section]:
                            # print(f"key----:{key}")
                            if key.startswith("dev_addr_"):
                                # print(f"self.config.get(section, key).strip()----:{self.config.get(section, key).strip()}")
                                command['data_field'] += [int(self.config.get(section, key).strip()[i:i + 2], 16) for i
                                                          in range(0, len(self.config.get(section, key).strip()), 2)]
                    # print(f"command['data_field']--xxx--:{command['data_field']}")
                elif command_name == '0000000B':
                    data_field = self.config.get(section, 'data_field', fallback="").strip()
                    if data_field:
                        command['data_field'] = [int(data_field[i:i + 2], 16) for i in range(0, len(data_field), 2)]
                    else:
                        command['data_field'] = [int(self.config.get(section, "signature_num").strip()[i:i + 2], 16) for
                                                 i in
                                                 range(0, len(self.config.get(section, "signature_num").strip()), 2)]
                        # print(f"command['data_field']----:{command['data_field']}")
                        for key in self.config[section]:
                            # print(f"key----:{key}")
                            if key.startswith("signature_type_"):
                                # print(f"self.config.get(section, key).strip()----:{self.config.get(section, key).strip()}")
                                command['data_field'] += [int(self.config.get(section, key).strip()[i:i + 2], 16) for i
                                                          in range(0, len(self.config.get(section, key).strip()), 2)]
                    # print(f"command['data_field']--xxx--:{command['data_field']}")
                elif command_name == '00000010':
                    data_field = self.config.get(section, 'data_field', fallback="").strip()
                    if data_field:
                        command['data_field'] = [int(data_field[i:i + 2], 16) for i in range(0, len(data_field), 2)]
                    else:
                        command['data_field'] = [int(self.config.get(section, "report_status").strip()[i:i + 2], 16) for
                                                 i in
                                                 range(0, len(self.config.get(section, "report_status").strip()), 2)]
                        command['data_field'] += [int(self.config.get(section, "report_interval").strip()[i:i + 2], 16)
                                                  for i in
                                                  range(0, len(self.config.get(section, "report_interval").strip()), 2)]
                elif command_name == 'F20B0201':
                    data_field = self.config.get(section, 'data_field', fallback="").strip()
                    if data_field:
                        command['data_field'] = [int(data_field[i:i + 2], 16) for i in range(0, len(data_field), 2)]
                    else:
                        command['data_field'] = [int(self.config.get(section, "pulse_type").strip()[i:i + 2], 16) for i
                                                 in range(0, len(self.config.get(section, "pulse_type").strip()), 2)]
                        command['data_field'] += [int(self.config.get(section, "interval").strip()[i:i + 2], 16) for i
                                                  in range(0, len(self.config.get(section, "interval").strip()), 2)]
                        command['data_field'] += [int(self.config.get(section, "tx_power").strip()[i:i + 2], 16) for i
                                                  in range(0, len(self.config.get(section, "tx_power").strip()), 2)]
                        command['data_field'] += [int(self.config.get(section, "comm_addr").strip()[i:i + 2], 16) for i
                                                  in range(0, len(self.config.get(section, "comm_addr").strip()), 2)]
                        command['data_field'] += [int(self.config.get(section, "ch_num").strip()[i:i + 2], 16) for i in
                                                  range(0, len(self.config.get(section, "ch_num").strip()), 2)]

                        for key in self.config[section]:
                            # print(f"key----:{key}")
                            if key.startswith("freq_"):
                                # print(f"self.config.get(section, key).strip()----:{self.config.get(section, key).strip()}")
                                command['data_field'] += [int(self.config.get(section, key).strip()[i:i + 2], 16) for i
                                                          in range(0, len(self.config.get(section, key).strip()), 2)]
                elif command_name == '00000013':
                    if self.project_name == '泰瑞捷':
                        data_field = self.config.get(section, 'data_field', fallback="").strip()
                        if data_field:
                            command['data_field'] = [int(data_field[i:i + 2], 16) for i in range(0, len(data_field), 2)]
                        else:
                            flag_mapping = {
                                "auto_pairing_verification_code": 0,  # BIT0 - 特征码/断路器自动配对校验码
                                "connection_pin_code_message": 1,  # BIT1 - 连接 PIN 码报文
                                "device_name_info_flag": 2,  # BIT2 - 设备名称的信息标识位
                                "manufacturer_code_id": 3,  # BIT3 - 厂商代码 (厂家国网 ID 编号)
                            }
                            status = self.generate_status_from_config(flag_mapping, section)
                            command['data_field'] = [status]
                            mapping = [
                                "auto_pairing_verification_code",
                                "connection_pin_code_message",
                                "device_name_info_flag",
                                "manufacturer_code_id",
                            ]
                            for key in mapping:
                                if self.config.has_option(section, key):
                                    feature_value = self.config.get(section, key).strip()  # 获取配对模式，去除空格

                                    print(f"feature_value:{feature_value}")
                                    # 如果配对方式或长度或者配对数据存在且非空
                                    if feature_value:
                                        command['data_field'] += [int(feature_value[i:i + 2], 16) for i in
                                                                  range(0, len(feature_value), 2)]

                    else:
                        data_field = self.config.get(section, 'data_field', fallback="").strip()
                        if data_field:
                            command['data_field'] = [int(data_field[i:i + 2], 16) for i in range(0, len(data_field), 2)]
                        else:
                            command['data_field'] = []
                elif command_name == '00000019':
                    if self.project_name == '泰瑞捷':
                        data_field = self.config.get(section, 'data_field', fallback="").strip()
                        if data_field:
                            command['data_field'] = [int(data_field[i:i + 2], 16) for i in range(0, len(data_field), 2)]
                        else:
                            flag_mapping = {
                                "master_1_opcode": 0,  # BIT0 -主 1
                                "master_2_opcode": 1,  # BIT1 -主 2
                                "slave_1_opcode": 2,  # BIT2 -从 1
                                "slave_2_opcode": 3,  # BIT3 -从 2
                                "slave_3_opcode": 4,  # BIT4 -从 3
                            }
                            status = self.generate_status_from_config(flag_mapping, section)
                            command['data_field'] = [status]
                            mapping = [
                                "master_1_opcode",
                                "master_2_opcode",
                                "slave_1_opcode",
                                "slave_2_opcode",
                                "slave_3_opcode",
                            ]
                            for key in mapping:
                                if self.config.has_option(section, key):
                                    opcode_value = self.config.get(section, key).strip()  # 获取配对模式，去除空格
                                    pair_addr_key = key.replace("opcode", "addr")  # 对应的参数长度键
                                    pair_addr = self.config.get(section, pair_addr_key).strip()
                                    print(f"opcode_value:{opcode_value}")
                                    # 如果配对方式或长度或者配对数据存在且非空
                                    if feature_value:
                                        command['data_field'] += [int(opcode_value[i:i + 2], 16) for i in
                                                                  range(0, len(opcode_value), 2)]
                                        command['data_field'] += [int(pair_addr[i:i + 2], 16) for i in
                                                                  range(0, len(pair_addr), 2)][::-1]

                    else:
                        data_field = self.config.get(section, 'data_field', fallback="").strip()
                        if data_field:
                            command['data_field'] = [int(data_field[i:i + 2], 16) for i in range(0, len(data_field), 2)]
                        else:
                            command['data_field'] = []
                else:
                    data_field = self.config.get(section, 'data_field', fallback="").strip()
                    if data_field:
                        command['data_field'] = [int(data_field[i:i + 2], 16) for i in range(0, len(data_field), 2)]
                    else:
                        command['data_field'] = []
            elif 'read' in section:
                # 处理 data_field，如果为空，返回空数组
                data_field = self.config.get(section, 'data_field').strip()
                if data_field:
                    command['data_field'] = [int(data_field[i:i + 2], 16) for i in range(0, len(data_field), 2)]
                else:
                    command['data_field'] = []

            size = len(command['data_field'])
            # 将 size 转换为两字节小端
            size_packed = struct.pack("<H", size)
            # 如果需要将其作为整数数组
            size_array = list(size_packed)
            command['length'] = size_array

            L = command['length']  # 长度
            T = command['type']  # 类型
            C = command['control_field']  # 控制域
            A = command['A_field']  # 地址域
            R = command['R_field']  # R0~R3
            D = command['data_field']
            constructed_message = self.construct_message(L, T, C, A, R, D)
            # 输出十六进制格式的报文
            print("Constructed message:", [hex(b) for b in constructed_message])
            # commands.append(constructed_message)
            commands[section] = constructed_message


        else:
            print(f"Section not found in the .ini file")

        return commands

    def load_commands_from_ini_t(self):
        commands = {}
        for section in self.config.sections():
            command = {}
            print(f"Section: {self.mac_section}\r\n")
            if 'MAC' in section:
                continue
            command_name = self.get_command_name(section)
            print(f"command_name: {command_name}\r\n")
            command = {'data_field': []}  # 确保 'data_field' 键存在且是空列表
            if 'set' in section:
                if command_name == 'F20B0001':
                    command['data_field'] = [int(self.mac_info['masterMac'][i:i + 2], 16) for i in
                                             range(0, len(self.mac_info['masterMac']), 2)]
                    # 将 Slave MAC 地址转换为十六进制列表并添加到 D 后面
                    command['data_field'] += [int(self.mac_info['slaveMac'][i:i + 2], 16) for i in
                                              range(0, len(self.mac_info['slaveMac']), 2)]

                    command['data_field'] += [int(self.mac_info['slaveMac_2'][i:i + 2], 16) for i in
                                              range(0, len(self.mac_info['slaveMac_2']), 2)]
                    command['data_field'] += [int(self.mac_info['slaveMac_3'][i:i + 2], 16) for i in
                                              range(0, len(self.mac_info['slaveMac_3']), 2)]

                elif command_name == 'F20B0000':
                    if self.project_name == '威胜':
                        device_type = self.config.get(section, 'device_type').strip()
                        manufacturer_id = self.config.get(section, 'manufacturer_id').strip()
                        feature_code = self.config.get(section, 'feature_code').strip()
                        command['data_field'] = [int(self.mac_info['masterMac'][i:i + 2], 16) for i in
                                                 range(0, len(self.mac_info['masterMac']), 2)]
                        # 将 Slave MAC 地址转换为十六进制列表并添加到 D 后面
                        command['data_field'] += [int(self.mac_info['slaveMac'][i:i + 2], 16) for i in
                                                  range(0, len(self.mac_info['slaveMac']), 2)]

                        command['data_field'] += [int(self.mac_info['slaveMac_2'][i:i + 2], 16) for i in
                                                  range(0, len(self.mac_info['slaveMac_2']), 2)]
                        command['data_field'] += [int(self.mac_info['slaveMac_3'][i:i + 2], 16) for i in
                                                  range(0, len(self.mac_info['slaveMac_3']), 2)]

                        command['data_field'] += [int(manufacturer_id[i:i + 2], 16) for i in
                                                  range(0, len(manufacturer_id), 2)]
                        command['data_field'] += [int(device_type[i:i + 2], 16) for i in
                                                  range(0, len(device_type), 2)]

                        command['data_field'] += [int(feature_code[i:i + 2], 16) for i in
                                                  range(0, len(feature_code), 2)]
                        # 将 Master PIN 转换为十六进制列表并添加到D 后面
                        command['data_field'] += [int(self.mac_info['masterPin_pw'][i:i + 2], 16) for i in
                                                  range(0, len(self.mac_info['masterPin_pw']), 2)]
                        command['data_field'] += [int(self.mac_info['masterPin'][i:i + 2], 16) for i in
                                                  range(0, len(self.mac_info['masterPin']), 2)]
                        command['data_field'] += [int(self.mac_info['slavePin'][i:i + 2], 16) for i in
                                                  range(0, len(self.mac_info['slavePin']), 2)]
                        calculated_checksum = sum(command['data_field']) % 256
                        print(f"所有参数部分的累加和校验码: 0x{calculated_checksum:02X}")
                        # 将校验和添加到 D 列表
                        command['data_field'].append(calculated_checksum)
                    elif self.project_name == '泰瑞捷':
                        status_mapping = {
                            "master_dev_pair_mode": 0,  # 主机 1
                            "slave_1_dev_pair_mode": 1,  # 从机 1
                            "slave_2_dev_pair_mode": 2,  # 从机 2
                            "slave_3_dev_pair_mode": 3,  # 从机 3
                        }
                        status = self.generate_status_from_config(status_mapping, section)
                        command['data_field'] = [status]
                        # print(f"value --------------:{value}")

                elif command_name == 'F20B0008':
                    command['data_field'] = [int(self.mac_info['masterMac'][i:i + 2], 16) for i in
                                             range(0, len(self.mac_info['masterMac']), 2)]

                elif command_name == 'F20B0009':
                    slave_1_length = [int(self.config.get(section, 'slave_1_length').strip(), 16)]
                    slave_1_pin = [int(self.config.get(section, 'slave_1_pin').strip()[i:i + 2], 16) for i in
                                   range(0, len(self.config.get(section, 'slave_1_pin').strip()), 2)]
                    slave_2_length = [int(self.config.get(section, 'slave_2_length').strip(), 16)]
                    slave_2_pin = [int(self.config.get(section, 'slave_2_pin').strip()[i:i + 2], 16) for i in
                                   range(0, len(self.config.get(section, 'slave_2_pin').strip()), 2)]

                    slave_3_length = [int(self.config.get(section, 'slave_3_length').strip(), 16)]
                    slave_3_pin = [int(self.config.get(section, 'slave_3_pin').strip()[i:i + 2], 16) for i in
                                   range(0, len(self.config.get(section, 'slave_3_pin').strip()), 2)]

                    command['data_field'] = [int(self.mac_info['slaveMac'][i:i + 2], 16) for i in
                                             range(0, len(self.mac_info['slaveMac']), 2)]
                    command['data_field'] += slave_1_length
                    command['data_field'] += slave_1_pin
                    command['data_field'] += [int(self.mac_info['slaveMac_2'][i:i + 2], 16) for i in
                                              range(0, len(self.mac_info['slaveMac_2']), 2)]
                    command['data_field'] += slave_2_length
                    command['data_field'] += slave_2_pin
                    command['data_field'] += [int(self.mac_info['slaveMac_3'][i:i + 2], 16) for i in
                                              range(0, len(self.mac_info['slaveMac_3']), 2)]
                    command['data_field'] += slave_3_length
                    command['data_field'] += slave_3_pin
                elif command_name == '00000013':
                    if self.project_name == '泰瑞捷':
                        flag_mapping = {
                            "auto_pairing_verification_code": 0,  # BIT0 - 特征码/断路器自动配对校验码
                            "connection_pin_code_message": 1,  # BIT1 - 连接 PIN 码报文
                            "device_name_info_flag": 2,  # BIT2 - 设备名称的信息标识位
                            "manufacturer_code_id": 3,  # BIT3 - 厂商代码 (厂家国网 ID 编号)
                        }
                        status = self.generate_status_from_config(flag_mapping, section)
                        command['data_field'] = [status]
                elif command_name == '00000000':
                    command['a_field'] = [int(self.mac_info['slaveMac'][i:i + 2], 16) for i in
                                              range(0, len(self.mac_info['slaveMac']), 2)][::-1]
                elif command_name == '00000019':
                    if self.project_name == '泰瑞捷':
                        flag_mapping = {
                            "master_1_opcode": 0,  # BIT0 -主 1
                            "master_2_opcode": 1,  # BIT1 -主 2
                            "slave_1_opcode": 2,  # BIT2 -从 1
                            "slave_2_opcode": 3,  # BIT3 -从 2
                            "slave_3_opcode": 4,  # BIT4 -从 3
                        }
                        status = self.generate_status_from_config(flag_mapping, section)
                        command['data_field'] = [status]

            for key, value in self.config.items(section):
                print(f"  {key} = {value}")
                if key == 'type':
                    command[key] = [int(value.replace(" ", "")[i:i + 2], 16) for i in
                                    range(0, len(value.replace(" ", "")), 2)]
                    # print(f"command['type']: {command['type']}\r\n")
                elif key == 'a_field':
                    if command_name != '00000000':
                        command[key] = [int(value.replace(" ", "")[i:i + 2], 16) for i in
                                    range(0, len(value.replace(" ", "")), 2)]
                    # print(f"command['A_field']: {command['a_field']}\r\n")
                elif key == 'r_field':
                    command[key] = [int(value.replace(" ", "")[i:i + 2], 16) for i in
                                    range(0, len(value.replace(" ", "")), 2)]
                    # print(f"command['R_field']: {command['r_field']}\r\n")
                else:
                    data_field = self.config.get(section, 'data_field', fallback="").replace(" ", "")
                    if data_field:
                        command['data_field'] = [int(data_field[i:i + 2], 16) for i in
                                                  range(0, len(data_field), 2)]
                    else:
                        if value:
                            command['data_field'] += [int(value.replace(" ", "")[i:i + 2], 16) for i in range(0, len(value.replace(" ", "")), 2)]

            print(f"--------------------- ----------------------")
            print(f"command['data_field']: {command['data_field']}\r\n")
            # 从 name 中提取控制域
            control_field_str = command_name
            command['control_field'] = [int(control_field_str[i:i + 2], 16) for i in
                                        range(0, len(control_field_str), 2)][::-1]

            size = len(command['data_field'])
            # 将 size 转换为两字节小端
            size_packed = struct.pack("<H", size)
            # 如果需要将其作为整数数组
            size_array = list(size_packed)
            command['length'] = size_array

            L = command['length']  # 长度
            T = command['type']  # 类型
            C = command['control_field']  # 控制域
            A = command['a_field']  # 地址域
            R = command['r_field']  # R0~R3
            D = command['data_field']
            constructed_message = self.construct_message(L, T, C, A, R, D)
            # 输出十六进制格式的报文
            print("Constructed message:", [hex(b) for b in constructed_message])
            # commands.append(constructed_message)
            commands[section] = constructed_message


        else:
            print(f"Section not found in the .ini file")

        return commands

    def generate_status_from_config(self, mapping, section):
        """
        根据配置生成连接状态标识
        :param config: 字典，包含主机和从机配置信息
        :return: 连接状态标识 (1 字节)
        """
        status = 0

        for key, bit_position in mapping.items():
            # print(f"generate_status_from_config key:{key}")
            # 检查配置是否存在
            if self.config.has_option(section, key):
                key_value = self.config.get(section, key).strip()  # 获取配对模式，去除空格
                # 如果配对方式或长度存在且非空，则设置对应位
                if key_value:
                    status |= (1 << bit_position)  # 设置对应位为 1
        print(f"generate_status_from_config status:{status:02X}")
        return status

    def calculate_checksum(self, byte_list):
        checksum = sum(byte_list) % 256
        return checksum

    def construct_message(self,L, T, C, A, R, D):
        # 起始头部
        header = [0xFE, 0xFE, 0xFE, 0xFE]

        # 起始符
        start_byte = [0x68]

        # 长度 L
        length_bytes = L

        # 类型 T
        type_byte = T

        # 控制域 C0~C3
        C_bytes = C

        # 地址域 A5~A0
        A_bytes = A

        # R0~R3 字节
        R_bytes = R

        # 数据域 D0~Dn
        D_bytes = D

        # 第二个 68H 起始符
        second_start_byte = [0x68]

        # 组合报文（从起始符到数据域）
        message_body = start_byte + length_bytes + type_byte + C_bytes + A_bytes + R_bytes + second_start_byte + D_bytes
        # print(f"message_body: {message_body}\r\n")
        # 计算校验和（不包含 FE FE FE FE 和校验和本身）
        checksum = self.calculate_checksum(message_body)

        # 结束符
        end_byte = [0x16]

        # 组合完整报文
        full_message = header + message_body + [checksum] + end_byte

        return full_message

    def send_commands_trj00000007(self):
        L = [0x02, 0x00]  # 长度
        T = [0xC4]  # 类型
        C = [0x07, 0x00, 0x00, 0x00]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        D = [0x01, 0x00]
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("Constructed message:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_trj0000001C(self, data):
        size = len(data)
        # 将 size 转换为两字节小端
        size_packed = struct.pack("<H", size)
        # 如果需要将其作为整数数组
        size_array = list(size_packed)
        L = size_array  # 长度
        T = [0x03] # 类型
        C = [0x1C, 0x00, 0x00, 0x00]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        D = data
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("Constructed message:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_00000007(self):
        L = [0x02, 0x00]  # 长度
        T = [0x84]  # 类型
        C = [0x07, 0x00, 0x00, 0x00]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        D = [0x01, 0x00]
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("Constructed message:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_00000008(self):
        L = [0x00, 0x00]  # 长度
        T = [0x03]  # 类型
        C = [0x08, 0x00, 0x00, 0x00]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        D = []
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("Constructed message:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_F20B000A(self):
        L = [0x00, 0x00] # 长度
        T = [0x03]  # 类型
        C = [0x0A, 0x00, 0x0B, 0xF2]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        D = []
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("Constructed message:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_get_F20B0000(self):
        L = [0x00, 0x00] # 长度
        T = [0x03]  # 类型
        C = [0x00, 0x00, 0x0B, 0xF2]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        D = []
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("Constructed message:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_set_F20B0000(self):

        L = [0x46, 0x00] # 长度
        T = [0x02]  # 类型
        C = [0x00, 0x00, 0x0B, 0xF2]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        D = []
        # 构造报文
        textEditMasterMacLast = self.mac_info['masterMac']  # 发送编辑区上次masterMac字符串备份
        textEditSlaveMacLast = self.mac_info['slaveMac'] # 发送编辑区上次slaveMac字符串备份
        textEditMasterPinLast = self.mac_info['masterPin'] # 发送编辑区上次masterPin字符串备份
        textEditmasterPin_pw = self.mac_info['masterPin_pw']
        textEditslavePin = self.mac_info['slavePin']
        textEditslaveMac_2 = self.mac_info['slaveMac_2']
        textEditslaveMac_3 = self.mac_info['slaveMac_3']
        # 厂商 ID
        manufacturer_id = self.config.get('F20B0000-set', 'manufacturer_id').strip()
        # 设备类型
        device_type = self.config.get('F20B0000-set', 'device_type').strip()
        # 特征校验码
        feature_code = self.config.get('F20B0000-set', 'feature_code').strip()
        # 判断是否有空值
        if not textEditMasterMacLast:
            textEditMasterMacLast = 'FFFFFFFFFFFF'
            print("Master MAC 地址为空，指令使用默认值FFFFFFFFFFFF！")

        if not textEditSlaveMacLast:
            textEditSlaveMacLast = 'FFFFFFFFFFF1'
            print("从机1MAC 地址为空，指令使用默认值 FFFFFFFFFFF1！")

        if not textEditslaveMac_2:
            textEditslaveMac_2 = 'FFFFFFFFFFF1'
            print("从机2MAC 地址为空，指令使用默认值 FFFFFFFFFFF1！")

        if not textEditslaveMac_3:
            textEditslaveMac_3 = 'FFFFFFFFFFF1'
            print("从机3MAC 地址为空，指令使用默认值FFFFFFFFFFF1！")

        if not textEditmasterPin_pw:
            textEditmasterPin_pw = 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
            print("主通道配对 PIN 码加密后的密文(明文 模式)为空，指令使用默认值FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF！")

        if not textEditMasterPinLast:
            textEditMasterPinLast = 'FFFFFFFFFFFF'
            print("Master PIN 码为空，指令使用默认值FFFFFFFFFFFF！")

        if not textEditslavePin:
            textEditslavePin = 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
            print("从通道配对码为空，指令使用默认值FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF！")
        # 将 Master MAC 地址转换为十六进制列表
        D = [int(textEditMasterMacLast[i:i + 2], 16) for i in range(0, len(textEditMasterMacLast), 2)]
        # 将 Slave MAC 地址转换为十六进制列表并添加到 D 后面
        D += [int(textEditSlaveMacLast[i:i + 2], 16) for i in range(0, len(textEditSlaveMacLast), 2)]

        D += [int(textEditslaveMac_2[i:i + 2], 16) for i in range(0, len(textEditslaveMac_2), 2)]
        D += [int(textEditslaveMac_3[i:i + 2], 16) for i in range(0, len(textEditslaveMac_3), 2)]

        D += [int(manufacturer_id[i:i + 2], 16) for i in range(0, len(manufacturer_id), 2)]
        D += [int(device_type[i:i + 2], 16) for i in range(0, len(device_type), 2)]

        D += [int(feature_code[i:i + 2], 16) for i in range(0, len(feature_code), 2)]
        # 将 Master PIN 转换为十六进制列表并添加到D 后面
        D += [int(textEditmasterPin_pw[i:i + 2], 16) for i in range(0, len(textEditmasterPin_pw), 2)]
        D += [int(textEditMasterPinLast[i:i + 2], 16) for i in range(0, len(textEditMasterPinLast), 2)]
        D += [int(textEditslavePin[i:i + 2], 16) for i in range(0, len(textEditslavePin), 2)]
        calculated_checksum = sum(D) % 256
        print(f"所有参数部分的累加和校验码: 0x{calculated_checksum:02X}")
        # 将校验和添加到 D 列表
        D.append(calculated_checksum)
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("Constructed message:", [hex(b) for b in constructed_message])
        return constructed_message

    def send_commands_set_F20B0002(self):
        L = [0x05, 0x00]  # 长度
        T = [0x02]  # 类型
        C = [0x02, 0x00, 0x0B, 0xF2]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        D = [0x00, 0x28, 0x00, 0xA0, 0x00]
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("Constructed message:", [hex(b) for b in constructed_message])
        return constructed_message

    def send_commands_get_F20B0002(self):
        L = [0x00, 0x00]  # 长度
        T = [0x03]  # 类型
        C = [0x02, 0x00, 0x0B, 0xF2]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        D = []
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("Constructed message:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_get_F20B0003(self):
        L = [0x00, 0x00]  # 长度
        T = [0x03]  # 类型
        C = [0x03, 0x00, 0x0B, 0xF2]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        D = []
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("Constructed message:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_set_F20B0003(self):
        L = [0x1F, 0x00]  # 长度
        T = [0x04]  # 类型
        C = [0x03, 0x00, 0x0B, 0xF2]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        D = [0x1F]
        textEditMasterMac = 'C4409405E771'
        textEditMasterMac_2 = 'F4479B6CFB01'
        textEditSlaveMac = 'C32201141001'
        textEditslaveMac_2 = 'C32201141002'
        textEditslaveMac_3 = 'C32201141003'
        D += [int(textEditMasterMac[i:i + 2], 16) for i in range(0, len(textEditMasterMac), 2)]
        D += [int(textEditMasterMac_2[i:i + 2], 16) for i in range(0, len(textEditMasterMac_2), 2)]

        D += [int(textEditSlaveMac[i:i + 2], 16) for i in range(0, len(textEditSlaveMac), 2)]
        # 将 Master PIN 转换为十六进制列表并添加到D 后面
        D += [int(textEditslaveMac_2[i:i + 2], 16) for i in range(0, len(textEditslaveMac_2), 2)]
        D += [int(textEditslaveMac_3[i:i + 2], 16) for i in range(0, len(textEditslaveMac_3), 2)]
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("Constructed message:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_00000000(self):
        L = [0x1B, 0x00]  # 长度
        T = [0x04]  # 类型
        C = [0x07, 0x00, 0x00, 0x00]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        D = [0x01, 0x01, 0x02,0x03,0x04,0x05,0x06,0x07, 0x08, 0x09, 0x0A, 0x0B ,0x0C, 0x0D ,0x0E ,0x0F ,0x00, 0x01 ,0x02, 0x03 ,0x04, 0x02, 0x00 ,0x00 ,0x39 ,0x00 ,0x0D]
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("Constructed message:", [hex(b) for b in constructed_message])
        return constructed_message

    def send_commands_get_version_0000002E(self):
        L = [0x0b, 0x00]  # 长度
        T = [0x02]  # 类型
        C = [0x2e, 0x00, 0x00, 0x00]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        HANDLE = [0x09, 0x00]
        MODE = [0x00, 0x00]
        OFFSET = [0x00, 0x00]
        CTRLCODE = [0x00]
        OTHER = [0x00, 0x00, 0x00, 0x00]
        D = HANDLE + MODE +OFFSET +CTRLCODE +OTHER
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("send_commands_get_version_0000002E:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_OTA_CTRL_START_0000002E(self):
        L = [0x0b, 0x00]  # 长度
        T = [0x02]  # 类型
        C = [0x2e, 0x00, 0x00, 0x00]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        HANDLE = [0x0b, 0x00]
        MODE = [0x00, 0x00]
        OFFSET = [0x00, 0x00]
        CTRLCODE = [0xAA]
        OTHER = [0x00, 0x00, 0x00, 0x00]
        D = HANDLE + MODE +OFFSET +CTRLCODE +OTHER
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("send_commands_OTA_CTRL_START_0000002E:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_OTA_CTRL_PAGE_BEGIN_0000002E(self, addr):
        L = [0x0b, 0x00]  # 长度
        T = [0x02]  # 类型
        C = [0x2e, 0x00, 0x00, 0x00]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        HANDLE = [0x0b, 0x00]
        MODE = [0x00, 0x00]
        OFFSET = [0x00, 0x00]
        CTRLCODE = [0xB0]
        OTHER = addr
        D = HANDLE + MODE +OFFSET +CTRLCODE +OTHER
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("send_commands_OTA_CTRL_PAGE_BEGIN_0000002E:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_OTA_CTRL_REBOOT_0000002E(self):
        L = [0x0b, 0x00]  # 长度
        T = [0x02]  # 类型
        C = [0x2e, 0x00, 0x00, 0x00]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        HANDLE = [0x0b, 0x00]
        MODE = [0x00, 0x00]
        OFFSET = [0x00, 0x00]
        CTRLCODE = [0xFF]
        OTHER = [0x00, 0x00, 0x00, 0x00]
        D = HANDLE + MODE +OFFSET +CTRLCODE +OTHER
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("send_commands_OTA_CTRL_REBOOT_0000002E:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_OTA_CTRL_METADATA_0000002E(self, data):
        # 将 size 转换为两字节小端
        size_packed = struct.pack("<H", len(data) + 7)
        # 如果需要将其作为整数数组
        size_array = list(size_packed)
        L = size_array  # 长度
        T = [0x02]  # 类型
        C = [0x2e, 0x00, 0x00, 0x00]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        HANDLE = [0x0b, 0x00]
        MODE = [0x00, 0x00]
        OFFSET = [0x00, 0x00]
        CTRLCODE = [0xE0]
        OTHER = data
        D = HANDLE + MODE +OFFSET +CTRLCODE +OTHER
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("send_commands_OTA_CTRL_METADATA_0000002E:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_OTA_CTRL_PAGE_END_0000002E(self, length, crc):
        L = [0x0b, 0x00]  # 长度
        T = [0x02]  # 类型
        C = [0x2e, 0x00, 0x00, 0x00]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        HANDLE = [0x0b, 0x00]
        MODE = [0x00, 0x00]
        OFFSET = [0x00, 0x00]
        CTRLCODE = [0xB1]
        print("send_commands_OTA_CTRL_PAGE_END_0000002E--------:", length)
        length_packed = struct.pack("<H", length)
        # 如果需要将其作为整数数组
        length_array = list(length_packed)
        print("send_commands_OTA_CTRL_PAGE_END_0000002E:", [hex(b) for b in length_array])
        crc_packed = struct.pack("<H", crc)
        # 如果需要将其作为整数数组
        crc_array = list(crc_packed)
        OTHER = length_array +crc_array
        D = HANDLE + MODE +OFFSET +CTRLCODE +OTHER
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("send_commands_OTA_CTRL_PAGE_END_0000002E:", [hex(b) for b in constructed_message])
        return constructed_message

    def send_commands_OTA_WriteData_0000002E(self, size, data):
        # 将 size 转换为两字节小端
        size_packed = struct.pack("<H", size+6)

        # 如果需要将其作为整数数组
        size_array = list(size_packed)
        print(size_array)
        L = size_array  # 长度
        T = [0x02]  # 类型
        C = [0x2e, 0x00, 0x00, 0x00]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        HANDLE = [0x0D, 0x00]
        MODE = [0x00, 0x00]
        OFFSET = [0x00, 0x00]
        CTRLCODE = [0xB0]
        OTHER = data
        D = HANDLE + MODE +OFFSET +OTHER
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("send_commands_OTA_CTRL_PAGE_BEGIN_0000002E:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_FFFF0005(self, parsed_result):
        L = [0x13, 0x00]  # 长度
        T = [0x02]  # 类型
        C = [0x05, 0x00, 0xFF, 0xFF]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        pulse_type = parsed_result['pulse_type']
        print(f"pulse_type: {pulse_type}")
        channel_interval = parsed_result['channel_interval']
        print(f"channel_interval: {channel_interval}")
        transmit_power = parsed_result['transmit_power']
        print(f"transmit_power: {transmit_power}")
        comm_address = parsed_result['comm_address']
        frequency_points_1 = parsed_result['frequency_points_1']
        frequency_points_2 = parsed_result['frequency_points_2']
        frequency_points_3 = parsed_result['frequency_points_3']
        frequency_points_4 = parsed_result['frequency_points_4']
        frequency_points_5 = parsed_result['frequency_points_5']
        D = [int(pulse_type[i:i + 2], 16) for i in range(0, len(pulse_type), 2)]
        D += [int(channel_interval[i:i + 2], 16) for i in range(0, len(channel_interval), 2)]
        D += [int(transmit_power[i:i + 2], 16) for i in range(0, len(transmit_power), 2)]
        D += comm_address[::-1]
        D += frequency_points_1[::-1]
        D += frequency_points_2[::-1]
        D += frequency_points_3[::-1]
        D += frequency_points_4[::-1]
        D += frequency_points_5[::-1]
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("Constructed message:", [hex(b) for b in constructed_message])
        return constructed_message
    def send_commands_F20B0201(self, parsed_result):
        T = [0x02]  # 类型
        C = [0x01, 0x02, 0x0B, 0xF2]  # 控制域
        A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # 地址域
        R = [0x00, 0x00, 0x00, 0x00]  # R0~R3
        pulse_type = parsed_result['pulse_type']
        print(f"pulse_type: {pulse_type}")
        channel_interval = parsed_result['channel_interval']
        print(f"channel_interval: {channel_interval}")
        transmit_power = parsed_result['transmit_power']
        print(f"transmit_power: {transmit_power}")
        comm_address = parsed_result['comm_address']
        # 存储所有 frequency_points 的键
        frequency_keys = [
            'frequency_points_1',
            'frequency_points_2',
            'frequency_points_3',
            'frequency_points_4',
            'frequency_points_5',
        ]
        ch_num = 0
        for key in frequency_keys:
            print(f"{key}: {parsed_result[key]}")
            if parsed_result[key]:  # 如果 frequency_point 不为空
                ch_num += 1
        print(f"非空键数量: {ch_num}")

        frequency_points_1 = parsed_result['frequency_points_1']
        frequency_points_2 = parsed_result['frequency_points_2']
        frequency_points_3 = parsed_result['frequency_points_3']
        frequency_points_4 = parsed_result['frequency_points_4']
        frequency_points_5 = parsed_result['frequency_points_5']
        D = [int(pulse_type[i:i + 2], 16) for i in range(0, len(pulse_type), 2)]
        D += [int(channel_interval[i:i + 2], 16) for i in range(0, len(channel_interval), 2)]
        D += [int(transmit_power[i:i + 2], 16) for i in range(0, len(transmit_power), 2)]
        D += comm_address
        hex_str = f"{ch_num:02X}"  # 转换为十六进制字符串
        D += [int(hex_str[i:i + 2], 16) for i in range(0, len(hex_str), 2)]
        D += frequency_points_1[::-1]
        D += frequency_points_2[::-1]
        D += frequency_points_3[::-1]
        D += frequency_points_4[::-1]
        D += frequency_points_5[::-1]
        size_packed = struct.pack("<H", len(D))

        # 如果需要将其作为整数数组
        size_array = list(size_packed)
        print(size_array)
        L = size_array  # 长度
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("Constructed message:", [hex(b) for b in constructed_message])
        return constructed_message
    def parse_except_00000000_645(self, byte_list):
        print("byte_list message:", [hex(b) for b in byte_list])
        T = byte_list[7]  # 类型
        C = byte_list[8:12]  # 控制域
        A = byte_list[12:18]  # 地址域
        R = byte_list[18:22]  # R0~R3
        test_parts = []
        length_bytes = byte_list[5:7][::-1]
        length = length_bytes[0] * 256 + length_bytes[1]  # 将两个字节组合为一个整数
        logging.debug("parse_except_00000000_645 Length: 0x{:02X}".format(length))

        data_field = byte_list[23:23 + length]
        logging.debug("parse_except_00000000_645 D0~Dn: {}".format([hex(b) for b in data_field]))
        data_field_str = ''.join([f"{byte:02X}" for byte in data_field])
        logging.debug("parse_except_00000000_645 D0~Dn_str:{}".format(data_field_str))

        # 跳过同步字节 FE FE FE FE
        header = data_field[:4]
        # 报文起始符
        start_byte = data_field[4]

        checksum = byte_list[23 + length]
        logging.debug("parse_except_00000000_645 Checksum: 0x{:02X}".format(checksum))

        # 报文结束符
        final_end_byte = byte_list[24 + length]
        logging.debug("parse_except_00000000_645 final_end_byte: 0x{:02X}".format(final_end_byte))

        a_byte = data_field[5:11]
        logging.debug("parse_except_00000000_645 a_byte: {}".format([hex(b) for b in a_byte]))

        start_byte_1 = data_field[11]
        print(f"start_byte_1 : {start_byte_1}")

        c_byte = data_field[12]
        logging.debug("parse_except_00000000_645 c_byte: 0x{:02X}".format(c_byte))

        data_length = data_field[13]
        logging.debug("parse_except_00000000_645 data_length: 0x{:02X}".format(data_length))

        data_field_1 = data_field[14:14 + data_length]
        logging.debug("parse_except_00000000_645 data_field_1: {}".format([hex(b) for b in data_field_1]))

        hcs = data_field[14 + data_length]
        print(f"hcs : {hcs}")

        final_end_byte_1 = data_field[15 + data_length]
        logging.debug("final_end_byte_1: 0x{:02X}".format(final_end_byte_1))

        new_data_field = header + [start_byte]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有起始字符S:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有起始字符S FE FE FE FE 68 05 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 XX 16", True))

        new_data_field = header + [start_byte] + a_byte
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有起始符S和地址域A:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有起始符S和地址域A FE FE FE FE 68 0B 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 XX 16", True))

        new_data_field = header + [start_byte] + a_byte +[start_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有S，A和帧起始符S:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有S，A和帧起始符S FE FE FE FE 68 0C 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 XX 16", True))

        new_data_field = header + [start_byte] + a_byte +[start_byte_1] + [c_byte]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有S，A，S和控制码C:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有S，A，S和控制码C FE FE FE FE 68 0D 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 11 XX 16", True))

        new_data_field = header + [start_byte] + a_byte +[start_byte_1] + [c_byte] + [data_length]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有S，A，S，C和数据域长度L:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有S，A，S，C和数据域长度L FE FE FE FE 68 0E 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 11 04 XX 16", True))

        new_data_field = header + [start_byte] + a_byte +[start_byte_1] + [c_byte] + [data_length] + data_field_1
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有完整帧头和数据部分:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有完整帧头和数据部分 FE FE FE FE 68 12 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 11 04 33 33 33 33 XX 16", True))

        new_data_field = header + [start_byte] + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有起始符和结束符部分:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有起始符和结束符部分 FE FE FE FE 68 06 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 16 XX 16", True))

        new_data_field = header + [start_byte] + a_byte + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有起始符，地址域A和结束符:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有起始符，地址域A和结束符 FE FE FE FE 68 0C 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 16 XX 16", True))

        new_data_field = header + [start_byte] + a_byte + [start_byte_1] + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有起始符，地址域A，帧起始符和结束符部分:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有起始符，地址域A，帧起始符和结束符部分 FE FE FE FE 68 0D 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 16 XX 16", True))

        new_data_field = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有起始符，地址域A，帧起始符，控制码和结束符部分:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有起始符，地址域A，帧起始符，控制码和结束符部分 FE FE FE FE 68 0E 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 11 16 XX 16", True))

        new_data_field = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [data_length] + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有起始符，地址域A，帧起始符，控制码，数据域长度和结束符部分:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有起始符，地址域A，帧起始符，控制码，数据域长度和结束符部分 FE FE FE FE 68 0F 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 11 04 16 XX 16", True))

        hc = header + [0xFF] + a_byte + [start_byte_1] + [c_byte] + [data_length] + data_field_1
        hcs_1 = self.calculate_checksum(hc)

        new_data_field = header + [0xFF] + a_byte + [start_byte_1] + [c_byte] + [data_length] + data_field_1 + [hcs_1] + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 起始符错误:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 起始符错误 FE FE FE FE 68 14 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE FF 01 00 00 00 00 00 68 11 04 33 33 33 33 XX 16 XX 16", True))

        hc = header + [start_byte] + a_byte + [0xFF] + [c_byte] + [data_length] + data_field_1
        hcs_1 = self.calculate_checksum(hc)



        new_data_field = header + [start_byte] + a_byte + [0xFF] + [c_byte] + [data_length] + data_field_1 + [hcs_1] + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 帧起始符错误:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 帧起始符错误 FE FE FE FE 68 14 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 FF 11 04 33 33 33 33 XX 16 XX 16", True))

        hc = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [0xF4] + data_field_1
        hcs_1 = self.calculate_checksum(hc)

        new_data_field = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [0xF4] + data_field_1 + [hcs_1] + [
            final_end_byte_1]

        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令:数据域长度错误:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令:数据域长度错误 FE FE FE FE 68 14 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 11 F4 33 33 33 33 XX 16 XX 16", True))



        new_data_field = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [data_length] + data_field_1 + [0xFF] + [
            final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 帧校验错误:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 帧校验错误 FE FE FE FE 68 14 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 11 04 33 33 33 33 FF 16 XX 16", True))


        new_data_field = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [data_length] + data_field_1 + [
            hcs] + [0xF6]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 结束符错误:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 结束符错误 FE FE FE FE 68 14 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 11 04 33 33 33 33 B2 F6 XX 16", True))


        data_field_n = []
        data_field_n[:14] = header + [start_byte] + [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        print("异常指令: 数据域包含起始字符data_field_n:", [hex(b) for b in data_field_n])
        hc = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [0x0E] + data_field_n
        hcs_1 = self.calculate_checksum(hc)
        new_data_field = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [0x0E] + data_field_n + [
            hcs_1] + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 数据域包含起始字符:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 数据域包含起始字符 FE FE FE FE 68 1E 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 11 0E FE FE FE FE 68 00 00 00 00 00 00 00 00 00 XX 16 XX 16", False))

        data_field_n = []
        data_field_n[:14] = header + [start_byte] + a_byte + [0x00, 0x00, 0x00]
        print("异常指令: 数据域包含起始字符和地址域 data_field_n:", [hex(b) for b in data_field_n])
        hc = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [0x0E] + data_field_n
        hcs_1 = self.calculate_checksum(hc)
        new_data_field = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [0x0E] + data_field_n + [
            hcs_1] + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 数据域包含起始字符和地址域:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 数据域包含起始字符和地址域 FE FE FE FE 68 1E 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 11 0E FE FE FE FE 68 01 00 00 00 00 00 00 00 00 XX 16 XX 16", False))

        data_field_n = []
        data_field_n[:14] = header + [start_byte] + a_byte + [start_byte_1]+ [ 0x00, 0x00]
        print("异常指令: 数据域包含起始字符，地址域和帧起始符data_field_n:", [hex(b) for b in data_field_n])
        hc = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [0x0E] + data_field_n
        hcs_1 = self.calculate_checksum(hc)
        new_data_field = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [0x0E] + data_field_n + [
            hcs_1] + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 数据域包含起始字符，地址域和帧起始符:", [hex(b) for b in constructed_message])
        test_parts.append((constructed_message,"异常指令: 数据域包含起始字符，地址域和帧起始符 FE FE FE FE 68 1E 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 11 0E FE FE FE FE 68 01 00 00 00 00 00 68 00 00 XX 16 XX 16", False))

        data_field_n = []
        data_field_n[:14] = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [0x00]
        print("异常指令: 数据域包含起始字符，地址域和帧起始符，控制码data_field_n:", [hex(b) for b in data_field_n])
        hc = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [0x0E] + data_field_n
        hcs_1 = self.calculate_checksum(hc)
        new_data_field = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [0x0E] + data_field_n + [
            hcs_1] + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 数据域包含起始字符，地址域和帧起始符，控制码:", [hex(b) for b in constructed_message])
        test_parts.append((constructed_message,
                           "异常指令: 数据域包含起始字符，地址域和帧起始符，控制码 FE FE FE FE 68 1E 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 11 0E FE FE FE FE 68 01 00 00 00 00 00 68 11 00 XX 16 XX 16", False))

        data_field_n = []
        data_field_n[:14] = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [final_end_byte_1]
        print("异常指令: 数据域包含起始字符，地址域和帧起始符，控制码，结束符data_field_n:", [hex(b) for b in data_field_n])
        hc = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [0x0E] + data_field_n
        hcs_1 = self.calculate_checksum(hc)
        new_data_field = header + [start_byte] + a_byte + [start_byte_1] + [c_byte] + [0x0E] + data_field_n + [
            hcs_1] + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 数据域包含起始字符，地址域和帧起始符，控制码，结束符:", [hex(b) for b in constructed_message])
        test_parts.append((constructed_message,
                           "异常指令: 数据域包含起始字符，地址域和帧起始符，控制码，结束符 FE FE FE FE 68 1E 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 01 00 00 00 00 00 68 11 0E FE FE FE FE 68 01 00 00 00 00 00 68 11 16 XX 16 XX 16", False))

        return test_parts

    def parse_except_00000000_698(self, byte_list):
        T = byte_list[7]  # 类型
        C = byte_list[8:12]  # 控制域
        A = byte_list[12:18]  # 地址域
        R = byte_list[18:22]  # R0~R3
        test_parts = []
        length_bytes = byte_list[5:7][::-1]
        length = length_bytes[0] * 256 + length_bytes[1]  # 将两个字节组合为一个整数
        logging.debug("parse_except_00000000 Length: 0x{:02X}".format(length))

        data_field = byte_list[23:23 + length]
        logging.debug("parse_except_00000000 D0~Dn: {}".format([hex(b) for b in data_field]))
        data_field_str = ''.join([f"{byte:02X}" for byte in data_field])
        logging.debug("parse_except_00000000 D0~Dn_str:{}".format(data_field_str))

        # 跳过同步字节 FE FE FE FE
        header = data_field[:4]
        # 报文起始符
        start_byte = data_field[4]

        checksum = byte_list[23 + length]
        logging.debug("parse_except_00000000 Checksum: 0x{:02X}".format(checksum))

        # 报文结束符
        final_end_byte = byte_list[24 + length]
        logging.debug("parse_except_00000000 final_end_byte: 0x{:02X}".format(final_end_byte))

        data_length_bytes = data_field[5:7][::-1]
        data_length = data_length_bytes[0] * 256 + data_length_bytes[1]  # 将两个字节组合为一个整数
        logging.debug("parse_except_00000000 data_length: 0x{:02X}".format(data_length))

        c_byte = data_field[7]
        logging.debug("parse_except_00000000 c_byte: 0x{:02X}".format(c_byte))

        a_length_byte = data_field[8]+1
        logging.debug("parse_except_00000000 a_length_byte: 0x{:02X}".format(a_length_byte))
        print(f"a_length_byte : {a_length_byte}")
        a_byte = data_field[8:8+a_length_byte+1]
        logging.debug("parse_except_00000000 a_byte: {}".format([hex(b) for b in a_byte]))
        print(f"a_byte : {a_byte}")
        ca_byte = data_field[8+a_length_byte+1]
        print(f"ca_byte : {ca_byte}")
        hcs = data_field[10+a_length_byte:12+a_length_byte]
        print(f"hcs : {hcs}")
        logging.debug("parse_except_00000000 hcs: {}".format([hex(b) for b in hcs]))

        data_field_1 = data_field[5:5 + data_length]
        logging.debug("parse_except_00000000 data_field_1: {}".format([hex(b) for b in data_field_1]))

        data_field_2 = data_field[12+a_length_byte:3 + data_length]
        logging.debug("parse_except_00000000 data_field_2: {}".format([hex(b) for b in data_field_2]))

        fcs = data_field[3 + data_length:5 + data_length]
        logging.debug("parse_except_00000000 fcs: {}".format([hex(b) for b in fcs]))
        final_end_byte_1 = data_field[5 + data_length]
        logging.debug("final_end_byte_1: 0x{:02X}".format(final_end_byte_1))

        new_data_field = header + [start_byte]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有起始字符S :", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有起始字符S FE FE FE FE 68 60 00 01 ... 68 FE FE FE FE 68  XX 16", True))
        new_data_field = header + [start_byte] + data_field[5:7]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只发起始符S和长度域:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只发起始符S和长度域L FE FE FE FE 68 60 00 01 ... 68 FE FE FE FE 68 5A 00  XX 16", True))

        new_data_field = header + [start_byte] + data_field[5:7]+[c_byte]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有S，L和控制域C:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有S，L和控制域C FE FE FE FE 68 60 00 01 ... 68 FE FE FE FE 68 5A 00 C3  XX 16", True))

        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [ca_byte]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有S，L，C和地址域A:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有S，L，C和地址域A FE FE FE FE 68 60 00 01 ... 68 FE FE FE FE 68 5A 00 C3 05 43 65 09 11 21 20  XX 16", True))

        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [ca_byte] + hcs
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有S，L，C，A和帧头检验HCS:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有S，L，C，A和帧头检验HCS FE FE FE FE 68 ... 68 FE FE FE FE 68 5A 00 C3 05 43 65 09 11 21 20 A1 B9  XX 16", True))

        new_data_field = header + [start_byte] + data_field[5:3 + data_length]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有完整帧头和链路数据部分:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有完整帧头和链路数据部分 FE FE FE FE 68 ... 68 FE FE FE FE 68 ...C8 00 00 07 08 00 00 00 00  XX 16", True))

        new_data_field = header + [start_byte] + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有起始符和结束符部分:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有起始符和结束符部分 FE FE FE FE 68 60 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 76 29 16 XX 16", True))

        new_data_field = header + [start_byte] + fcs + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有起始符，帧校验FCS和结束符:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有起始符，帧校验FCS和结束符 FE FE FE FE 68 60 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 76 29 16 XX 16", True))

        new_data_field = header + [start_byte] + data_field[5:7] + fcs + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有起始符，长度域，帧校验和结束符部分:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有起始符，长度域，帧校验和结束符部分 FE FE FE FE 68 60 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 5A 00 76 29 16 XX 16", True))

        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + fcs + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有起始符，长度域，控制域，帧校验和结束符部分:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有起始符，长度域，控制域，帧校验和结束符部分 FE FE FE FE 68 60 00 01 00 00 00 00 XX XX XX XX XX XX 00 00 00 00 68 FE FE FE FE 68 5A 00 C3 76 29 16 XX 16", True))

        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [ca_byte] + hcs + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有起始符，长度域，控制域，地址域，帧头校验和结束符部分:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有起始符，长度域，控制域，地址域，帧头校验和结束符部分 FE FE FE FE 68 ... FE FE FE FE 68 5A 00 C3 05 43 65 09 11 21 20 A1 B9 16 XX 16", True))

        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [ca_byte] + hcs + fcs + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 只有起始符，长度域，控制域，地址域，帧头校验，帧校验和结束符部分:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 只有起始符，长度域，控制域，地址域，帧头校验，帧校验和结束符部分 FE FE FE FE 68 ... FE FE FE FE 68 5A 00 C3 05 43 65 09 11 21 20 A1 B9 76 29 16 XX 16", True))

        new_data_field = [0xFF, 0xFF, 0xFF, 0xFF] + [start_byte] + data_field_1 + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 起始符错误:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 起始符错误 FE FE FE FE 68 ... FF FF FF FF 68 5A 00 C3 05 43 65 09 11 21 20 A1 B9... 76 29 16 XX 16", True))

        hc = [0x00, 0x00] + [c_byte] + a_byte + [
            ca_byte]
        hcs_1 = self.tryfcs16(hc)
        hcs_n = [hcs_1 & 0xFF, (hcs_1 >> 8) & 0xFF]
        print(f"hcs_n: {hcs_n}\r\n")

        fc = [0x00, 0x00] + [c_byte] + a_byte + [
            ca_byte] + hcs_n + data_field_2
        fcs_1 = self.tryfcs16(fc)
        fcs_n = [fcs_1 & 0xFF, (fcs_1 >> 8) & 0xFF]
        print(f"fcs_n: {fcs_n}\r\n")

        new_data_field = header + [start_byte] + [0x00, 0x00] + [c_byte] + a_byte + [
            ca_byte] + hcs_n + data_field_2 + fcs_n + [
                             final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 长度域错误:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 长度域错误 FE FE FE FE 68 ... FF FF FF FF 68 00 00 C3 05 43 65 09 11 21 20 A1 B9... 76 29 16 XX 16", True))

        hc = data_field[5:7] + [c_byte] + [data_field[8]] + [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        hcs_1 = self.tryfcs16(hc)
        hcs_n = [hcs_1 & 0xFF, (hcs_1 >> 8) & 0xFF]
        print(f"hcs_n: {hcs_n}\r\n")

        fc = data_field[5:7] + [c_byte] + [data_field[8]] + [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF] + hcs_n + data_field_2
        fcs_1 = self.tryfcs16(fc)
        fcs_n = [fcs_1 & 0xFF, (fcs_1 >> 8) & 0xFF]
        print(f"fcs_n: {fcs_n}\r\n")

        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + [data_field[8]] + [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF] + hcs_n + data_field_2 + fcs_n + [
                             final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 地址域错误:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 地址域错误 FE FE FE FE 68 ... FF FF FF FF 68 00 00 C3 05 ff ff ff ff ff ff A1 B9... 76 29 16 XX 16", True))

        fc = data_field[5:7] + [c_byte] + a_byte + [ca_byte] + [0xFF, 0xFF] + data_field_2
        fcs_1 = self.tryfcs16(fc)
        fcs_n = [fcs_1 & 0xFF, (fcs_1 >> 8) & 0xFF]

        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [
            ca_byte] + [0xFF, 0xFF] + data_field_2 + fcs_n + [
                             final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 帧头校验错误:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 帧头校验错误 FE FE FE FE 68 ... FE FE FE FE 68 5A 00 C3 05 43 65 09 11 21 20 A1 FF FF ... 29 16 XX 16", True))

        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [
            ca_byte] + hcs + data_field_2 + [0xFF, 0xFF] + [
                             final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 帧校验错误:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 帧校验错误 FE FE FE FE 68 ... FE FE FE FE 68 5A 00 C3 05 43 65 09 11 21 20 A1 B9 7B 82  ... FF FF 16 XX 16", True))

        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [
            ca_byte] + hcs + data_field_2 + fcs + [0xFF]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 结束符错误:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 结束符错误 FE FE FE FE 68 ... FE FE FE FE 68 5A 00 C3 05 43 65 09 11 21 20 A1 B9 7B 82  ... 76 29 FF XX 16", True))

        data_field_n = data_field_2
        data_field_n[:5] = header + [start_byte]
        print("异常指令: 数据域包含起始字符 data_field_n:", [hex(b) for b in data_field_n])
        fc = data_field[5:7] + [c_byte] + a_byte + [ca_byte] + hcs + data_field_n
        fcs_1 = self.tryfcs16(fc)
        fcs_n = [fcs_1 & 0xFF, (fcs_1 >> 8) & 0xFF]
        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [
            ca_byte] + hcs + data_field_n + fcs_n + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 数据域包含起始字符:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 数据域包含起始字符 FE FE FE FE 68 ... FE FE FE FE 68 5A 00 C3 05 ...A1 B9 FE FE FE FE 68 58.. 76 29 FF XX 16", False))

        data_field_n = data_field_2
        data_field_n[:7] = header + [start_byte] + data_field[5:7]
        print("异常指令: 数据域包含起始字符和长度域 data_field_n:", [hex(b) for b in data_field_n])
        fc = data_field[5:7] + [c_byte] + a_byte + [ca_byte] + hcs + data_field_n
        fcs_1 = self.tryfcs16(fc)
        fcs_n = [fcs_1 & 0xFF, (fcs_1 >> 8) & 0xFF]
        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [
            ca_byte] + hcs + data_field_n + fcs_n + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 数据域包含起始字符和长度域:", [hex(b) for b in constructed_message])
        test_parts.append(
            (constructed_message,
             "异常指令: 数据域包含起始字符和长度域 FE FE FE FE 68 ... FE FE FE FE 68 5A 00 C3 05 ...A1 B9 FE FE FE FE 68 5A 00 58.. 76 29 FF XX 16", False))

        data_field_n = data_field_2
        data_field_n[:8] = header + [start_byte] + data_field[5:7] + [c_byte]
        print("异常指令: 数据域包含起始字符，长度域和控制域 data_field_n:", [hex(b) for b in data_field_n])
        fc = data_field[5:7] + [c_byte] + a_byte + [ca_byte] + hcs + data_field_n
        fcs_1 = self.tryfcs16(fc)
        fcs_n = [fcs_1 & 0xFF, (fcs_1 >> 8) & 0xFF]
        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [
            ca_byte] + hcs + data_field_n + fcs_n + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 数据域包含起始字符，长度域和控制域:", [hex(b) for b in constructed_message])
        test_parts.append((constructed_message,"异常指令: 数据域包含起始字符，长度域和控制域 FE FE FE FE 68 ... FE FE FE FE 68 5A 00 C3 05 ...A1 B9 FE FE FE FE 68 5A 00 C3 58.. 76 29 FF XX 16", False))

        data_field_n = data_field_2
        data_field_n[:16] = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [ca_byte]
        print("异常指令: 数据域包含起始字符，长度域，控制域和地址域data_field_n:", [hex(b) for b in data_field_n])
        fc = data_field[5:7] + [c_byte] + a_byte + [ca_byte] + hcs + data_field_n
        fcs_1 = self.tryfcs16(fc)
        fcs_n = [fcs_1 & 0xFF, (fcs_1 >> 8) & 0xFF]
        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [
            ca_byte] + hcs + data_field_n + fcs_n + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 数据域包含起始字符，长度域，控制域和地址域:", [hex(b) for b in constructed_message])
        test_parts.append((constructed_message,
                           "异常指令: 数据域包含起始字符，长度域，控制域和地址域 FE FE FE FE 68 ...A1 B9 FE FE FE FE 68 5A 00 C3 58.. 76 29 FF XX 16", False))

        data_field_n = data_field_2
        data_field_n[:18] = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [ca_byte] + hcs
        print("异常指令: 数据域包含起始字符，长度域，控制域，地址域，帧头检验data_field_n:", [hex(b) for b in data_field_n])
        fc = data_field[5:7] + [c_byte] + a_byte + [ca_byte] + hcs + data_field_n
        fcs_1 = self.tryfcs16(fc)
        fcs_n = [fcs_1 & 0xFF, (fcs_1 >> 8) & 0xFF]
        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [
            ca_byte] + hcs + data_field_n + fcs_n + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 数据域包含起始字符，长度域，控制域，地址域，帧头检验:", [hex(b) for b in constructed_message])
        test_parts.append((constructed_message,
                           "异常指令: 数据域包含起始字符，长度域，控制域，地址域，帧头检验 FE FE FE FE 68 ...A1 B9 FE FE FE FE 68 5A 00 C3 58.. 76 29 FF XX 16", False))

        data_field_n = data_field_2
        data_field_n[:19] = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [ca_byte] + hcs + [final_end_byte]
        print("异常指令: 数据域包含起始字符，长度域，控制域，地址域，帧头检验和结束符data_field_n:", [hex(b) for b in data_field_n])
        fc = data_field[5:7] + [c_byte] + a_byte + [ca_byte] + hcs + data_field_n
        fcs_1 = self.tryfcs16(fc)
        fcs_n = [fcs_1 & 0xFF, (fcs_1 >> 8) & 0xFF]
        new_data_field = header + [start_byte] + data_field[5:7] + [c_byte] + a_byte + [
            ca_byte] + hcs + data_field_n + fcs_n + [final_end_byte_1]
        L = list(struct.pack('<H', len(new_data_field)))
        D = new_data_field
        # 构造报文
        constructed_message = self.construct_message(L, T, C, A, R, D)
        # 输出十六进制格式的报文
        print("异常指令: 数据域包含起始字符，长度域，控制域，地址域，帧头检验和结束符:", [hex(b) for b in constructed_message])
        test_parts.append((constructed_message,
                           "异常指令: 数据域包含起始字符，长度域，控制域，地址域，帧头检验和结束符 FE FE FE FE 68 ...A1 B9 FE FE FE FE 68 5A 00 C3 58.. 76 29 FF XX 16", False))
        return test_parts
    def parse_except_packet(self, byte_list):
        # 跳过同步字节 FE FE FE FE
        header = byte_list[:4]
        # 报文起始符
        start_byte = byte_list[4]
            # 长度 L (两个字节)
        length_bytes = byte_list[5:7][::-1]
        length = length_bytes[0] * 256 + length_bytes[1]  # 将两个字节组合为一个整数
        logging.debug("Parsed Length: 0x{:02X}".format(length))

        # 类型 T (一个字节)
        type_byte = byte_list[7]
        logging.debug("Parsed Type: 0x{:02X}".format(type_byte))
        # 解析地址（6字节）
        # C0~C3 (接下来的四个字节)
        control_code = byte_list[8:12]
        logging.debug("Parsed C0~C3: {}".format([hex(b) for b in control_code]))
        control_code_str = ''.join([f"{byte:02X}" for byte in control_code])
        logging.debug("address_str:{}".format(control_code_str))


        # A5~A0 (接下来的六个字节)
        address = byte_list[12:18]
        logging.debug("Parsed A5~A0: {}".format([hex(b) for b in address]))
        address_str = ''.join([f"{byte:02X}" for byte in address])
        logging.debug("Parsed A5~A0_str:{}".format(address_str))
        # R0~R3 (接下来的四个字节)
        R = byte_list[18:22]
        logging.debug("Parsed R0~R3: {}".format([hex(b) for b in R]))
        # 报文结束符
        end_byte = byte_list[22]


        # D0~Dn (接下来的 N 个字节，N 为长度 L 的值)
        data_field = byte_list[23:23 + length]
        logging.debug("Parsed D0~Dn: {}".format([hex(b) for b in data_field]))
        data_field_str = ''.join([f"{byte:02X}" for byte in data_field])
        logging.debug("Parsed D0~Dn_str:{}".format(data_field_str))
        # 校验和 CS (倒数第二个字节)
        checksum = byte_list[23 + length]
        logging.debug("Parsed Checksum: 0x{:02X}".format(checksum))

        # 报文结束符
        final_end_byte = byte_list[24 + length]
        logging.debug("final_end_byte: 0x{:02X}".format(final_end_byte))
        test_parts = [
            (byte_list[:4], "异常指令: 只发前导码", True),  # 只发送前导码
            (byte_list[:5], "异常指令: 只发前导码和帧起始符", True),  # 前导码 + 帧起始符
            (byte_list[:7], "异常指令: 只发帧头和数据长度L", True),  # 前导码 + 帧起始符 + 长度字段
            (byte_list[:8], "异常指令: 只发帧头，L，报文类型T", True),  # 前导码 + 帧起始符 + 长度字段+报文类型T
            (byte_list[:12], "异常指令: 只发帧头，L，T,控制命令C", True),
            (byte_list[:18], "异常指令: 只发帧头，L，T，C，传输设备地址A", True),
            (byte_list[:22], "异常指令: 只发帧头，L，T，C，A，预留R", True),
            (byte_list[:23], "异常指令: 只发帧头，L，T，C，A，R，帧起始符S", True),
            (byte_list[:23 + length], "异常指令: 只发帧头，L，T，C，A，R，S，数据域D", True),
            (byte_list[:23 + length + 1], "异常指令: 只发帧头，L，T，C，A，R，S，D，校验码C", True),
            (header + [final_end_byte], "异常指令: 只发前导码和结束符", True),
            (header +[start_byte] + [final_end_byte], "异常指令: 只发前导码，帧起始符和结束符", True),
            (header + [start_byte] + [checksum] + [final_end_byte], "异常指令: 只发前导码，帧起始符，检验和结束符", True),
            (byte_list[:7] + [checksum] + [final_end_byte], "异常指令: 只发前导码，帧起始符，数据长度，检验和结束符", True),
        ]


        # 打印解析结果
        return test_parts

    def pppfcs16(self, fcs, cp, length):
        """
        Calculate a new FCS given the current FCS and the new data.
        :param fcs: initial FCS value (16-bit)
        :param cp: data (byte array or list)
        :param length: length of the data
        :return: new FCS value
        """
        for i in range(length):
            fcs = (fcs >> 8) ^ self.fcstab[(fcs ^ cp[i]) & 0xff]
        return fcs

    def tryfcs16(self, data):
        """
        Calculate and check the FCS for a given byte array.
        Adds the FCS to the output and checks on input.
        :param data: byte array or list of data
        :return: None
        """
        # Calculate trial FCS
        trialfc_s = self.pppfcs16(self.PPPINITFCS16, data, len(data))
        print(f"trialfc_s start: {trialfc_s:02X}")
        trialfc_s ^= 0xffff  # complement
        print(f"trialfc_s ----: {trialfc_s:02X}")
        # Append FCS bytes to the data
        data.append(trialfc_s & 0x00ff)  # least significant byte
        data.append((trialfc_s >> 8) & 0x00ff)  # most significant byte

        # Check FCS on input
        c_trialfcs = self.pppfcs16(self.PPPINITFCS16, data, len(data))
        print(f"c_trialfcs end: {c_trialfcs:02X}")
        if c_trialfcs == self.PPPGOODFCS16:
            print("Good FCS")
            return trialfc_s
        else:
            print("Bad FCS")
            return []