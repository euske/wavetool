#!/usr/bin/env python
#
# Pitch detector
#
# usage: python pitch.py [-M|-F] [-n pitchmin] [-m pitchmax] wav ...
#

import sys
import wavcorr


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
                 pitchmin=70, 
                 threshold_sim=0.75,
                 threshold_mag=0.025):
        self.framerate = framerate
        self.threshold_sim = threshold_sim
        self.threshold_mag = threshold_mag
        self.windowsize = 2*(framerate/pitchmin)
        self._samples = []
        self._nsamples = 0
        return

    def feed(self, n, sim, mag, pitch):
        self._samples.append((n, sim, mag, pitch))
        self._nsamples += n
        p = [ pitch for (_,sim,mag,pitch) in self._samples
              if self.threshold_sim < sim and self.threshold_mag < mag ]
        if p:
            pitch = sum(p)/len(p)
        else:
            pitch = 0
        yield (n, pitch)
        while self.windowsize <= self._nsamples:
            (n,sim,freq,mag) = self._samples.pop(0)
            self._nsamples -= n
        return


# main
def main(argv):
    import getopt
    from wavestream import WaveReader
    def usage():
        print 'usage: %s [-d] [-M|-F] [-n pitchmin] [-m pitchmax] [-T threshold_sim] [-S threshold_mag] wav ...' % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'dMFn:m:T:S:')
    except getopt.GetoptError:
        return usage()
    debug = 0
    pitchmin = 70
    pitchmax = 400
    threshold_sim = 0.75
    threshold_mag = 0.025
    bufsize = 10000
    for (k, v) in opts:
        if k == '-d': debug += 1
        elif k == '-M': (pitchmin,pitchmax) = (75,200) # male voice
        elif k == '-F': (pitchmin,pitchmax) = (150,300) # female voice
        elif k == '-n': pitchmin = int(v)
        elif k == '-m': pitchmax = int(v)
        elif k == '-T': threshold_sim = float(v)
        elif k == '-S': threshold_mag = float(v)
    detector = None
    smoother = None
    for path in args:
        print '#', path
        src = WaveReader(path)
        if src.nchannels != 1: raise ValueError('invalid number of channels')
        if src.sampwidth != 2: raise ValueError('invalid sampling width')
        if detector is None:
            detector = PitchDetector(src.framerate,
                                     pitchmin=pitchmin, pitchmax=pitchmax)
            smoother = PitchSmoother(src.framerate,
                                     pitchmin=pitchmin,
                                     threshold_sim=threshold_sim,
                                     threshold_mag=threshold_mag)
        i = 0
        skip = True
        while 1:
            (nframes,buf) = src.readraw(bufsize)
            if not nframes: break
            pitches = detector.feed(buf, nframes)
            for (n,sim,mag,pitch,data) in pitches:
                if debug:
                    print ('# %d-%d: %.3f %.3f %d' %
                           (i, i+src.framerate/pitch, sim, mag, pitch))
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
