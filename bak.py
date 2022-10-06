import base64
from Crypto.Cipher import AES
from utils import Utils
#定义全局变量
# iv是初始化向量，第一组明文就是用它加密的
#
# key是密钥，这里选择的长度是128比特，所以字符串的长度要固定在16字节。
#
# data就是需要加密的数据
iv = '1234567887654321'
key = 'miyaoxuyao16ziji'
data = 'hello world'

#编写加密函数
#AES的区块固定是128比特，也就是16字节，所以一开始要先判断明文是否小于16字节，如果小于16字节，需要补齐，为此要写一个补齐的函数。
def pad(data):
    pad_data = data
    for i in range(0,16-len(data)):
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
    # 用base64编码一下
    AES_en_str = base64.b64encode(AES_en_str)
    # 最后将密文转化成字符串
    AES_en_str = AES_en_str.decode("utf-8")
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
print(data)
print(len(data))
data = AES_en(key, data)
print(data)
print(len(data))
data = AES_de(key, data)
print(data)


#####****************************************************************************************************************************
'''    
        功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
        参数：s_index, E_index, counter_addr, counter_block
        返回值：None
        作者：史文燕
        日期：2022.09.23
    '''
def counter_verify(self, counter_addr, counter_block):
    #BMT树的高度为height
    height = self.memory.BMT_height
    #先根据counter_addr换算出counter父节点在BMT上的地址
    #根据第k层的counter地址，计算出第k-1层对应的BMTnode的地址
    BMT_addr_k1 = Utils.counterAddr_mapto_BMTAddr(counter_addr)
    #根据BMTnode地址取出BMTnode，如果该BMTnode缓存命中，则不需要进行验证，否则该BMTnode也需要先进行验证
    hit, BMT_node_k1 = self.read_BMT_node(BMT_addr_k1)
    if hit:
        #省略验证步骤，且可以当做根，剩下的迭代验证过程到此为止
        #用该BMTnode验证counter
        pass
    else:
        #如果缓存不命中，那么就需要第K-1层的BMT node进行验证，也就是取进k-2层的父节点来验证第k-1层的子节点
        #首先，根据第k-1层BMTnode的地址，计算出第k-1层父节点的地址
        BMT_addr_k2 = Utils.caculate_partentNode_addr(BMT_node_k1, height-2)
        #重复上面针对第k-1层node的操作，根据地址，取进对应的node，如果命中，不验证，且直接返回，若不命中，需要继续取父节点进行验证，此过程直到根为止
        hit, BMT_node_k2 = self.read_BMT_node(BMT_addr_k2)
        if hit:
            # 省略验证步骤，且可以当做根，剩下的迭代验证过程到此为止
            # 用该BMTnode验证k-1层node
            pass
        else:
            # 如果缓存不命中，那么就需要第K-3层的BMT node进行验证，也就是取进k-3层的父节点来验证第k-2层的子节点
            pass

    pass

'''    
    功能：根据找到的空闲行索引，将从NVM中取到的counter_block插入到相应的缓存行。
    参数：s_index, E_index, counter_addr, counter_block
    返回值：None
    作者：史文燕
    日期：2022.10.03
'''
def test(self, BMT_parent_node_addr, BMT_child_node, height):
    flag = False
    #根节点永远在芯片上，不需要验证，直接返回
    if height == 1:
        flag = True
        return flag
    hit, BMT_parent_node = self.read_BMT_node(BMT_parent_node_addr)
    if hit:
        # 省略验证步骤，且可以当做根，剩下的迭代验证过程到此为止
        # 用该BMTnode验证k-1层node
        flag = self.compare_BMTnode(BMT_child_node, BMT_parent_node)
    else:
        # 如果缓存不命中，那么就需要第K-3层的BMT node进行验证，也就是取进k-3层的父节点来验证第k-2层的子节点
        #先计算K-3的node地址
        BMT_parnet_parent_node_addr = Utils.caculate_partentNode_addr(BMT_parent_node_addr, height-1)
        flag = self.test(BMT_parnet_parent_node_addr, BMT_parent_node)
    return flag, BMT_parent_node
###############**************************************************************************************************************
# 第一种创建counter_block的方式是用numpy数组
# counter_block_type = np.dtype([("major_counter", np.int64),("minor_counter1", np.int8),("minor_counter2", np.int8),("minor_counter3", np.int8),("minor_counter4", np.int8),("minor_counter5", np.int8),("minor_counter6", np.int8),("minor_counter7", np.int8),("minor_counter8", np.int8),("minor_counter9", np.int8),("minor_counter10", np.int8),("minor_counter11", np.int8),("minor_counter12", np.int8),("minor_counter13", np.int8),("minor_counter14", np.int8),("minor_counter15", np.int8),("minor_counter16", np.int8),("minor_counter17", np.int8),("minor_counter18", np.int8),("minor_counter19", np.int8),("minor_counter20", np.int8),("minor_counter21", np.int8),("minor_counter22", np.int8),("minor_counter23", np.int8),("minor_counter24", np.int8),("minor_counter25", np.int8),("minor_counter26", np.int8),("minor_counter27", np.int8),("minor_counter28", np.int8),("minor_counter29", np.int8),("minor_counter30", np.int8),("minor_counter31", np.int8),("minor_counter32", np.int8),("minor_counter33", np.int8),("minor_counter34", np.int8),("minor_counter35", np.int8),("minor_counter36", np.int8),("minor_counter37", np.int8),("minor_counter38", np.int8),("minor_counter39", np.int8),("minor_counter40", np.int8),("minor_counter41", np.int8),("minor_counter42", np.int8),("minor_counter43", np.int8),("minor_counter44", np.int8),("minor_counter45", np.int8),("minor_counter46", np.int8),("minor_counter47", np.int8),("minor_counter48", np.int8),("minor_counter49", np.int8),("minor_counter50", np.int8),("minor_counter51", np.int8),("minor_counter52", np.int8),("minor_counter53", np.int8),("minor_counter54", np.int8),("minor_counter55", np.int8),("minor_counter56", np.int8),("minor_counter57", np.int8),("minor_counter58", np.int8),("minor_counter59", np.int8),("minor_counter60", np.int8),("minor_counter61", np.int8),("minor_counter62", np.int8),("minor_counter63", np.int8),("minor_counter64", np.int8)])
# memory_list = np.zeros(10000000,dtype= counter_block_type)
# print(memory_list)
# 第二种创建counter_block的方式是使用list，我们使用的是第二种list的方式。