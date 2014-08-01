#!/usr/bin/env python
import sys
import matplotlib.pyplot as plt

def flush(p):
    plt.plot([ x for (x,_) in p ], [ y for (_,y) in p ], 'o')
    return

def main(argv):
    import fileinput
    p = []
    for line in fileinput.input():
        line = line.strip()
        if not line:
            flush(p)
            p = []
        else:
            (f1,_,f2) = line.partition(' ')
            p.append((int(f1), int(f2)))
    flush(p)
    plt.show()
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv))
