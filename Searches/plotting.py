import optparse
import sys
from aStar import AStar
import matplotlib
matplotlib.use('Agg')
from pylab import *

# Class that parses a file and plots several graphs
class Plotter:
    def __init__(self,file):
        """ Initialize plotter with a file name. """
        self.file = file
        self.time = []
        self.m = []

    def parse(self):
        """ Parse the data file and accumulate values for the time,
            download time, and size columns.
        """
        first = None

        file = open(self.file, "r")

        self.time.append(0)
        self.m.append(0)
        
        for line in file.readlines():
            if line.startswith("#"):
                continue
            try:
                m,time = line.split()
                #print time
                #s = raw_input(m)
                # 0:01:30.079064
                h,mt,sms = time.split(":")
                s, ms = sms.split(".")
            except:
                continue
            
            m = float(m)
            mtime = float(int(ms) + 1000 * int(s) + 60000 * int(mt) + 3600000 * int(h))
            mtime = mtime / 1000
            

            self.time.append(mtime)
            self.m.append(m)

        print "Multiplier: ",self.m, "\n"
        print "Time: ", self.time, "\n"
        

    def downloadplot(self):
        """ Create a line graph of download time versus experiment time. """
        print "plotting file"
        clf()
        plot(self.m,self.time)
        xlabel('Heuristic Multiplier')
        ylabel('Run Time')
        savefig('download-line.png')

    def run_tests(self):

        file = open(self.file, "w")

        inc = 1
        a = AStar()
        for i in range(5):
            time = a.run(i * inc)
            print str(i * inc) + " " + str(time)
            file.write(str(i * inc) + " " + str(time) + "\n")

        file.close()


if __name__ == "__main__":

    
    plotter = Plotter("hstic.txt")
    plotter.run_tests()
    plotter.parse()
    plotter.downloadplot()