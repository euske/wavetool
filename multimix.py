#!/usr/bin/env python
#
# usage: python multimix.py [-o out.wav] src.wav [script ...]
#
# script (columns delimited by a tab)
#   0.00        1.00    sound1.wav
#   0.50        -       sound2.wav
#   ...
#

import sys
from wavestream import WaveReader
from wavestream import WaveWriter
from wavestream import PygameWavePlayer as WavePlayer

def mix(bufs):
    n = len(bufs)
    return [ sum(row)/n for row in zip(*bufs) ]

# main
def main(argv):
    import getopt
    import fileinput
    def usage():
        print 'usage: %s [-v] [-o out.wav] [script ...]' % argv[0]
        return 100
    def getv(v):
        try:
            if '.' in v:
                return float(v)
            else:
                return int(v)
        except ValueError:
            return 0
    try:
        (opts, args) = getopt.getopt(argv[1:], 'vo:')
    except getopt.GetoptError:
        return usage()
    verbose = 0
    outfp = None
    for (k, v) in opts:
        if k == '-v': verbose += 1
        elif k == '-o': outfp = open(v, 'wb')
    #
    if not args: return usage()
    path = args.pop(0)
    src = WaveReader(path)
    #
    waves = []
    for line in fileinput.input(args):
        (line,_,_) = line.partition('#')
        line = line.strip()
        if not line: continue
        (t,dur,path) = line.split('\t')
        t = getv(t)
        dur = getv(dur)
        wav = WaveReader(path)
        assert wav.nchannels == src.nchannels
        assert wav.sampwidth == src.sampwidth
        #assert wav.framerate == src.framerate
        if isinstance(t, float):
            t = int(t*src.framerate)
        if isinstance(dur, float):
            dur = int(dur*src.framerate)
        buf = wav.read(dur)
        wav.close()
        waves.append((t, buf))
    waves.append((src.nframes, []))
    #
    if outfp is not None:
        dst = WaveWriter(outfp,
                         nchannels=src.nchannels,
                         sampwidth=src.sampwidth,
                         framerate=src.framerate)
    else:
        dst = WavePlayer(nchannels=src.nchannels,
                         sampwidth=src.sampwidth,
                         framerate=src.framerate)
    #
    t0 = 0
    bufs = []
    for (t1,buf1) in sorted(waves, key=lambda (t,_): t):
        dt = (t1-t0)*dst.nchannels
        tmp = [src.read(t1-t0)]
        assert len(tmp[0]) == dt
        for (i,b) in enumerate(bufs):
            if dt <= len(b):
                tmp.append(b[:dt])
            else:
                tmp.append(b+[0]*(dt-len(b)))
            bufs[i] = b[dt:]
        bufs.append(buf1)
        bufs = [ b for b in bufs if b ]
        dst.write(mix(tmp))
        t0 = t1
    #
    dst.close()
    if outfp is not None:
        outfp.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
