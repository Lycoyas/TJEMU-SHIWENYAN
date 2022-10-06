



class Statistics:
    @classmethod
    def stat_counters(cls, memory_size):
        memory_size = memory_size.Upper()
        memory_size_num = Statistics.str_to_num(memory_size)
        counters_overhead = ""
        if memory_size.find("K") != -1:
            if memory_size_num//64 >1 and memory_size_num//64 < 1024:
                counters_overhead = str(memory_size_num//64)

        elif memory_size.find("M") != -1:

            pass
        elif memory_size.find("G") != -1:
            pass
        elif memory_size.find("T") != -1:
            pass

    def str_to_num(cls, memory_size_str):
        for i in range(len(memory_size_str)):
            if memory_size_str[i].isdigit():
                continue
            else:
                return int(memory_size_str[:i])

    @classmethod
    def stat_BMT(cls, height):
        pass
        counter_overhead_size = 8**(height - 1)  * 64
        memory_size = counter_overhead_size * 64
        BMT_size = 0
        height -= 1
        while height > 1:
            BMT_size += 8 ** (height - 1) * 64
            height -= 1
        memory_size_KB = memory_size/(2**10)
        memory_size_MB = memory_size_KB / (2 ** 10)
        memory_size_GB = memory_size_MB / (2 ** 10)
        memory_size_TB = memory_size_GB / (2 ** 10)
        print(f"内存大小为：{memory_size}B,{memory_size_KB}KB,{memory_size_MB}MB,{memory_size_GB}GB,{memory_size_TB}TB")
        counter_oversize_KB = counter_overhead_size/(2**10)
        counter_oversize_MB = counter_oversize_KB/(2**10)
        counter_oversize_GB = counter_oversize_MB / (2 ** 10)
        counter_oversize_TB = counter_oversize_GB / (2 ** 10)
        print(f"counter的内存开销为：{counter_overhead_size}B,{counter_oversize_KB}KB,{counter_oversize_MB}MB,{counter_oversize_GB}GB,{counter_oversize_TB}TB")
        BMT_size_KB = BMT_size/(2**10)
        BMT_size_MB = BMT_size_KB / (2 ** 10)
        BMT_size_GB = BMT_size_MB / (2 ** 10)
        BMT_size_TB = BMT_size_GB / (2 ** 10)
        print(f"BMT的内存开销为：{BMT_size}B,{BMT_size_KB}KB,{BMT_size_MB}MB,{BMT_size_GB}GB,{BMT_size_TB}TB")


Statistics.stat_BMT(0)

