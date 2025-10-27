import time

class TimePerf:
    num = 0
    total_time = time.perf_counter()
    all_active = True
    def __init__(self, name = "Default", auto = False):
        self.name = name
        self.auto = auto
        if auto:
            self.start_time = time.perf_counter()
        else:
            self.start_time = 0
        self.end_time = 0
        TimePerf.num += 1

    def startTick(self):
        self.start_time = time.perf_counter()

    def endTick(self, clear_start_time = False):
        self.end_time = time.perf_counter() - self.start_time
        if clear_start_time:
            self.start_time = time.perf_counter()
        print(f"Time taken by {self.name}: {self.end_time} seconds")

    def __del__(self):
        #print (TimePerf.num)
        if self.auto:
            self.end_time = time.perf_counter() - self.start_time
            print(f"Time taken by {self.name}: {self.end_time} seconds")
        TimePerf.num -= 1
        if TimePerf.num == 0:
            TimePerf.total_time = time.perf_counter() - TimePerf.total_time
            print(f"Total time taken by {self.name}: {TimePerf.total_time} seconds")


def main():
    timer1 = TimePerf()
    timer1.startTick()
    print("goo gaa")
    time.sleep(2)
    timer1.endTick()

    timer2 = TimePerf()
    timer2.startTick()
    time.sleep(3)
    timer2.endTick()
    time.sleep(5)
    
if __name__ == "__main__":
    main()
