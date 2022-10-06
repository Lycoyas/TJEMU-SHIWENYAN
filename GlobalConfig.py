from configparser import ConfigParser
#定义全局变量
#[labtency]
encryption_latency = 0
meta_hit_latency = 0
memory_read_latency = 0
memory_write_latency = 0
#[memory]
memory_size = 0


#[AES]
iv = 0
AES_key = 0

#[counter_cache]
counter_cache_E = 0
counter_cache_S = 0
counter_cache_B = 64

#[data_l2_cache]
data_l2_cache_E = 0
data_l2_cache_S = 0
data_l2_cache_B = 64

#[BMT_cache]
BMT_cache_E = 0
BMT_cache_S = 0
BMT_cache_B = 64



def init_global():
    config_parser = ConfigParser()
    config_parser.read("config.ini")

    #[latency]
    global encryption_latency
    global meta_hit_latency
    global memory_read_latency
    global memory_write_latency
    encryption_latency = config_parser.get("latency", "encryption_latency")
    meta_hit_latency = config_parser.get("latency", "meta_hit_latency")
    memory_read_latency = int(eval(config_parser.get("latency", "memory_read_latency")))
    memory_write_latency = int(eval(config_parser.get("latency", "memory_write_latency")))

    #[memory]
    global memory_size
    memory_size = int(eval(config_parser.get("memory", "size")))

    #[AES]
    global iv
    global AES_key
    iv = config_parser.get("AES", "iv")
    AES_key = config_parser.get("AES", "key")

    # [counter_cache]
    global counter_cache_E
    global counter_cache_S
    global counter_cache_B
    counter_cache_E = int(eval(config_parser.get("counter_cache", "counter_cache_E")))
    counter_cache_S = int(eval(config_parser.get("counter_cache", "counter_cache_S")))
    counter_cache_B = int(eval(config_parser.get("counter_cache", "counter_cache_B")))

    # [data_l2_cache]
    global data_l2_cache_E
    global data_l2_cache_S
    global data_l2_cache_B
    data_l2_cache_E = int(eval(config_parser.get("data_l2_cache", "data_l2_cache_E")))
    data_l2_cache_S = int(eval(config_parser.get("data_l2_cache", "data_l2_cache_S")))
    data_l2_cache_B = int(eval(config_parser.get("data_l2_cache", "data_l2_cache_B")))

    # [BMT_cache]
    global BMT_cache_E
    global BMT_cache_S
    global BMT_cache_B
    BMT_cache_E = int(eval(config_parser.get("data_l2_cache", "data_l2_cache_E")))
    BMT_cache_S = int(eval(config_parser.get("data_l2_cache", "data_l2_cache_S")))
    BMT_cache_B = int(eval(config_parser.get("data_l2_cache", "data_l2_cache_B")))


