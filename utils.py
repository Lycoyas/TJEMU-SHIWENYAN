import hashlib
from time import strftime
from time import gmtime
import time
import math
import logUtils
import logging

class Utils:
    """
        功能：将二进制的字符串形式转换为整数形式，如'01'转换为01
        参数：字符串如‘01’
        返回值：二进制整数int(2)
        作者：史文燕
        日期：2022
    """
    @classmethod
    def hash_data(cls, data, hash_function='sha256'):
        "hash function"
        start_timestamp = time.perf_counter()
        hash_function = getattr(hashlib, hash_function)
        data = data.encode('utf-8')
        end_timestamp = time.perf_counter()
        time_overhead = Utils.to_human_time(end_timestamp - start_timestamp)
        #logging.debug("一次hash的时间开销为：{}".format(time_overhead))
        return hash_function(data).hexdigest()

    '''    
        功能：
        参数：
        返回值：
        作者：史文燕
        日期：2022
    '''
    @classmethod
    def num_to_binary(cls, addr, m):
        return bin(addr)[2:].zfill(m)

    '''    
        功能：将”0000010“形式的字符串地址，补齐为地址线的位数
        参数：
        返回值：
        作者：史文燕
        日期：2022
    '''

    @classmethod
    def zfill_addr(cls, str_addr, m):
        str_addr = str_addr.zfill(m)
        return str_addr

    '''    
        功能：将二进制的字符串形式转换为整数形式，如'01'转换为01
        参数：字符串如‘01’
        返回值：二进制整数int(2)
        作者：史文燕
        日期：2022
    '''
    #计算地址线位数,该函数功能，将整数转换为对应的二进制字符串，返回类型为str。
    @classmethod
    def calcuAddrBits(cls, memory_size):
        if memory_size <= 1:
            return 0
        return int(math.ceil(math.log2(memory_size)))
    '''    
        功能：
        参数：
        返回值：
        作者：史文燕
        日期：2022
    '''
    @classmethod
    def trans_str_int(self, str):
        if not str:
            return 0
        return int(str, 2)

    '''    
        功能：
        参数：
        返回值：
        作者：史文燕
        日期：2022
    '''
    #将以字节显示的数字，转换为human的大小，输出带human单位的字符串。num仅限制在TB级别。超过TB不准确
    @classmethod
    def to_human_B(cls, num):
        if num < 2**10:
            num = str(num) + "B"
        elif num >= 2**10 and num < 2**20:
            num = str(round(num/(2**10), 2)) + "KB"
        elif num >= 2**20 and num < 2**30:
            num = str(round(num/(2**20), 2)) + "MB"
        elif num >= 2**30 and num < 2**40:
            num = str(round(num/(2**30),2)) + "GB"
        else:
            num = str(num/(2**40)) + "TB"
        return num

    '''    
        功能：输入为秒，格式化为符合人习惯的单位(暂时弃用，因为未保留毫秒级别)
        参数：time,秒
        返回值：时：分：秒
        作者：史文燕
        日期：2022
    '''
    @classmethod
    def to_human_time(cls, time):
        return strftime("%H:%M:%S", gmtime(time))

    '''    
        功能：将二进制的字符串形式转换为整数形式，如'01'转换为01
        参数：字符串如‘01’
        返回值：二进制整数int(2)
        作者：史文燕
        日期：2022
    '''
    @classmethod
    def dataAddr_mapto_counterAddr(cls, data_addr):
        page_id = data_addr //(64*64)
        page_offset = (data_addr % (64*64))//64
        #测试预留
        #print(page_id)
        #print(page_offset)
        counter_addr = page_id * 64  + page_offset
        #print(counter_addr)
        return counter_addr

    '''    
        功能：将二进制的字符串形式转换为整数形式，如'01'转换为01
        参数：字符串如‘01’
        返回值：二进制整数int(2)
        作者：史文燕
        日期：2022
    '''
    #下面这两个方法其实是可以合并的，毕竟counter其实就是BMT的叶子节点而已，并没有什么特殊之处。后续处理一下
    @classmethod
    def counterAddr_mapto_BMTAddr(cls, counter_addr):
        BMT_addr = (counter_addr//(64*8))*64 + (counter_addr%(64*8))//64 * 8
        #测试保留
        print(BMT_addr)
        return BMT_addr

    '''    
        功能：将二进制的字符串形式转换为整数形式，如'01'转换为01
        参数：字符串如‘01’
        返回值：二进制整数int(2)
        作者：史文燕
        日期：2022
    '''
    #计算第k层childNode的父节点的地址，也就是第k-1层相应的父节点的地址。（注意此处子节点和父节点的地址都是BMT区域中的地址。另外BMT的高度是从根节点为第一层，叶子节点为最后一层这样的高度计算的。）
    @classmethod
    def caculate_partentNode_addr(cls, childNode_addr, k, counter_flag):
        if counter_flag:
            parentNode_addr = (childNode_addr//(64*8))*64 + (childNode_addr%(64*8))//64 * 8
        else:
            parentNode_addr = childNode_addr//(64*8) * 64 + (8**(k-1))*64 + (childNode_addr%(64*8) // 64) * 8
        #parentNode_addr = childNode_addr // (64 * 8) * 64 + (childNode_addr % (64 * 8) // 64) * 8
        #测试保留
        #print(parentNode_addr)
        return parentNode_addr

    @classmethod
    def caculate_parentNode_addr_index(cls, childNode_addr):
        return (childNode_addr % 64 // 8)



        
#测试预留

#测试dataAddr_mapto_counterAddr方法
# Utils.dataAddr_mapto_counterAddr(63)
# Utils.dataAddr_mapto_counterAddr(64)
# Utils.dataAddr_mapto_counterAddr(127)
# Utils.dataAddr_mapto_counterAddr(128)
# Utils.dataAddr_mapto_counterAddr(2**12-1)
#测试dataAddr_mapto_BMTAddr方法
# Utils.counterAddr_mapto_BMTAddr(0)
# Utils.counterAddr_mapto_BMTAddr(1)
# Utils.counterAddr_mapto_BMTAddr(512)
# Utils.counterAddr_mapto_BMTAddr(576)
# Utils.counterAddr_mapto_BMTAddr(1536)
#测试caculate_partentNode_addr方法
#首先假设BMT只有四层，第一层是根，第四层是叶子节点，只有第二层、第三层保存在BMT memory区域中。BMT memory中的地址排列是从第三层左边开始的。
# Utils.caculate_partentNode_addr(1, 3)
# Utils.caculate_partentNode_addr(64, 3)
# Utils.caculate_partentNode_addr(512, 3)
# Utils.caculate_partentNode_addr(578, 3)
# Utils.caculate_partentNode_addr(642, 3)





