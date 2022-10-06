import logging
#此日志采用追加模式写log，会保留历史日志，如果想每次启动建立新的日志，那么可以采用时间戳拼接文件名，要么就是在下面指定filemode = 'w'
#另外后续也可以使用配置文件来决定日志分级显示
logging.basicConfig(filename="test.log", level=logging.DEBUG, format='%(asctime)s:%(module)s :%(message)s')

#也能直接打印数组
# list_test = {1,2,3}
# logging.debug(list_test)

# list1 = ["a", "b", "c"]
# print("".join(list1))