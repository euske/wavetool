#!/usr/bin/env python
#
# Sound picker
#
# usage: python pick.py [-b basepath] [-L left_window] [-R right_window] wav pitch ...
#

import sys
from wavestream import WaveReader
from wavestream import WaveWriter

def load_pitch(path):
    fp = open(path)
    for line in fp:
        line = line.strip()
        (line,_,_) = line.partition('#')
        if not line: continue
        (f, _, pitch) = line.partition(' ')
        yield (int(f), int(pitch))
    fp.close()
    return

def pick_frames(triggers, w0=0, w1=0):
    (f0,f1) = (None,None)
    for t in triggers:
        if f0 is None:
            f0 = t-w0
            f1 = t+w1
        elif f1 <= t-w0:
            yield (f0, f1)
            f0 = t-w0
            f1 = t+w1
        else:
            f1 = max(f1, t+w1)
    if f0 is not None:
        yield (f0, f1)
    return
    
def main(argv):
    import getopt
    def usage():
        print 'usage: %s [-b basepath] [-L left_window] [-R right_window] src.wav pitch ...' % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'b:L:R:')
    except getopt.GetoptError:
        return usage()
    basepath = 'out%05d.wav'
    window0 = 0.1
    window1 = 0.1
    for (k,v) in opts:
        if k == '-b': basepath = v
        elif k == '-L': window0 = float(v)
        elif k == '-R': window1 = float(v)
    if not args: return usage()
    wavpath = args.pop(0)
    src = WaveReader(wavpath)
    w0 = int(window0*src.framerate)
    w1 = int(window1*src.framerate)
    
    i = 0
    for path in args:
        triggers = ( t for (t,_) in load_pitch(path) )
        for (f0,f1) in pick_frames(triggers, w0, w1):
            f0 = max(0, f0)
            f1 = min(f1, src.nframes)
            src.seek(f0)
            (nframes, data) = src.readraw(f1-f0)
            outpath = basepath % i
            print outpath, (f0,f1)
            out = open(outpath, 'wb')
            dst = WaveWriter(out,
                             nchannels=src.nchannels,
                             sampwidth=src.sampwidth,
                             framerate=src.framerate,
                             nframes=nframes)
            dst.writeraw(data)
            dst.close()
            out.close()
            i += 1
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv))
