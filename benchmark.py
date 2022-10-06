# -*- coding: UTF-8 -*-
import GlobalConfig
from numpy import int64
from MemoryController import MemoryController
import numpy as np
from Memory import Memory
import logUtils
import logging
import datetime







class Benchmark:
    def __init__(self):
        self.memory_controller = MemoryController()  # 只用初始化内存控制器，剩下的部件交给内存控制器去发起初始化就可以了。

    # 从trace文件中读取访存命令，开始一步一步执行
    def benchmark1(self):
        #后续benchmarks路径做成参数可配置的，放在config.ini文件中
        file_object2 = open("D:\project\PythonProject\\benchmarks\\benchmark1.txt", encoding='utf-8')
        try:
            lines = file_object2.readlines()
            for line in lines:
                if line.startswith("#"):
                    continue
                elif line.find("load") != -1:
                    self.memory_controller.load_data(int(line.split(" ")[1]))
                elif line.find("store") != -1:
                    self.memory_controller.store_data(int(line.strip().split(" ")[1]), line.strip().split(" ")[2])

        finally:
            file_object2.close()
        pass

    def benchmark2(self):
        # self.memory_controller.load_data(0)#缓存不命中，明文全0
        # #newdata = "0000000000000000000000000000000000000000000000000000000000000001"
        # newdata = '1'
        # self.memory_controller.store_data(0, newdata)
        # self.memory_controller.load_data(0)#缓存命中，但明文变化
        # self.memory_controller.load_data(1)#缓存命中
        # self.memory_controller.load_data(63)#缓存命中
        # self.memory_controller.load_data(64)#缓存不命中
        # self.memory_controller.load_data(65)#缓存命中
        # self.memory_controller.load_data(512)  #缓存命中
        self.memory_controller.load_data(0)#未命中
        self.memory_controller.load_data(2**15)#未命中

        pass


if __name__ == '__main__':
    # 初始化全局变量
    GlobalConfig.init_global()
    benchmark = Benchmark()

    # logging.info("开始运行benchmark1...")
    # starttime = datetime.datetime.now()
    # benchmark.benchmark1()
    # endtime = datetime.datetime.now()
    # logging.debug("benchmark1耗时：{}".format((endtime - starttime)))

    logging.info("开始运行benchmark1...")
    starttime = datetime.datetime.now()
    benchmark.benchmark2()
    endtime = datetime.datetime.now()
    logging.debug("benchmark1耗时：{}".format((endtime - starttime)))

# counter cache block的数据结构，1个major counter block，64个7bit的minor counter
