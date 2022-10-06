import time
import GlobalConfig
from utils import Utils
from CounterBlock import CounterMemoryBlock
from collections import OrderedDict, defaultdict
import math


# 测试1，memory_size是32KB的时候，counter overhead size是512B，如果counter cache是1组8路或者2组4路（B=64是固定的），那么第一遍读完以后，后续的cache应该全部命中，不会有驱逐的。
# 思考，分1组8路和2组4路和8组1路，在counter cache的总容量上相同的，那么具体的区别在哪里呢？最重要的是命中率有什么不同呢？内存缩小会有什么影响呢？这些可以一边做实验一边理解。
# 缓存这种东西，理解多了，对体系结构的优化也会有很大的帮助，整个多级存储的体系。
# counter_cache命中的步骤应该是，先从内存地址计算出需要的counter在counter size中的地址，然后用这个地址去在counter cache中做命中。


class CounterCache:

    def __init__(self, B, E, S, counter_overhead_size):
        self.B = B  # 块大小，固定值，目前缓存与内存的交换粒度就是64B
        self.E = E  # 相连度
        self.S = S  # 组数，全相联
        self.s = Utils.calcuAddrBits(self.S)
        self.cache_size = self.S * self.E * self.B
        cache_set = CacheSet(self.E)
        self.sets = [cache_set] * (self.S)
        # 下面与memory的对应可能也不需要。cache与memory两者完全是依靠addr建立对应联系的，只要拿到地址就可以进行存取和命中了。
        # 这个传参先保留，没有用到。因为目前我的设计理念是，cache没有与memeory的直接交互，只有MC与memory有读取交互，都是通过MC作为中间桥梁实现的。
        # 实际上，我也不清楚cache有没有与memory的直接交互。
        # self.memory = memory
        #计算counter block的地址线位数
        self.m = Utils.calcuAddrBits(counter_overhead_size)  # 地址线的位数，注意不是整个memory的地址线，而是可以覆盖counter memory block那一部分的地址线即可,地址线范围为（0~counter_overhead_size)。


    '''    
        功能：根据counter_addr查看counter cache，查看是否命中,若命中，从缓存中返回想要的counter值
        参数：counter_addr
        返回值：二进制整数int(2)
        作者：史文燕
        日期：2022
    '''
    def get_counter_incache(self, counter_addr, E_index):
        s_index, tag, b_offset = self.addr_to_S_tag_offset(counter_addr)
        cache_set = self.sets[s_index]
        counter_block = cache_set.E_rows[E_index].counter_block
        major_counter = counter_block.major_counter
        minor_counter = counter_block.minor_counter_list[b_offset]
        return major_counter, minor_counter


    '''    
            功能：根据counter_addr查看counter cache，查看是否命中
            参数：counter_addr
            返回值：二进制整数int(2)
            作者：史文燕
            日期：2022
        '''
    def lookup(self, counter_addr):
        hit = False
        s_index, tag, b_offset = self.addr_to_S_tag_offset(counter_addr)
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
        功能：lookup命中的情况下，在counter cache中直接更新counter+1
        参数：counter_addr
        返回值：is overflow
        作者：史文燕
        日期：2022
    '''
    def update_counter_incache(self, counter_addr, E_index):
        s_index, tag, b_offset = self.addr_to_S_tag_offset(counter_addr)
        cache_set = self.sets[s_index]
        overflow = False
        counter_block = cache_set.E_rows[E_index].counter_block
        old_major_counter = counter_block.major_counter
        old_minor_counter = counter_block.minor_counter_list[b_offset]
        new_minor_counter = old_minor_counter + 1
        # 此处需要考虑minor counter溢出的情形,溢出就需要重加密
        if new_minor_counter == 2 ** 7:
            overflow = True
            self.sets[s_index].E_rows[E_index].counter_block.major_counter = old_major_counter + 1  # major_counter+1
            self.sets[s_index].E_rows[E_index].counter_block.minor_counter_list = [0] * 64  # minor_counter清零
            return overflow, old_major_counter + 1, 0
        else:
            self.sets[s_index].E_rows[E_index].counter_block.minor_counter_list[b_offset] = new_minor_counter
            return overflow,old_major_counter, new_minor_counter

    '''    
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    # 从NVM读入counter cache
    def insert_counter(self, s_index, E_index, counter_addr, counter_block):
        cache_set = CacheSet(self.E)
        E_row = SetErow()
        E_row.valid = 1
        E_row.tag = self.addr_to_S_tag_offset(counter_addr)[1]
        E_row.counter_block = counter_block
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
    def find_ERow_for_insert(self, counter_addr):
        s_index, tag, b_offset = self.addr_to_S_tag_offset(counter_addr)
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
    def addr_to_S_tag_offset(self, counter_addr):
        # 先根据sbits的组索引找到对应的组，在对应的组的E行里面找到匹配的标记位，如果标记匹配就命中，否则就不命中
        counter_addr = Utils.num_to_binary(counter_addr, self.m)  # 将地址转换为二进制形态
        # 从地址中找出组索引
        s_index = Utils.trans_str_int(counter_addr[-6 - self.s:-6])
        cache_set = self.sets[s_index]
        # 标记位
        tag = counter_addr[:-6 - self.s]
        # 找出字偏移
        b_offset = Utils.trans_str_int(counter_addr[-6:])
        return s_index, tag, b_offset

    '''    
       功能：根据counter_addr找出该地址对应的缓存中的组索引、tag和字偏移
       参数：
       返回值：
       作者：史文燕
       日期：2022
    '''

    def caculate_eviction_addr(self, S_index, tag):
        # 需要先把地址拼接好，按照顺序是，tag|S_index|（offset补0即可）
        print("开始计算eviction_addr...")
        print(tag)
        print(S_index)
        str_s_index = Utils.num_to_binary(S_index, self.s)
        print(str_s_index)
        str_eviction_addr = Utils.zfill_addr(tag + str_s_index, self.m)
        print(str_eviction_addr)
        int_evictin_addr = Utils.trans_str_int(str_eviction_addr)
        print(int_evictin_addr)
        return int_evictin_addr

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
        print("测试LRU策略")
        print(s_index)
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
        self.counter_block = None
        self.dirty = 0
