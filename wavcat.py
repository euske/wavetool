#!/usr/bin/env python
#
# usage: python wavcat.py [-o out.wav] [-t from-to] wav ...
#

import sys
from wavestream import WaveReader
from wavestream import WaveWriter
from wavestream import PygameWavePlayer as WavePlayer


# main
def main(argv):
    import getopt
    def usage():
        print 'usage: %s [-o out.wav] [-t f0-f1] wav ...' % argv[0]
        return 100
    def getv(v):
        if '.' in v:
            return float(v)
        else:
            return int(v)
    try:
        (opts, args) = getopt.getopt(argv[1:], 'o:t:')
    except getopt.GetoptError:
        return usage()
    outfp = None
    ranges = []
    for (k, v) in opts:
        if k == '-o': outfp = open(v, 'wb')
        elif k == '-t':
            (f0,_,f1) = v.partition('-')
            ranges.append((getv(f0), getv(f1)))
    dst = None
    for path in args:
        src = WaveReader(path)
        if dst is None:
            if outfp is None:
                dst = WavePlayer(nchannels=src.nchannels,
                                 sampwidth=src.sampwidth,
                                 framerate=src.framerate)
            else:
                dst = WaveWriter(outfp,
                                 nchannels=src.nchannels,
                                 sampwidth=src.sampwidth,
                                 framerate=src.framerate)
        for (f0,f1) in ranges:
            if isinstance(f0, float):
                f0 = int(f0*src.framerate)
            if isinstance(f1, float):
                f1 = int(f1*src.framerate)
            src.seek(f0)
            if f1 < f0:
                f1 = src.nframes
            (_,buf) = src.readraw(f1-f0)
            dst.writeraw(buf)
        src.close()
    if dst is not None:
        dst.close()
    if outfp is not None:
        outfp.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
