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
                 threshold_sim=0.75, maxitems=10):
        self.framerate = framerate
        self.wmin = (framerate/pitchmax)
        self.wmax = (framerate/pitchmin)
        self.threshold_sim = threshold_sim
        self.maxitems = maxitems
        self.reset()
        return

    def reset(self):
        self._buf = ''
        return
    
    def feed(self, buf, nframes):
        self._buf += buf
        bufmax = len(self._buf)/2 - self.wmax*2
        step = self.wmin/2
        i = 0
        while i < bufmax:
            r = wavcorr.autocorrs16(
                self.wmin, self.wmax,
                self.threshold_sim, self.maxitems,
                self._buf, i)
            r = [ (w, sim, wavcorr.calcmags16(self._buf, i, w))
                  for (w,sim) in r ]
            yield (step, r, self._buf[i*2:(i+step)*2])
            i += step
        self._buf = self._buf[i*2:]
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
        self._threads = []  # [(w0,t0), (w1,t1), ...]
        self._t = 0
        return

    def feed(self, n, pitches):
        pitches = [ (w,sim,mag) for (w,sim,mag) in pitches 
                    if self.threshold_sim < sim and self.threshold_mag < mag ]
        threads = [ (w,0,t) for (w,t) in self._threads ]
        for (w1,sim1,_) in pitches:
            taken = False
            for (i,(w0,sim0,_)) in enumerate(threads):
                if w0*self.ratio <= w1 and w1 <= w0/self.ratio:
                    if sim0 < sim1:
                        threads[i] = (w1, sim1, self._t)
                    taken = True
            if not taken:
                threads.append((w1, sim1, self._t))
        self._threads = []
        r = []
        for (w,sim,t) in threads:
            if self.windowsize <= (self._t-t):
                continue
            else:
                r.append((sim, self.framerate/w))
            self._threads.append((w,t))
        self._t += n
        yield (n, sorted(r, reverse=True))
        return


# main
def main(argv):
    import getopt
    from wavestream import WaveReader
    def usage():
        print ('usage: %s [-d] [-M|-F] [-n pitchmin] [-m pitchmax]'
               ' [-T threshold_sim] [-S threshold_mag] wav ...' % argv[0])
        return 100
    def parse_range(x):
        (b,_,e) = x.partition('-')
        try:
            b = int(b)
        except ValueError:
            b = 0
        try:
            e = int(e)
        except ValueError:
            e = 0
        return (b,e)
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
    for arg1 in args:
        (path,_,ranges) = arg1.partition(':')
        ranges = [ parse_range(x) for x in ranges.split(',') if x ]
        if not ranges:
            ranges.append((0,0))
        print '#', path, ranges
        src = WaveReader(path)
        if src.nchannels != 1: raise ValueError('invalid number of channels')
        if src.sampwidth != 2: raise ValueError('invalid sampling width')
        if detector is None:
            detector = PitchDetector(src.framerate,
                                     pitchmin=pitchmin, pitchmax=pitchmax,
                                     threshold_sim=threshold_sim)
            smoother = PitchSmoother(src.framerate,
                                     windowsize=2*src.framerate/pitchmin,
                                     threshold_sim=threshold_sim,
                                     threshold_mag=threshold_mag)
        for (b,e) in ranges:
            if e == 0:
                e = src.nframes
            src.seek(b)
            length = e-b
            i = b
            skip = True
            while length:
                (nframes,buf) = src.readraw(min(bufsize, length))
                if not nframes: break
                length -= nframes
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
