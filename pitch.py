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
            mag = wavcorr.calcmags16(self._buf, i, dmax)
            pitch = self.framerate/dmax
            yield (n, mmax, mag, pitch, self._buf[i*2:(i+n)*2])
            i += n
        self._buf = self._buf[i*2:]
        self._nframes -= i
        return


##  PitchSmoother
##
class PitchSmoother(object):

    def __init__(self, framerate,
                 simmin=0.7, simmax=0.9,
                 magmin=0.01, magmax=0.03,
                 window=0.01):
        self.framerate = framerate
        self.simmin = simmin
        self.simmax = simmax
        self.magmin = magmin
        self.magmax = magmax
        self.window = int(window * framerate)
        self._samples = []
        self._nsamples = 0
        self._active = False
        return

    def feed(self, n, sim, mag, pitch):
        self._samples.append((n, sim, mag, pitch))
        self._nsamples += n
        smax = max( sim for (_,sim,mag,pitch) in self._samples )
        mmax = max( mag for (_,sim,mag,pitch) in self._samples )
        if self.simmax < smax and self.magmax < mmax:
            p = [ pitch for (_,sim,mag,pitch) in self._samples
                  if self.simmin < sim and self.magmin < mag ]
            pitch = (min(p)+max(p))/2
        else:
            pitch = 0
        yield (n, pitch)
        while self.window <= self._nsamples:
            (n,sim,freq,mag) = self._samples.pop(0)
            self._nsamples -= n
        return


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
        skip = False
        while 1:
            (nframes,buf) = src.readraw(bufsize)
            if not nframes: break
            pitches = detector.feed(buf, nframes)
            for (n,sim,mag,pitch,data) in pitches:
                #print (n,sim,mag,pitch)
                for (n,spitch) in smoother.feed(n, sim, mag, pitch):
                    if spitch:
                        print i, spitch
                        skip = False
                    else:
                        if not skip:
                            print
                            skip = True
                    i += n
        src.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
