#!/usr/bin/env python
#
# usage: python match.py wav pitch ...
#

import sys
import wavcorr
from wavestream import WaveReader


##  WaveMatcher
##
class WaveMatcher(object):

    def __init__(self, threshold=0.6):
        self.threshold = threshold
        self.pats = []
        return

    def load_pat(self, path, name=None):
        fp = WaveReader(path)
        (_, pat) = fp.readraw()
        self.pats.append((name or path, pat))
        fp.close()
        return

    def load_wav(self, wavpath, pitchpath):
        src = WaveReader(wavpath)
        fp = open(pitchpath)
        for line in fp:
            line = line.strip()
            if not line:
                print
            (line,_,_) = line.partition('#')
            if not line: continue
            (f, _, pitch) = line.partition(' ')
            f = int(f)
            pitch = int(pitch)
            src.seek(f)
            r = []
            (nframes, data) = src.readraw(int(src.framerate/pitch))
            for (name,pat) in self.pats:
                s = wavcorr.matchs16(pat, 0, nframes, data)
                if self.threshold <= s:
                    r.append((s, name))
            if r:
                r.sort(reverse=True)
                print f, ' '.join( '%.04f:%s' % (s,name) for (s,name) in r )
        fp.close()
        src.close()
        return


# main
def main(argv):
    import getopt
    def usage():
        print 'usage: %s [-t threshold] src.wav pitch pat.wav ...' % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 't:')
    except getopt.GetoptError:
        return usage()
    threshold = 0.6
    for (k,v) in opts:
        if k == '-t': threshold = float(v)
    if not args: return usage()
    wavpath = args.pop(0)
    if not args: return usage()
    pitchpath = args.pop(0)

    matcher = WaveMatcher(threshold=threshold)
    for path in args:
        matcher.load_pat(path)

    matcher.load_wav(wavpath, pitchpath)
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
