import time
import GlobalConfig
from utils import Utils
from CounterBlock import CounterMemoryBlock
from collections import OrderedDict, defaultdict
import math









class DataL2Cache:

    def __init__(self, B, E, S, memory_size):
        self.B = B  # 块大小，固定值，目前缓存与内存的交换粒度就是64B
        self.E = E  # 相连度
        self.S = S  # 组数，全相联
        self.s = Utils.calcuAddrBits(self.S)
        self.cache_size = self.S * self.E * self.B
        cache_set = CacheSet(self.E)
        self.sets = [cache_set] * (self.S)
        #计算memory的地址线位数
        self.m = Utils.calcuAddrBits(memory_size)  # 整个memory的地址线

    '''    
            功能：根据addr查看counter cache，查看是否命中
            参数：counter_addr
            返回值：二进制整数int(2)
            作者：史文燕
            日期：2022
    '''
    def lookup(self, addr):
        hit = False
        s_index, tag, b_offset = self.addr_to_S_tag_offset(addr)
        cache_set = self.sets[s_index]
        E_index = 0
        for i in range(self.E):
            E_index = i
            valid = cache_set.E_rows[i].valid
            if valid:
                if tag == cache_set.E_rows[i].tag:
                    hit = True
                    #LRU queue
                    self.put_index_queue(s_index, E_index)
                    return hit, E_index
        return hit, E_index

    '''    
            功能：根据addr查看counter cache，查看是否命中
            参数：counter_addr
            返回值：二进制整数int(2)
            作者：史文燕
            日期：2022
    '''
    def getData_Incache(self, addr, E_index):
        s_index, tag, b_offset = self.addr_to_S_tag_offset(addr)
        return self.sets[s_index].E_rows[E_index].data_block[b_offset]

    '''    
        功能：lookup命中的情况下，在counter cache中直接更新counter+1
        参数：counter_addr
        返回值：is overflow
        作者：史文燕
        日期：2022
    '''
    def update_data_incache(self, addr, E_index, new_plaintext):
        s_index, tag, b_offset = self.addr_to_S_tag_offset(addr)
        list_temp = list(self.sets[s_index].E_rows[E_index].data_block)
        print("量子纠缠")
        print(list_temp)
        list_temp[b_offset] = new_plaintext
        self.sets[s_index].E_rows[E_index].data_block = "".join(list_temp)
        self.sets[s_index].E_rows[E_index].dirty = 1



    '''    
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    # 从NVM读入counter cache
    def insert_data(self, s_index, E_index, addr, plaintext):
        cache_set = CacheSet(self.E)
        E_row = SetErow()
        E_row.valid = 1
        E_row.tag = self.addr_to_S_tag_offset(addr)[1]
        E_row.data_block= plaintext
        E_row.dirty = 0  # 刚插入为干净行
        cache_set.E_rows[E_index] = E_row
        cache_set.index_queue[E_index] = E_index  # 将插入的行索引放入该组的LRU队列(插入该行就代表该行被用到了）
        self.sets[s_index] = cache_set

    '''    
        功能：根据counter_addr在counter cache中找到的合适的组索引和空闲行索引
        参数：counter_addr
        返回值：是否需要驱逐，s_index, E_index
        作者：史文燕
        日期：2022
    '''
    def find_ERow_for_insert(self, addr):
        s_index, tag, b_offset = self.addr_to_S_tag_offset(addr)
        cache_set = self.sets[s_index]
        E_index = 0
        for i in range(self.E):
            E_index = i
            if cache_set.E_rows[i].valid == 0:
                # LRU queue
                self.put_index_queue(s_index, E_index)
                return True, s_index, E_index
        # 找不到空闲行：使用LRU index_queue找到LRU的行index,FIFO
        E_index = self.find_lru_index(s_index)
        return False, s_index, E_index

    '''    
        功能：根据counter_addr找出该地址对应的缓存中的组索引、tag和字偏移
        参数：
        返回值：
        作者：史文燕
        日期：2022
    '''
    # 由地址计算组索引、标记位、字偏移
    def addr_to_S_tag_offset(self, addr):
        # 先根据sbits的组索引找到对应的组，在对应的组的E行里面找到匹配的标记位，如果标记匹配就命中，否则就不命中
        addr = Utils.num_to_binary(addr, self.m)  # 将地址转换为二进制形态
        #测试预留
        # print(type(addr))
        # print(addr)
        # print(type(addr[-6 - self.s:-6]))
        # print(addr[-6 - self.s:-6])
        # 从地址中找出组索引
        s_index = Utils.trans_str_int(addr[-6 - self.s:-6])
        cache_set = self.sets[s_index]
        # 标记位
        tag = addr[:-6 - self.s]
        # 找出字偏移
        b_offset = Utils.trans_str_int(addr[-6:])
        return s_index, tag, b_offset

    '''    
       功能：根据counter_addr找出该地址对应的缓存中的组索引、tag和字偏移
       参数：
       返回值：
       作者：史文燕
       日期：2022
    '''
    def caculate_eviction_addr(self, S_index, tag):
        #需要先把地址拼接好，按照顺序是，tag|S_index|（offset补0即可）
        print("开始计算eviction_addr...")
        print(tag)
        print(S_index)
        str_s_index = Utils.num_to_binary(S_index, self.s)
        print(str_s_index)
        str_eviction_addr = Utils.zfill_addr(tag+str_s_index, self.m)
        print(str_eviction_addr)
        int_evictin_addr = Utils.trans_str_int(str_eviction_addr)
        print(int_evictin_addr)
        return int_evictin_addr


        pass
    '''    
        功能：根据counter_addr找出该地址对应的缓存中的字偏移
        参数：
        返回值：单独返回字偏移
        作者：史文燕
        日期：2022
    '''
    def addr_to_tag(self, counter_addr):
        return counter_addr[:-6 - self.s]

    def put_index_queue(self, s_index, E_index):
        """数据录入缓存"""
        if E_index in self.sets[s_index].index_queue:
            # 若数据已存在，表示命中一次，需要把数据移到缓存队列末端
            self.sets[s_index].index_queue.move_to_end(E_index)
            return
        self.sets[s_index].index_queue[E_index] = E_index

    #返回队列首元素，然后在将该元素移动到队列的末尾,表示又被访问了
    def find_lru_index(self, s_index):
        first_item = 0
        for key in self.sets[s_index].index_queue.keys():
            first_item = key
            break
        self.sets[s_index].index_queue.move_to_end(first_item)
        return first_item


class CacheSet:
    def __init__(self, E):
        e_row = SetErow()
        self.E_rows = [e_row] * E
        self.index_queue = OrderedDict()  # 有序字典，仅缓存E_index


class SetErow:
    def __init__(self):
        self.valid = 0
        self.tag = 0
        self.data_block = None
        self.dirty = 0
