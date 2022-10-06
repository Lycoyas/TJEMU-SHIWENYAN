import base64
from Crypto.Cipher import AES
import logUtils


class EncryptionEngine:
    def __init__(self, iv, key):
        self.iv = iv
        self.key = key

    #使用addr和counter，AES加密计算出PAD，再与plaintext异或计算出密文。后续如果预留加密延时出来，可以以增加标志位的形式标记是加密还是解密，加密有延时，但是解密是没有延时的。
    def encrypt_or_decrypt(self, plain_or_ciphertext, major_counter,minor_counter, addr):

        pad = self.gen_pad(major_counter, minor_counter, addr)
        plain_or_ciphertext = self.xor_pad(pad, plain_or_ciphertext)
        return plain_or_ciphertext


    # #用不上
    # def decrypt(self,ciphertext, major_counter,minor_counter, addr):
    #     pad = self.gen_pad(major_counter,minor_counter, addr)
    #     plaintext =  self.xor_pad(pad, ciphertext)
    #     return plaintext




    def gen_pad(self, major_counter, minor_counter, addr):
        seed = (str(major_counter) + str(minor_counter) + str(addr)).zfill(64)
        pad = self.AES_en(self.key, seed)
        return pad

    # def verify_dataHMAC(self, ciphertext):
    #
    #     pass
    #
    # def verify_BMT(self, addr):
    #     pass
    #
    # def update_BMT(self, addr):
    #     pass

    # AES的区块固定是128比特，也就是16字节，所以一开始要先判断明文是否小于16字节，如果小于16字节，需要补齐，为此要写一个补齐的函数。
    #是不是也可以直接用str.zfill(64)直接将data补齐为64字节，这样密文和明文至少可以长度一致。
    def pad(data):
        pad_data = data
        for i in range(0, 16 - len(data)):
            pad_data = pad_data + ' '
        return pad_data
    #明文转密文，或者密文转明文
    def xor_pad(self, pad, data):
        data_bytes = (data.zfill(64)).encode("utf-8")
        pad = pad.encode("utf-8")
        result = b''
        for bytes1, bytes2 in zip(pad, data_bytes):
            result += bytes([bytes1 ^ bytes2])
        return str(result, encoding = "utf8")



    # 创建AES加密对象
    # 用创建好的加密对象，对明文进行加密
    # 把加密好的密文用base64编码
    # 把字符串解码成字符串
    def AES_en(self, key, data):
        # 将长度不足16字节的字符串补齐
        if len(data) < 16:
            data = self.pad(data)
        # 创建加密对象
        AES_obj = AES.new(key.encode("utf-8"), AES.MODE_CBC, self.iv.encode("utf-8"))
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

    def AES_de(self, key, data):
        # 解密过程逆着加密过程写
        # 将密文字符串重新编码成二进制形式
        data = data.encode("utf-8")
        # 将base64的编码解开
        data = base64.b64decode(data)
        # 创建解密对象
        AES_de_obj = AES.new(key.encode("utf-8"), AES.MODE_CBC, self.iv.encode("utf-8"))
        # 完成解密
        AES_de_str = AES_de_obj.decrypt(data)
        # 去掉补上的空格
        AES_de_str = AES_de_str.strip()
        # 对明文解码
        AES_de_str = AES_de_str.decode("utf-8")
        return AES_de_str
