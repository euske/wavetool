#!/usr/bin/env python
#
# usage: python match.py wav pitch ...
#

import sys
import wavcorr


# main
def main(argv):
    import getopt
    from wavestream import WaveReader
    def usage():
        print 'usage: %s src.wav pitch pat.wav ...' % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], '')
    except getopt.GetoptError:
        return usage()
        
    if not args: return usage()
    path = args.pop(0)
    src = WaveReader(path)
    
    if not args: return usage()
    pitches = []
    fp = open(args.pop(0))
    for line in fp:
        line = line.strip()
        if not line: continue
        (f, _, pitch) = line.partition(' ')
        pitches.append((int(f), int(pitch)))
    fp.close()

    pats = []
    for path in args:
        pat = WaveReader(path)
        pats.append((path, pat.readraw()))
        pat.close()

    for (f, pitch) in pitches:
        src.seek(f)
        (nframes, data) = src.readraw(int(src.framerate/pitch))
        for (name,(_,pat)) in pats:
            s = wavcorr.matchs16(pat, 0, nframes, data)
            print f, s, name
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
