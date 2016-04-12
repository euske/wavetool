#!/usr/bin/env python
#
# Generates a tone wave.
#
# usage:
#   $ python genwav.py {-S|-Q|-T|-N} [-o out.wav] [tone ...]
#

import sys
import wave
import struct
import array
import random
import os.path
from math import sin, cos, pi
from wavestream import WaveWriter


##  WaveGenerator
##
class WaveGenerator(object):

    TONE2FREQ = {
        'A0': 28, '^A0': 29, 'B0': 31, 'C1': 33,
        '^C1': 35, 'D1': 37, '^D1': 39, 'E1': 41,
        'F1': 44, '^F1': 46, 'G1': 49, '^G1': 52,
        'A1': 55, '^A1': 58, 'B1': 62, 'C2': 65,
        '^C2': 69, 'D2': 73, '^D2': 78, 'E2': 82,
        'F2': 87, '^F2': 93, 'G2': 98, '^G2': 104,
        'A2': 110, '^A2': 117, 'B2': 123, 'C3': 131,
        '^C3': 139, 'D3': 147, '^D3': 156, 'E3': 165,
        'F3': 175, '^F3': 185, 'G3': 196, '^G3': 208,
        'A3': 220, '^A3': 233, 'B3': 247, 'C4': 262,
        '^C4': 277, 'D4': 294, '^D4': 311, 'E4': 330,
        'F4': 349, '^F4': 370, 'G4': 392, '^G4': 415,
        'A4': 440, '^A4': 466, 'B4': 494, 'C5': 523,
        '^C5': 554, 'D5': 587, '^D5': 622, 'E5': 659,
        'F5': 698, '^F5': 740, 'G5': 784, '^G5': 831,
        'A5': 880, '^A5': 932, 'B5': 988, 'C6': 1047,
        '^C6': 1109, 'D6': 1175, '^D6': 1245, 'E6': 1319,
        'F6': 1397, '^F6': 1480, 'G6': 1568, '^G6': 1661,
        'A6': 1760, '^A6': 1865, 'B6': 1976, 'C7': 2093,
        '^C7': 2217, 'D7': 2349, '^D7': 2489, 'E7': 2637,
        'F7': 2794, '^F7': 2960, 'G7': 3136, '^G7': 3322,
        'A7': 3520, '^A7': 3729, 'B7': 3951, 'C8': 4186,
    }
    @classmethod
    def tone2freq(klass, v):
        if v in klass.TONE2FREQ:
            return klass.TONE2FREQ[v]
        else:
            return float(v)

    def __init__(self, framerate):
        self.framerate = framerate
        return

    def add(self, *iters):
        while 1:
            x = 0.0
            for it in iters:
                try:
                    x += it.next()
                except StopIteration:
                    return
            yield x
        return

    def mult(self, *iters):
        while 1:
            x = 1.0
            for it in iters:
                try:
                    x *= it.next()
                except StopIteration:
                    return
            yield x
        return

    def concat(self, *iters):
        for it in iters:
            for x in it:
                yield x
        return

    def mix(self, *iters):
        r = 1.0/len(iters)
        return self.amp(r, self.add(*iters))

    def amp(self, it, volume):
        for x in it:
            yield volume*x
        return

    def clip(self, it, duration):
        n = int(self.framerate * duration)
        for i in xrange(n):
            try:
                yield it.next()
            except StopIteration:
                break
        return

    def env(self, duration, a0, a1):
        n = int(self.framerate * duration)
        r = (a1-a0)/float(n)
        for i in xrange(n):
            yield a0+(i+1)*r
        return

    def sine(self, freq):
        freq = self.tone2freq(freq)
        fr = 2*pi*freq/self.framerate
        i = 0
        while 1:
            yield sin(i*fr)
            i += 1
        return

    def rect(self, freq):
        freq = self.tone2freq(freq)
        if freq == 0:
            while 1:
                yield 0
        else:
            w = int(self.framerate/freq/2)
            while 1:
                for i in xrange(w):
                    yield +1
                for i in xrange(w):
                    yield -1
        return

    def saw(self, freq):
        freq = self.tone2freq(freq)
        if freq == 0:
            while 1:
                yield 0
        else:
            w = int(self.framerate/freq)
            r = 2.0/float(w)
            while 1:
                for i in xrange(w):
                    yield i*r-1.0
        return

    def noise(self, freq):
        freq = self.tone2freq(freq)
        if freq == 0:
            while 1:
                yield 0
        else:
            w = int(self.framerate/freq/2)
            while 1:
                x = random.random()*2.0-1.0
                for i in xrange(w):
                    yield x
        return
        

# gen_sine_tone
def gen_sine_tone(framerate, tones, volume=0.4, duration=0.02):
    print 'gen_sine_tone', tones
    gen = WaveGenerator(framerate)
    wav = gen.concat(*[ gen.clip(duration, gen.sine(k)) for k in tones ])
    return gen.amp(volume, wav)

# gen_rect_tone
def gen_rect_tone(framerate, tones, volume=0.3, attack=0.00, decay=0.0):
    print 'gen_rect_tone', tones
    gen = WaveGenerator(framerate)
    wav = gen.mix(*[ gen.rect(k) for k in tones ])
    env = gen.concat(gen.env(attack, 0.0, volume),
                     gen.env(decay, volume, 0.0))
    return gen.mult(wav, env)

# gen_saw_tone
def gen_saw_tone(framerate, tones, volume=0.5, attack=0.01, decay=0.7):
    print 'gen_saw_tone', tones
    gen = WaveGenerator(framerate)
    wav = gen.mix(*[ gen.saw(k) for k in tones ])
    env = gen.concat(gen.env(attack, 0.0, volume),
                     gen.env(decay, volume, 0.0))
    return gen.mult(wav, env)

# gen_noise_tone
def gen_noise_tone(framerate, tones, volume=0.5, attack=0.01, decay=0.7):
    print 'gen_noise_tone', tones
    gen = WaveGenerator(framerate)
    wav = gen.mix(*[ gen.noise(k) for k in tones ])
    env = gen.concat(gen.env(attack, 0.0, volume),
                     gen.env(decay, volume, 0.0))
    return gen.mult(wav, env)

# main
def main(argv):
    import getopt
    def usage():
        print 'usage: %s [-f] [-o out.wav] [-m maxlength] [expr]' % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'fo:m:')
    except getopt.GetoptError:
        return usage()
    force = False
    maxlength = 10
    path = 'out.wav'
    for (k, v) in opts:
        if k == '-f': force = True
        elif k == '-o': path = v
        elif k == '-m': maxlength = float(v)
    if not args: return usage()
    if not force and os.path.exists(path): raise IOError(path)
    fp = open(path, 'wb')
    stream = WaveWriter(fp)
    expr = args.pop(0)
    gen = WaveGenerator(stream.framerate)
    vars = {
        'add': gen.add,
        'mult': gen.mult,
        'amp': gen.amp,
        'concat': gen.concat,
        'mix': gen.mix,
        'clip': gen.clip,
        'env': gen.env,
        'sine': gen.sine,
        'rect': gen.rect,
        'saw': gen.saw,
        'noise': gen.noise,
    }
    wav = eval(expr, vars, {})
    stream.write(gen.clip(wav, maxlength))
    stream.close()
    fp.close()
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv))
