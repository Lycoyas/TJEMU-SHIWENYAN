# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from typing import List
import GlobalConfig
from EncryptionEngine import EncryptionEngine
import sys
import logUtils
import logging









# 单元测试
# #配置文件测试
# GlobalConfig.init_global()
# x = bin(3)[2:].zfill(43)
# print(type(x))
# print(x)
# print(len(x))
# print(int("0b11",2))
import base64
from Crypto.Cipher import AES
#定义全局变量
# iv是初始化向量，第一组明文就是用它加密的
#
# key是密钥，这里选择的长度是128比特，所以字符串的长度要固定在16字节。
#
# data就是需要加密的数据
iv = '1234567887654321'
key = 'miyaoxuyao16ziji'
#data = ['hello world', 'shiwenyan']
data = b'010'
data = 'hello'

#编写加密函数
#AES的区块固定是128比特，也就是16字节，所以一开始要先判断明文是否小于16字节，如果小于16字节，需要补齐，为此要写一个补齐的函数。
def pad(data):
    pad_data = data
    for i in range(0, 16-len(data)):
        pad_data = pad_data + ' '
    return pad_data

# 创建AES加密对象
# 用创建好的加密对象，对明文进行加密
# 把加密好的密文用base64编码
# 把字符串解码成字符串
def AES_en(key, data):
    # 将长度不足16字节的字符串补齐
    if len(data) < 16:
        data = pad(data)
    # 创建加密对象
    AES_obj = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
    # 完成加密
    AES_en_str = AES_obj.encrypt(data.encode("utf-8"))
    print(AES_en_str)
    print(type(AES_en_str))
    print(sys.getsizeof(AES_en_str))
    # 用base64编码一下
    AES_en_str = base64.b64encode(AES_en_str)
    print(AES_en_str)
    print(type(AES_en_str))
    print(sys.getsizeof(AES_en_str))
    # 最后将密文转化成字符串
    AES_en_str = AES_en_str.decode("utf-8")
    print(AES_en_str)
    print(type(AES_en_str))
    print(sys.getsizeof(AES_en_str))
    return AES_en_str

# 解密是加密的逆过程，按着加密代码的逆序很容易就能写出
#
# 将密文字符串重新编码成bytes类型
# 将base64编码解开
# 创建AES解密对象
# 用解密对象对密文解密
# 将补齐的空格用strip（）函数除去
# 将明文解码成字符串


def AES_de(key, data):
    # 解密过程逆着加密过程写
    # 将密文字符串重新编码成二进制形式
    data = data.encode("utf-8")
    # 将base64的编码解开
    data = base64.b64decode(data)
    # 创建解密对象
    AES_de_obj = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
    # 完成解密
    AES_de_str = AES_de_obj.decrypt(data)
    # 去掉补上的空格
    AES_de_str = AES_de_str.strip()
    # 对明文解码
    AES_de_str = AES_de_str.decode("utf-8")
    return AES_de_str
# print(data)
# print(sys.getsizeof(data))
# print(sys.getsizeof(''))
# print(sys.getsizeof('c'))
# print(sys.getsizeof('cb'))
# print(sys.getsizeof('cba'))
# print(sys.getsizeof('0'))
# print(sys.getsizeof(1))
# print(sys.getsizeof(11))
# print(sys.getsizeof((2**28)))
# data = AES_en(key, data)
# print(data)
# print(type(data))
# print(sys.getsizeof(data))
# data = AES_de(key, data)
# print(data)

logging.debug(sys._getframe())