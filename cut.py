#!/usr/bin/env python
#
# usage: python cut.py [-o out.wav] [-t from,to] wav ...
#

import sys


# main
def main(argv):
    import getopt
    from wavestream import WaveReader
    from wavestream import WaveWriter
    def usage():
        print 'usage: %s [-o out.wav] [-f f0-f1] wav ...' % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'o:f:')
    except getopt.GetoptError:
        return usage()
    outfp = None
    ranges = []
    for (k, v) in opts:
        if k == '-o': outfp = open(v, 'wb')
        elif k == '-f':
            (f0,_,f1) = v.partition('-')
            ranges.append((int(f0), int(f1)))
    if outfp is None:
        dst = WaveWriter(sys.stdout)
    else:
        dst = WaveWriter(outfp)
    for path in args:
        src = WaveReader(path)
        for (f0,f1) in ranges:
            src.seek(f0)
            if f1 < f0:
                f1 = src.nframes
            (_,buf) = src.readraw(f1-f0)
            dst.writeraw(buf)
        src.close()
    dst.close()
    if outfp is not None:
        outfp.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
