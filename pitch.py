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

    def __init__(self, framerate,
                 pitchmin=70, pitchmax=400,
                 threshold=0.75, maxitems=10):
        self.framerate = framerate
        self.wmin = (framerate/pitchmax)
        self.wmax = (framerate/pitchmin)
        self.threshold = threshold
        self.maxitems = maxitems
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
            r = wavcorr.autocorrs16(
                self.wmin, self.wmax,
                self.threshold, self.maxitems,
                self._buf, i)
            r = [ (w, sim, wavcorr.calcmags16(self._buf, i, w))
                  for (w,sim) in r ]
            yield (n, r, self._buf[i*2:(i+n)*2])
            i += n
        self._buf = self._buf[i*2:]
        self._nframes -= i
        return


##  PitchSmoother
##
class PitchSmoother(object):

    def __init__(self, framerate, windowsize, 
                 threshold_sim=0.75,
                 threshold_mag=0.025):
        self.framerate = framerate
        self.windowsize = windowsize
        self.threshold_sim = threshold_sim
        self.threshold_mag = threshold_mag
        self.ratio = 0.9
        self._threads = []
        self._t = 0
        return

    def feed(self, n, pitches):
        pitches = [ (w,sim,mag) for (w,sim,mag) in pitches 
                    if self.threshold_sim < sim and self.threshold_mag < mag ]
        sims = [ 0 for _ in self._threads ]
        for (w1,sim1,_) in pitches:
            taken = False
            for (i,(w0,dt0,_)) in enumerate(self._threads):
                if w0*self.ratio <= w1 and w1 <= w0/self.ratio:
                    if sims[i] < sim1:
                        self._threads[i] = (w1, dt0, self._t)
                        sims[i] = sim1
                    else:
                        self._threads[i] = (w0, dt0, self._t)
                    taken = True
            if not taken:
                self._threads.append((w1, 0, self._t))
                sims.append(sim1)
        threads = []
        r = []
        for (sim,(w,dt,t)) in zip(sims, self._threads):
            if self.windowsize <= (self._t-t):
                continue
            elif self.windowsize/2 < dt:
                r.append((sim, self.framerate/w))
            if sim:
                threads.append((w,dt+n,t))
            else:
                threads.append((w,dt-n,t))
        self._threads = threads
        self._t += n
        yield (n, sorted(r, reverse=True))
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
                                     pitchmin=pitchmin, pitchmax=pitchmax,
                                     threshold=threshold_sim)
            smoother = PitchSmoother(src.framerate,
                                     windowsize=2*src.framerate/pitchmin,
                                     threshold_sim=threshold_sim,
                                     threshold_mag=threshold_mag)
        i = 0
        skip = True
        while 1:
            (nframes,buf) = src.readraw(bufsize)
            if not nframes: break
            seq = detector.feed(buf, nframes)
            for (n,pitches,data) in seq:
                if debug:
                    print ('# %d: %r' % (i, pitches))
                for (n,spitch) in smoother.feed(n, pitches):
                    if spitch:
                        print i, ' '.join( repr(pitch) for (sim,pitch) in spitch )
                        skip = False
                    else:
                        if not skip:
                            print
                            skip = True
                    i += n
        src.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
