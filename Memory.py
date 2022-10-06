import datetime
import hashlib
import GlobalConfig
from CounterBlock import CounterMemoryBlock
from utils import Utils
import time
import logUtils
import logging
import sys
import copy





class Memory:
    """
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。#单位"字节"
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    """
    def __init__(self, memory_size):
        self.memory_size = memory_size
        self.block_size = 64
        self.counter_memory_overhead = 0#初始化为0
        self.BMT_memory_overhead = 0#初始化为0
        self.stat = True
        # data_memory_block的仿真值为长度为64的字符串如“11111111111111111111111111111111111111111111111111111111111111”，字符串中字符的索引位置对应的block中的每个字节。
        #这样寻址的时候就知道是谁了。
        init_data = '0'.zfill(64)
        self.data_memory_blocks = [init_data] * (memory_size//64)
        #self.data_Bytes_list = [0] * memory_size#寻址范围为 0~memory_size，弃用这种写法主要是不知道怎么将加密后的密文按照数组的索引写回去，主要是不知道怎么在数组中存储密文，后续知道了再优化吧。
        #建立Counter memory block区域
        self.counter_memory_blocks = self.init_counter_memory(memory_size)
        print(self.counter_memory_blocks)
        print(len(self.counter_memory_blocks))
        #建立dataHMAC memory block区域
        self.dataHMACs = [0] * (memory_size//64)
        #统计初始化BMT block区域的时间开销。
        #start_timestamp = time.perf_counter()
        starttime = datetime.datetime.now()
        #建立BMT memory block区域
        self.BMT_memory_blocks = []
        self.BMT_height = 0
        print("===========================")
        print(self.counter_memory_blocks)
        print(len(self.counter_memory_blocks))
        self.init_BMT_memory()
        print("******************************")
        print(self.counter_memory_blocks)
        print(len(self.counter_memory_blocks))
        #end_timestamp = time.perf_counter()
        endtime = datetime.datetime.now()
        #time_overhead = Utils.to_human_time(end_timestamp - start_timestamp)
        # logging.debug("初始化BMT树的时间开销为：{}（实际时间）".format(time_overhead))
        logging.debug("初始化BMT树的时间开销为：{}（实际时间）".format((endtime-starttime)))
        self.statistical()

    '''
            功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
            参数：s_index, E_index, counter_addr, counter_block
            返回值：None
            作者：史文燕
            日期：2022
        '''

    def statistical(self):
        if self.stat:
            #统计内存大小
            str_memory_size = Utils.to_human_B(self.memory_size)
            logging.debug(f"本次仿真内存大小为：{str_memory_size}")
            # 统计counter开销
            percentage = '{:.2%}'.format(1 / 64)
            counter_overhead = Utils.to_human_B(self.counter_memory_overhead)
            logging.debug(f"counter的内存开销为：{counter_overhead}, 占内存大小的{percentage} ")
            # 统计dataHMAC开销
            dataHMAC_overhead = self.memory_size / 8
            self.dataHMAC_overhead = dataHMAC_overhead
            dataHMAC_overhead = Utils.to_human_B(dataHMAC_overhead)
            percentage = '{:.2%}'.format(1 / 8)
            logging.debug(f"data HMAC的内存开销为：{dataHMAC_overhead}, 占内存大小的{percentage} ")
            # 统计BMT memory开销
            str_BMT_overhead = Utils.to_human_B(self.BMT_memory_overhead)
            percentage = '{:.2%}'.format((self.BMT_memory_overhead) / self.memory_size)
            logging.debug(f"BMT树的内存开销为：{str_BMT_overhead}, BMT树的高度为：{self.BMT_height}层, 占内存大小的{percentage}")

    '''
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def init_counter_memory(self, memory_size):
        counter_overhead = memory_size / 64
        self.counter_memory_overhead = counter_overhead
        counter_memory_block = CounterMemoryBlock()
        #print(memory_size)
        print((memory_size//(2**12)))
        counter_memory_blocks = [counter_memory_block] * (memory_size//(2**12))
        print(counter_memory_blocks)
        print(len(counter_memory_blocks))
        return counter_memory_blocks

    '''
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    #初始化dataHMAC，使用64bits的data HMAC（这个大小是可变的，是可以根据不同的安全等级需要裁剪的），与data一起存取,atomicity。
    def init_dataHMAC(self):
        for i in range(len(self.data_memory_blocks)):
            counter_block, minor_counter_index = self.get_counter(i, True)
            major_counter = counter_block.major_counter
            minor_counter = counter_block.minor_counter_list[minor_counter_index]
            iv = str(self.data_memory_blocks[i]) + str(major_counter) + str(minor_counter) + str(i)
            self.dataHMACs[i] = Utils.hash_data(iv, "sha256")

    '''
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    #arity=8,按顺序存储BMT，第一层叶子节点的个数即page的个数。第二层的个数是第一层除以8，以此类推。
    def init_BMT_memory_bak(self):
        # 设计内存的时候保证counter_memory_blocks的长度是8的倍数，也就是memory_size是2**15的倍数
        temp_list = []
        leaf_nodes = self.counter_memory_blocks
        temp_list = leaf_nodes
        #记录树的大小、高度
        BMT_overhead = 0
        height = 0
        while len(temp_list) > 1:
            height = height + 1
            #已经设定好每一层叶子层的个数是8的倍数，所以不用考虑7个一组或者6个一组不够8个一组的情况。
            level_list = []
            while len(temp_list) > 1:
                node1 = (temp_list.pop(0))
                node2 = temp_list.pop(0)
                node3 = temp_list.pop(0)
                node4 = temp_list.pop(0)
                node5 = temp_list.pop(0)
                node6 = temp_list.pop(0)
                node7 = temp_list.pop(0)
                node8 = temp_list.pop(0)
                #叶子节点的node不是str，而往上几层的node都是HASH值，所以都是str
                if type(node1) != str:
                    intermediate_node = Utils.hash_data(node1.to_str()) + "|" + Utils.hash_data(node2.to_str()) + "|" + Utils.hash_data(
                        node3.to_str()) + "|" + Utils.hash_data(node4.to_str()) + "|" + Utils.hash_data(node5.to_str()) + "|" + Utils.hash_data(
                        node6.to_str()) + "|" + Utils.hash_data(node7.to_str()) + "|" + Utils.hash_data(node8.to_str())
                else:
                    intermediate_node = Utils.hash_data(node1) + "|" + Utils.hash_data(node2) + "|" + Utils.hash_data(
                        node3) + "|" + Utils.hash_data(node4) + "|" + Utils.hash_data(node5) + "|" + Utils.hash_data(
                        node6) + "|" + Utils.hash_data(node7) + "|" + Utils.hash_data(node8)


                self.BMT_memory_blocks.append(intermediate_node)
                level_list.append(intermediate_node)
                BMT_overhead += 64
            temp_list = level_list
        #最终上面的while循环结束以后，temp_list会剩一个，也就是根，需要保存在芯片上的,这个可以在memory初始化以后，就放在片上去。
        self.BMT_root = temp_list
        self.BMT_memory_overhead = BMT_overhead - 64
        self.BMT_height = height + 1

    '''
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def init_BMT_memory(self):
        # 设计内存的时候保证counter_memory_blocks的长度是8的倍数，也就是memory_size是2**15的倍数
        temp_list = []
        leaf_nodes = copy.copy(self.counter_memory_blocks)
        print("hahaha")
        print(self.counter_memory_blocks)
        print(leaf_nodes)
        temp_list = leaf_nodes
        #记录树的大小、高度
        BMT_overhead = 0
        height = 0
        while len(temp_list) > 1:
            height = height + 1
            #已经设定好每一层叶子层的个数是8的倍数，所以不用考虑7个一组或者6个一组不够8个一组的情况。
            level_list = []
            while len(temp_list) > 1:
                intermediate_node = [0] * 8
                for i in range(8):
                    node = temp_list.pop(0)
                    if type(node) == CounterMemoryBlock:
                        intermediate_node[i] = Utils.hash_data(node.to_str())
                    elif type(node) == list:
                        intermediate_node[i] = Utils.hash_data("".join(node))
                    else:
                        intermediate_node[i] = Utils.hash_data(node)
                self.BMT_memory_blocks.append(intermediate_node)
                level_list.append(intermediate_node)
                BMT_overhead += 64
            temp_list = level_list
        #最终上面的while循环结束以后，temp_list会剩一个，也就是根，需要保存在芯片上的,这个可以在memory初始化以后，就放在片上去。
        self.BMT_root = temp_list[0]
        print(self.BMT_root)
        self.BMT_memory_overhead = BMT_overhead - 64
        self.BMT_height = height + 1
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        print(leaf_nodes)

    '''
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def get_counter(self, counter_addr, init_flag=False):
        #初始化的时候不Sleep，仅针对本实验。如果做与初始化相关的实验，则需要添加延时。默认为False
        if not init_flag:
            time.sleep(GlobalConfig.memory_read_latency)
        #根据addr定位出counter在counter memory中的位置
        page_id = counter_addr//2**12
        page_offset = (counter_addr//2**12)//64
        print(str(page_id)+ "#%&*************")
        print(len(self.counter_memory_blocks))
        counter_block = self.counter_memory_blocks[page_id]
        major_counter = self.counter_memory_blocks[page_id].major_counter
        minor_counter = self.counter_memory_blocks[page_id].minor_counter_list[page_offset]
        return counter_block, page_offset

    '''
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def write_counter(self, addr, counter_block):
        time.sleep(GlobalConfig.memory_write_latency)
        page_id = addr // 2 ** 12
        self.counter_memory_blocks[page_id] = counter_block


    '''
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def write_ciphertext(self, ciphertext, addr):
        #NVM的写延时
        time.sleep(GlobalConfig.memory_write_latency)
        #定位data在memory数组中的位置
        index = addr//64
        self.data_memory_blocks[index] = ciphertext

    '''
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def write_dataHMAC(self, addr, data_HMAC):
        # 更新data HMAC
        self.dataHMACs[addr // 64] = data_HMAC

    '''
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def read_ciphertext(self, addr):
        time.sleep(GlobalConfig.memory_read_latency)
        data_block_index = addr//64
        return self.data_memory_blocks[data_block_index]

    '''
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def read_dataHAMC(self, addr):
        return self.dataHMACs[addr // 64]

    '''
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    #读取明文，仅限制在内存初始化的时候，返回粒度应该是一个64长度的数组。初始化过程重要不要保留延时还在争议阶段，待定。如果需要延时的话，放弃此函数，直接用上面的read_ciphertext函数即可。
    def read_plaintext(self, addr):
        #根据地址范围，return出不同的memory block值，记住，memory和MC传输数据的粒度是64B.
        memory_block_index = addr//64
        return self.data_memory_blocks[memory_block_index]

    '''
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def read_BMT_node(self, BMT_addr):
        BMT_block_index = BMT_addr//64
        return self.BMT_memory_blocks[BMT_block_index]

    '''
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def write_BMT_node(self, BMT_addr, BMTnode):
        BMT_block_index = BMT_addr // 64
        self.BMT_memory_blocks[BMT_block_index] = BMTnode












