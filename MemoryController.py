import GlobalConfig
from CounterBlock import CounterMemoryBlock
from EncryptionEngine import EncryptionEngine
from CounterCache import CounterCache
from DataL2Cache import DataL2Cache
from Memory import Memory
from BMTCache import BMTCache
from utils import Utils
import sys
import datetime
import logging






class MemoryController:

    """
        功能：初始化内存、缓存，将BMT——root保存在芯片上，初始化加密；
        参数：
        返回值：None
        作者：史文燕
        日期：2022
    """
    def __init__(self):
        logging.info("开始内存初始化...")
        self.memory = Memory(GlobalConfig.memory_size)
        logging.info("内存初始化完成...")
        self.BMT_ROOT = self.memory.BMT_root#相当于将BMT根保存在芯片上
        self.encryption_engine = EncryptionEngine(GlobalConfig.iv, GlobalConfig.AES_key)
        # 看论文架构图的时候metadata cache一般都放在MC里面
        #测试保留
        # print(GlobalConfig.counter_cache_B)
        # print(type(GlobalConfig.counter_cache_B))
        logging.info("开始缓存初始化...")
        self.counter_cache = CounterCache(GlobalConfig.counter_cache_B, GlobalConfig.counter_cache_E, GlobalConfig.counter_cache_S, self.memory.counter_memory_overhead)
        self.dataL2Cache = DataL2Cache(GlobalConfig.data_l2_cache_B, GlobalConfig.data_l2_cache_E, GlobalConfig.counter_cache_S, self.memory.memory_size)
        self.BMTCache = BMTCache(GlobalConfig.BMT_cache_B, GlobalConfig.BMT_cache_E, GlobalConfig.BMT_cache_S, self.memory.BMT_memory_overhead)
        self.statistic()
        logging.info("缓存初始化完成...")
        starttime = datetime.datetime.now()
        logging.info("开始初始化加密...")
        self.init_encryption()
        endtime = datetime.datetime.now()
        logging.info("初始化加密完成...")
        logging.debug("初始化加密耗时：{}（实际时间）".format((endtime - starttime)))



    """
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    """
    def statistic(self):
        logging.info("dataL2_cache的大小设置为{}，具体参数为：B={}，S={}，E={}".format(Utils.to_human_B(self.dataL2Cache.cache_size), self.dataL2Cache.B, self.dataL2Cache.S, self.dataL2Cache.E))
        logging.info("counter_cache的大小设置为{}, 具体参数为：B={}，S={}，E={}".format(Utils.to_human_B(self.counter_cache.cache_size), self.counter_cache.B, self.counter_cache.S, self.counter_cache.E))
        logging.info("BMT_cache的大小设置为{}, 具体参数为：B={}，S={}，E={}".format(Utils.to_human_B(self.BMTCache.cache_size), self.BMTCache.B, self.BMTCache.S, self.BMTCache.E))

    """
        功能：对全内存进行初始化加密，并生成data HMAC。循环全地址范围，读取内存内容，但是绕过解密环节，因为初始化的时候内存还是明文，所以不需要解密，如果解密会导致明文发生改变。
        不解密读进来，加密写回去。memory与MC交换数据的粒度是64Bytes，同样的加密解密的基本单元也是64。
        参数：
        返回值：None
        作者：史文燕
        日期：2022
    """
    def init_encryption(self):
        #测试预留
        #i = 0
        for addr in range(self.memory.memory_size):
            if addr%64 != 0:
                continue
            #从内存中读取初始明文
            plaintext = self.memory.read_plaintext(addr)
            #测试预留
            # logging.debug(plaintext + "({})({})".format(i,len(plaintext)))
            # logging.debug(type(plaintext))
            # i = i + 1
            #加密写回,最后一个参数1代表初始化加密，counter默认都是0，不需要递增。
            self.write_data_to_NVM(addr, plaintext, 1)
        #测试预留，初始化加密完成以后，读取全内存密文查看，一开始的密文应该都是一样的，因为全内存为0，计数器也为0
        # i = 0
        # for addr in range(len(self.memory.data_memory_blocks)):
        #     ciphertext = self.memory.read_ciphertext(addr)
        #     #实验可知，密文长度也是64
        #     logging.debug(ciphertext + "({})({})".format(i, len(ciphertext)))
        #     i = i + 1


    '''    
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    #从NVM中读取密文数据，并解密为明文数据,然后将明文数据插入dataL2cache
    def read_data_from_NVM_to_cache(self, addr):
        dataHMAC_flag = False
        plaintext = ""
        E_index = 0
        #1.获取counter ,解密
        counter_addr = Utils.dataAddr_mapto_counterAddr(addr)
        logging.debug("开始获取counter")
        logging.debug("将data_addr:{}转换为counter_addr:{}".format(addr, counter_addr))
        major_counter, minor_counter = self.read_counter(counter_addr)
        logging.debug("成功获取counter，打印counter值如下：major counter:{}, minor counter:{}".format(major_counter, minor_counter))
        #获取密文
        ciphertext = self.memory.read_ciphertext(addr)
        logging.debug("从NVM中读取密文：{}".format(ciphertext))
        #获取dataHMAC
        dataHMAC_form_NVM = self.memory.read_dataHAMC(addr)
        logging.debug("从NVM中读取dataHMAC：{}".format(dataHMAC_form_NVM))
        logging.debug("开始进行dataHMAC验证...")
        #进行data HMAC验证（我的方案，data HMAC是基于密文计算的，所以解密之前进行验证）
        iv = str(ciphertext) + str(major_counter) + str(minor_counter) + str(addr)
        dataHMAC = Utils.hash_data(iv, "sha256")
        logging.debug("CPU计算dataHMAC：{}".format(dataHMAC))
        #对比dataHAMC
        if dataHMAC == dataHMAC_form_NVM:
            #不做处理
            logging.debug("dataHMAC验证通过...")
            dataHMAC_flag = True
            pass
        else:
            #报错处理
            logging.error("dataHMAC校验不通过，报错地址信息{}".format(addr))
            sys.exit(1)
        logging.debug("开始解密...")
        plaintext = self.encryption_engine.encrypt_or_decrypt(ciphertext, major_counter, minor_counter, addr)
        logging.debug("解密完成，明文信息为：{}".format(plaintext))
        logging.debug("开始将解密后的明文数据插入data缓存...")
        # 2.将从NVM获取的明文插入dataL2Cache中
        # 2.1查询是否有空余的缓存行，如果有，返回组set索引以及行索引，如果没有，使用LRU策略返回evition行索引
        is_found_idle_row, s_index, E_index = self.dataL2Cache.find_ERow_for_insert(addr)
        if is_found_idle_row:
            # 直接插入
            logging.debug("找到空闲行，将数据插入dataL2_cahce的第{}组，第{}行".format(s_index, E_index))
            self.dataL2Cache.insert_data(s_index, E_index, addr, plaintext)
            # 然后从缓存中返回给CPU，此处不做处理
        else:
            # 需要先驱逐E_index行上的东西再插入
            logging.debug("未找到空闲行，需要驱逐第{}组，第{}行，驱逐行当前dirty状态为：{}".format(s_index, E_index, self.dataL2Cache.sets[s_index].E_rows[E_index].dirty))
            if self.dataL2Cache.sets[s_index].E_rows[E_index].dirty:
                dirty_data_block = self.dataL2Cache.sets[s_index].E_rows[E_index].data_block
                #计算驱逐行地址。已知组索引以及tag，计算出物理地址，这个应该是从物理地址计算出s_index, E_index和tag的逆运算。
                evict_addr = self.dataL2Cache.caculate_eviction_addr(s_index, self.dataL2Cache.sets[s_index].E_rows[E_index].tag)
                self.write_data_to_NVM(evict_addr, dirty_data_block)
                logging.debug("将驱逐行的脏data_block写回data_addr:{}，脏data行内容为：{}".format(evict_addr, dirty_data_block))
            self.dataL2Cache.insert_data(s_index, E_index, addr, plaintext)
        logging.debug("数据插入缓存结束...")
        return dataHMAC_flag, plaintext, E_index

    '''    
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def read_counter(self, counter_addr):
        hit, E_index = self.counter_cache.lookup(counter_addr)
        if hit:
            logging.debug("counter缓存命中")
            major_counter, minor_counter = self.counter_cache.get_counter_incache(counter_addr, E_index)
        else:
            #1.从NVM中获取counter
            logging.debug("counter缓存未命中，从NVM中获取")
            major_counter, minor_counter, E_index = self.get_counter_from_NVM_to_cache(counter_addr)
        return major_counter, minor_counter

    '''    
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def get_counter_from_NVM_to_cache(self, counter_addr):
        # 1.从NVM中获取counter
        print(len(self.memory.counter_memory_blocks))
        counter_block, minor_counter_index = self.memory.get_counter(counter_addr, False)

        logging.debug("从NVM中获取的counter block内容如下：")
        logging.debug(counter_block.to_str())
        logging.debug("开始验证counter...")
        #完整性验证以后插入cache缓存行，循环读入counter在BMT上的父节点进行验证，直到根节点为止。
        print("开始验证counter。。。")
        if not self.counter_verify(counter_block, counter_addr, self.memory.BMT_height):
            logging.error("counter验证失败，失败地址为{}".format(counter_addr))
            sys.exit(0)
        logging.debug("counter验证通过...")
        logging.debug("开始将counter插入缓存...")
        # 2.counter验证通过后，将counter插入counter cache
        # 2.1 查询是否有空余的缓存行，如果有，返回组set索引以及行索引，如果没有，使用LRU策略返回eviction行索引
        is_found_idle_row, s_index, E_index = self.counter_cache.find_ERow_for_insert(counter_addr)
        if is_found_idle_row:
            # 直接插入
            logging.debug("找到空闲行，将counter block插入counter_cache的第{}组，第{}行".format(s_index, E_index))
            self.counter_cache.insert_counter(s_index, E_index, counter_addr, counter_block)
        else:
            # 需要先驱逐E_index行上的东西再插入
            logging.debug("未找到空闲行，将驱逐第{}组第{}行，驱逐行当前dirty标记为{}".format(s_index, E_index, self.counter_cache.sets[s_index].E_rows[E_index].dirty))
            if self.counter_cache.sets[s_index].E_rows[E_index].dirty:
                dirty_counter_block = self.counter_cache.set[s_index].E_rows[E_index].counter_block
                evict_addr = self.counter_cache.caculate_eviction_addr(s_index, self.counter_cache.set[s_index].E_rows[E_index].tag)
                self.memory.write_counter(evict_addr, dirty_counter_block)
                logging.debug("将驱逐行的脏counter_block写回counter_addr:{}，脏counter行内容为：{}".format(evict_addr, dirty_counter_block))
            self.counter_cache.insert_counter(s_index, E_index, counter_addr, counter_block)
        logging.debug("counter插入缓存结束...")
        major_counter = counter_block.major_counter
        minor_counter = counter_block.minor_counter_list[minor_counter_index]
        return major_counter, minor_counter, E_index

    '''    
        功能：height最低为2.
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def counter_verify(self, node, node_addr, height):
        print("寻找越界bug...")
        if type(node) == CounterMemoryBlock:
            print("验证子节点,子节点地址：{}， 子节点所在层的高度：{}".format(node_addr, height), node.to_str())
        elif type(node) == list:
            print("验证子节点,子节点地址：{}， 子节点所在层的高度：{}".format(node_addr, height), "".join(node))
        if height == self.memory.BMT_height:
            counter_flag = True
        else:
            counter_flag = False
        parent_node_addr = Utils.caculate_partentNode_addr(node_addr, height, counter_flag)
        print(parent_node_addr)
        hit, parent_node = self.read_BMT_node(parent_node_addr, height-1)
        print(parent_node)
        print("开始取父节点,父节点地址：{}， 父节点所在层的高度：{}".format(parent_node_addr, height - 1), "".join(parent_node))
        if hit:
            print("父节点缓存命中")
            res = self.compare_BMTnode(node, node_addr, parent_node)
            #测试保留
            # if not res:
            #     print("node验证失败，node地址为{}".format(node_addr))
            #     sys.exit()
            return res
        else:
            print("父节点缓存未命中， 开始迭代验证父节点，开始下一轮迭代")
            res = self.counter_verify(parent_node, parent_node_addr, height-1)
            if res:
                res = self.compare_BMTnode(node, node_addr, parent_node)
                #测试保留
                # if not res:
                #     print("node验证失败，node地址为{}".format(node_addr))
                #     sys.exit()
                return res

    '''
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def compare_BMTnode(self, child_node, node_addr, parent_node):
        flag = False
        print("比较两个node")
        print(child_node)
        print(node_addr)
        print(Utils.caculate_parentNode_addr_index(node_addr))
        parentNode_addr_index = Utils.caculate_parentNode_addr_index(node_addr)
        print(parent_node)
        #计算node的hash值
        if type(child_node) == list:
            nodeHMAC = Utils.hash_data("".join(child_node))
        else:
            nodeHMAC = Utils.hash_data(child_node.to_str())

        print(nodeHMAC)
        print(parent_node[parentNode_addr_index])
        if nodeHMAC == parent_node[parentNode_addr_index]:
            logging.debug("BMT树验证counter成功")
            flag = True
        if not flag:
            logging.error("BMT验证失败，失败节点地址为:{}".format(node_addr))
            sys.exit()
        return flag

    '''    
        功能：当height>1的时候，BMTnode是从BMTcache或者BMT memory block里面获取的，而当height ==1的时候，BMTnode也就是根节点，是从memory controller里面获取的。这个根是一直保存在芯片上，并且掉电不丢的。
        参数：BMT_addr, height
        返回值：hit, BMTnode
        作者：史文燕
        日期：2022
    '''
    def read_BMT_node(self, BMT_addr, height):
        hit_flag = False
        if height == 1:
            hit_flag = True
            return hit_flag, self.BMT_ROOT
        #如果需要取的不是根节点，就先查看缓存有没有命中
        hit, E_index = self.BMTCache.lookup(BMT_addr)
        if hit:
            #如果缓存命中，直接从缓存返回需要的BMT node，不需要验证，并且向上层的循环验证也可以终止
            hit_flag = True
            BMTnode = self.BMTCache.get_BMTnode_incache(BMT_addr, E_index)
        else:
            #将BMT block从NVM取出并插入到缓存中；
            BMTnode, E_index = self.get_BMTnode_from_NVM_to_cache(BMT_addr)
        return hit_flag, BMTnode

    '''    
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def get_BMTnode_from_NVM_to_cache(self, BMT_addr):
        # 如果缓存不命中，则从NVM中将该BMT node取进缓存，并验证；
        # 1.从NVM中获取BMT node
        BMT_node = self.memory.read_BMT_node(BMT_addr)
        # 2.查询是否有空余的缓存行，如果有，返回组set索引以及行索引，如果没有，使用LRU策略返回eviction行索引
        is_found_idle_row, s_index, E_index = self.BMTCache.find_ERow_for_insert(BMT_addr)
        if is_found_idle_row:
            # 直接插入
            self.BMTCache.insert_BMTnode(s_index, E_index, BMT_addr, BMT_node)
        else:
            # 需要先驱逐E_index行上的东西再插入
            if self.BMTCache.sets[s_index].E_rows[E_index].dirty:
                dirty_BMTnode = self.BMTCache.sets[s_index].E_rows[E_index].BMT_block
                evict_addr = self.BMTCache.caculate_eviction_addr(s_index, self.BMTCache.set[s_index].E_rows[E_index].tag)
                self.memory.write_BMT_node(BMT_addr, dirty_BMTnode)
                logging.debug("将驱逐行的脏BMTnode写回BMT_addr:{}，脏BMTnode内容为：{}".format(evict_addr, dirty_BMTnode))
            # 驱逐后插入
            self.BMTCache.insert_BMTnode(s_index, E_index, BMT_addr, BMT_node)

        return BMT_node, E_index

    '''    
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    #在缓存中更新counter值,该方法调用前必须调用read_counter方法。也即，如果被更新的counter不在缓存中，需要先读入缓存。
    def update_counter(self, counter_addr):
        #先lookup看是否缓存命中
        hit, E_index = self.counter_cache.lookup(counter_addr)
        if hit:
            #缓存命中时，根据返回的命中E_index,在缓存中直接更新counter值
            major_counter, minor_counter = self.update_counter_in_cache(counter_addr, E_index)
        else:
            #若是未命中，则需要将counter_addr对应的counter block从NVM中取入counter cache中以后，再在缓存中更新counter值。
            major_counter, minor_counter, E_index = self.get_counter_from_NVM_to_cache(counter_addr)
            #然后再执行”缓存中修改counter值“
            major_counter, minor_counter = self.update_counter_in_cache(counter_addr, E_index)
        return major_counter, minor_counter

    '''    
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def update_counter_in_cache(self,counter_addr, E_index):
        overflow, major_counter, minor_counter = self.counter_cache.update_counter_incache(counter_addr, E_index)
        # 如果溢出，需要进行重加密，重加密时需要对counter_addr所在的整个page进行重加密。
        if overflow:
            # 待完成
            pass
        return major_counter, minor_counter

    '''    
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def write_data_to_NVM(self, addr, plaintext, init_flag=False):
        #这里应该是先更新counter，更新发生在缓存中，更新完，返回major counter和minor counter（应该还没有只更新counter但不要counter的情形吧，
        #所以一般更新完counter都需要把Counter返回的。分析一下，更新counter只会出现在写Data的时候，所以更新完counter，必需要返回counter值。
        #1.获取counter，2.增加counter 3.使用新的counter计算出PAD 进而计算出密文 4.将密文写回到NVM
        if not init_flag:
            #更新缓存中的counter，并返回major counter和minor counter的值。（这里要注意如果更新的过程中溢出，那么返回的major counter和minor counter跟正常情形中是不一样的。）
            #正常的更新情况是major counter不变，minor counter +1，而溢出的情形是major counter+1,minor counter置为0。
            major_counter, minor_counter = self.update_counter(addr)
        else:
            #如果是初始化加密操作，则counter值不需要自增。
            major_counter = 0
            minor_counter = 0
        #使用新的counter加密数据以后写回NVM
        #logging.debug(plaintext)
        ciphertext = self.encryption_engine.encrypt_or_decrypt(plaintext, major_counter, minor_counter, addr)
        #logging.debug(plaintext)
        #logging.debug(ciphertext)
        # 计算data HMAC与data block一起写回去
        iv = str(ciphertext) + str(major_counter) + str(minor_counter) + str(addr)
        data_HMAC = Utils.hash_data(iv, "sha256")
        self.memory.write_ciphertext(ciphertext, addr)
        self.memory.write_dataHMAC(addr, data_HMAC)

    '''    
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def load_data(self, addr):
        logging.info("load({})...".format(addr))
        #先查看datal2Cache ,如果缓存命中，直接返回缓存中data
        hit, E_index = self.dataL2Cache.lookup(addr)
        if hit:
            #将数据取出来返回给CPU，我们这里不关注CPU的数据处理，所有不做处理即可
            plaintext = self.dataL2Cache.getData_Incache(addr, E_index)
            logging.debug("data缓存命中")
            logging.debug("将数据返回给CPU:{}".format(plaintext))
            logging.info("load({})成功...".format(addr))
            return True
        else:
            #1.缓存不命中，需要从NVM中将data取出来并解密
            logging.debug("data缓存未命中，从NVM中读取...")
            dataHMAC_flag, plaintext, E_index = self.read_data_from_NVM_to_cache(addr)
            if dataHMAC_flag:
                logging.debug("将数据返回给CPU:{}".format(plaintext))
                # 然后从缓存中返回给CPU，此处不做处理
                logging.info("load({})成功...".format(addr))
                return True
            else:
                logging.error("load({})失败...".format(addr))
                return False

    '''    
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022
    '''
    def store_data(self, addr, plaintext):
        logging.info("store({})...值{}".format(addr, plaintext))
        # 先lookup看是否缓存命中
        hit, E_index = self.dataL2Cache.lookup(addr)
        if hit:
            #缓存命中时，根据返回的命中E_index,在缓存中直接更新data_block值
            logging.debug("data缓存命中,直接在缓存中修改data...")
            self.dataL2Cache.update_data_incache(E_index, addr, plaintext)
            logging.info("store({})成功...".format(addr))
        else:
            #若是未命中，则需要将addr对应的data block从NVM中取入data L2 cache中以后，再在缓存中更新data值。
            logging.debug("data缓存未命中，从NVM中读取...")
            dataHMAC_flag, old_plaintext, E_index = self.read_data_from_NVM_to_cache(addr)
            if dataHMAC_flag:
                # 然后再执行”缓存中修改data block值“
                logging.debug("直接在缓存中修改data...")
                self.dataL2Cache.update_data_incache(addr, E_index, plaintext)
                logging.info("store({})成功...".format(addr))
            else:
                #校验不通过,store data失败
                logging.error("load({})失败...".format(addr))
                return False
        return True












