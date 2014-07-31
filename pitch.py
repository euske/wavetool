#!/usr/bin/env python
#
# Pitch detector
#
# usage: python pitch.py [-M|-F] [-n pitchmin] [-m pitchmax] [-t threshold_sim] wav ...
#

import sys
import wavcorr
from math import sqrt


##  PitchDetector
##
class PitchDetector(object):

    def __init__(self, framerate, pitchmin=70, pitchmax=400):
        self.framerate = framerate
        self.wmin = (framerate/pitchmax)
        self.wmax = (framerate/pitchmin)
        self.reset()
        return

    def reset(self):
        self._buf = ''
        self._nframes = 0
        return
    
    def feed(self, buf, nframes):
        self._buf += buf
        self._nframes += nframes
        i = 0
        n = self.wmin/2
        while i+self.wmax < self._nframes:
            (dmax, mmax) = wavcorr.autocorrs16(self.wmin, self.wmax, self._buf, i)
            pitch = self.framerate/dmax
            mag = wavcorr.calcmags16(self._buf, i, dmax)
            yield (n, mmax, pitch, mag, self._buf[i*2:(i+n)*2])
            i += n
        self._buf = self._buf[i*2:]
        self._nframes -= i
        return


##  PitchSmoother
##
class PitchSmoother(object):

    def __init__(self, framerate, durmin=0.01, varmax=100.1):
        self.framerate = framerate
        self.durframes = int(durmin * framerate)
        self.varmax = varmax
        self._samples = []
        return

    def feed(self, nframes, freq):
        self._samples.insert(0, (nframes, freq))
        (f1,f2,total) = (0, 0, 0)
        for (i,(n,f)) in enumerate(self._samples):
            f1 += f*n
            f2 += f*f*n
            total += n
            if self.durframes < total:
                self._samples = self._samples[:i+1]
                break
        if total == 0 or f1 == 0: return 0
        avg = f1/float(total)
        vari = sqrt(f2/float(total)-avg*avg)/avg
        if self.varmax < vari: return 0
        return avg


# main
def main(argv):
    import getopt
    from wavestream import WaveReader
    def usage():
        print 'usage: %s [-M|-F] [-n pitchmin] [-m pitchmax] [-t threshold] wav ...' % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'MFn:m:t:')
    except getopt.GetoptError:
        return usage()
    pitchmin = 70
    pitchmax = 400
    threshold_sim = 0.9
    threshold_mag = 0.01
    bufsize = 10000
    import matplotlib.pyplot as plt
    for (k, v) in opts:
        if k == '-M': (pitchmin,pitchmax) = (75,200) # male voice
        elif k == '-F': (pitchmin,pitchmax) = (150,300) # female voice
        elif k == '-n': pitchmin = int(v)
        elif k == '-m': pitchmax = int(v)
        elif k == '-t': threshold_sim = float(v)
    detector = None
    smoother = None
    for path in args:
        src = WaveReader(path)
        if src.nchannels != 1: raise ValueError('invalid number of channels')
        if src.sampwidth != 2: raise ValueError('invalid sampling width')
        if detector is None:
            detector = PitchDetector(src.framerate,
                                     pitchmin=pitchmin, pitchmax=pitchmax)
            smoother = PitchSmoother(src.framerate)
        i = 0
        r = []
        while 1:
            (nframes,buf) = src.readraw(bufsize)
            if not nframes: break
            pitches = detector.feed(buf, nframes)
            for (n,t,freq,mag,data) in pitches:
                if threshold_sim <= t and threshold_mag <= mag:
                    #print i,n,t,freq,mag
                    sfreq = smoother.feed(n, freq)
                else:
                    #print i,n,t
                    sfreq =  smoother.feed(n, 0)
                if sfreq:
                    r.append((i, sfreq))
                    print i, sfreq
                i += n
        src.close()
        if plt is not None:
            plt.plot([ x for (x,_) in r ], [ y for (_,y) in r ], 'o')
            plt.show()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
