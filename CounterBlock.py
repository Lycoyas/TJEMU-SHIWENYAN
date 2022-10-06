
class CounterMemoryBlock():
    def __init__(self):
        self.major_counter = 0
        self.minor_counter_list = [0]*64

    def to_str(self):
        res = ""
        for i in range(64):
            res += str(self.minor_counter_list[i])
        res += str(self.major_counter)
        return res
