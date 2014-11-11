#!/usr/bin/env python
#
# Streak picker
#
# usage: python pick.py [-b base_name] [-w outer_window] [-W inner_window] wav pitch ...
#

import sys
from wavestream import WaveReader

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

def pick_streaks(triggers, w0=0, w1=0):
    (f0,f1) = (None,None)
    for t in triggers:
        if f1 is None:
            f0 = t
        elif f1 <= t-w1:
            yield (f0-w0, f1+w0)
            f0 = t
        f1 = t
    if f0 is not None and f1 is not None:
        yield (f0-w0, f1+w0)
    return
    
def main(argv):
    import getopt
    def usage():
        print ('usage: %s [-b base_name]'
               ' [-w outer_window] [-W inner_window]'
               ' src.wav pitch ...' % argv[0])
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'b:w:W:')
    except getopt.GetoptError:
        return usage()
    base = 'out'
    window0 = 0.1
    window1 = 0.1
    for (k,v) in opts:
        if k == '-b': base = v
        elif k == '-w': window0 = float(v)
        elif k == '-W': window1 = float(v)
    if not args: return usage()
    wavpath = args.pop(0)
    src = WaveReader(wavpath)
    w0 = int(window0*src.framerate)
    w1 = int(window1*src.framerate)
    
    i = 0
    for path in args:
        triggers = ( t for (t,_) in load_pitch(path) )
        for (f0,f1) in pick_streaks(triggers, w0, w1):
            f0 = max(0, f0)
            f1 = min(f1, src.nframes)
            print '%s%04d %d %d' % (base, i, f0, f1)
            i += 1
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv))
