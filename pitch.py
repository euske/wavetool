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

    def __init__(self, 
                 wmin=100, wmax=600,
                 threshold_sim=0.75, maxitems=10):
        self.wmin = wmin
        self.wmax = wmax
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

    def __init__(self, windowsize, 
                 threshold_sim=0.75,
                 threshold_mag=0.025,
                 pitch_ratio=1.2):
        self.windowsize = windowsize
        self.threshold_sim = threshold_sim
        self.threshold_mag = threshold_mag
        self.pitch_ratio = pitch_ratio
        self._threads = []  # [(w0,score0,t0), (w1,score1,t1), ...]
        self._streak = []
        return

    def feed(self, bt, n, pitches):
        pitches = [ (w,sim,mag) for (w,sim,mag) in pitches 
                    if self.threshold_sim < sim and self.threshold_mag < mag ]
        threads = ([ (w,0,score,t) for (w,score,t) in self._threads ] +
                   [ (w,sim,0,bt) for (w,sim,_) in pitches ])
        self._threads = []
        r = []
        for (i,(w0,sim0,score0,t0)) in enumerate(threads):
            i += 1
            while i < len(threads):
                (w1,sim1,score1,t1) = threads[i]
                if w1 <= w0*self.pitch_ratio and w0 <= w1*self.pitch_ratio:
                    if sim0 < sim1:
                        w0 = w1
                    sim0 = max(sim0, sim1)
                    score0 = max(score0, score1)
                    t0 = max(t0, t1)
                    del threads[i]
                else:
                    i += 1
            if (bt-t0) < self.windowsize:
                score0 += sim0
                self._threads.append((w0,score0,t0))
                r.append((score0, w0, sim0))
        if r:
            r.sort(reverse=True)
            self._streak.append((bt,n,r))
        elif self._streak:
            yield self._streak
            self._streak = []
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
        framerate = src.framerate
        if detector is None:
            detector = PitchDetector(wmin=framerate/pitchmax,
                                     wmax=framerate/pitchmin,
                                     threshold_sim=threshold_sim)
            smoother = PitchSmoother(2*framerate/pitchmin,
                                     threshold_sim=threshold_sim,
                                     threshold_mag=threshold_mag)
        for (b,e) in ranges:
            if e == 0:
                e = src.nframes
            src.seek(b)
            length = e-b
            i0 = b
            while length:
                (nframes,buf) = src.readraw(min(bufsize, length))
                if not nframes: break
                length -= nframes
                seq = detector.feed(buf, nframes)
                for (n0,pitches,data) in seq:
                    if debug:
                        print ('# %d: %r' % (n0, pitches))
                    for streak in smoother.feed(i0, n0, pitches):
                        for (i1,n1,spitches) in streak:
                            print i1, n1, ' '.join( '%d:%.4f' % (w, sim)
                                                    for (_,w,sim) in spitches )
                        print
                    i0 += n0
        src.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
