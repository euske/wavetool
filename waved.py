#!/usr/bin/env python
import sys
import os.path
import pygame
from wavestream import WaveReader, WaveWriter, PygameWavePlayer

class WavEdError(Exception): pass
class WavNoFileError(Exception): pass

def bound(x,y,z): return max(x, min(y, z))

class Cursor(object):

    def __init__(self, maxlength):
        self.maxlength = maxlength
        self.start = 0
        self.end = 0
        self.length = None
        assert ((self.end is not None and self.length is None) or
                (self.end is None and self.length is not None))
        return

    def __repr__(self):
        if self.end is not None:
            return 'start %d end %d' % (self.start, self.end)
        else:
            return 'start %d length %d' % (self.start, self.length)

    def get_length(self):
        if self.end is not None:
            return (self.end - self.start)
        else:
            return self.length

    def set_start(self, start):
        self.start = bound(0, start, self.maxlength)
        if self.length is not None:
            self.length = bound(0, self.length, self.maxlength-self.start)
        return

    def set_end(self, end):
        self.end = bound(0, end, self.maxlength)
        self.length = None
        return

    def set_length(self, length):
        self.end = None
        self.length = bound(0, length, self.maxlength-self.start)
        return
    
class WavEd(object):

    def __init__(self):
        self._wav = None
        self._cur = None
        return

    def close(self):
        if self._wav is not None:
            self._wav.close()
            self._wav = None
            self._cur = None
        return

    def read(self, path):
        self.close()
        self._wav = WaveReader(path)
        self._cur = Cursor(self._wav.nframes)
        self._cur.set_length(self._wav.framerate)
        print ('Read: rate=%d, frames=%d, duration=%.3f' %
               (self._wav.framerate, self._wav.nframes,
                self._wav.nframes/float(self._wav.framerate)))
        return

    def write(self, path, force=False):
        if self._cur is None: raise WavNoFileError
        if not force and os.path.exists(path):
            raise WavEdError('File exists: %r' % path)
        nframes = self._cur.get_length()
        if nframes == 0:
            raise WavEdError('Empty range')
        fp = open(path, 'wb')
        writer = WaveWriter(fp,
                            nchannels=self._wav.nchannels,
                            sampwidth=self._wav.sampwidth,
                            framerate=self._wav.framerate)
        self._wav.seek(self._cur.start)
        (_,data) = self._wav.readraw(nframes)
        writer.writeraw(data)
        writer.close()
        fp.close()
        print ('Written: %r, rate=%d, frames=%d, duration=%.3f' %
               (path, writer.framerate, nframes,
                nframes/float(writer.framerate)))
        return

    def play(self):
        if self._cur is None: raise WavNoFileError
        nframes = self._cur.get_length()
        player = PygameWavePlayer(nchannels=self._wav.nchannels,
                                  sampwidth=self._wav.sampwidth,
                                  framerate=self._wav.framerate)
        self._wav.seek(self._cur.start)
        (_,data) = self._wav.readraw(nframes)
        player.writeraw(data)
        player.close()
        return

    def status(self):
        if self._cur is None: raise WavNoFileError
        print self._cur
        return

    def _getv(self, v):
        if self._wav is None: raise WavNoFileError
        if '.' in v:
            return int(float(v)*self._wav.framerate)
        else:
            return int(v)

    def run(self):
        self.command('p')
        while 1:
            try:
                s = raw_input('> ')
            except EOFError:
                break
            pygame.mixer.stop()
            s = s.strip()
            if s:
                if not self.command(s): break
        return

    def command(self, s):
        try:
            if s[0].isdigit():
                self._cur.set_start(self._getv(s))
                self.status()
                self.play()
                return True
            c = s[0]
            v = s[1:].strip()
            if c == 'q':
                return False
            elif c == 'r':
                self.read(v)
                self.status()
                self.play()
            elif c == 'w' or c == 'W':
                self.write(v, force=(c=='W'))
            elif c == 'p':
                self.status()
                self.play()
            elif c == 's':
                self._cur.set_start(self._getv(v))
                self.status()
                self.play()
            elif c == 'e':
                self._cur.set_end(self._getv(v))
                self.status()
                self.play()
            elif c == 'l':
                self._cur.set_length(self._getv(v))
                self.status()
                self.play()
            else:
                print 'commands: q)uit, r)ead, w)rite, p)lay, s)tart, e)nd, l)ength'
        except WavNoFileError, e:
            print 'no file'
        except (WavEdError, IOError, ValueError), e:
            print 'error:', e
        return True

def main(argv):
    #pygame.mixer.pre_init(22050, -16, 1)
    pygame.mixer.init()
    args = argv[1:]
    waved = WavEd()
    if args:
        waved.read(args.pop(0))
    waved.run()
    waved.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
