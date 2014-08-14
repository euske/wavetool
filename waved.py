#!/usr/bin/env python
import sys
import os.path
import pygame
import array
from cStringIO import StringIO
from wavestream import WaveReader, WaveWriter

class WavEdError(Exception): pass
class WavNoFileError(Exception): pass

class WavEd(object):

    def __init__(self):
        self._wav = None
        return

    def close(self):
        if self._wav is not None:
            self._wav.close()
            self._wav = None
        return

    def read(self, path):
        self.close()
        self._wav = WaveReader(path)
        self._start = 0
        self._end = 0
        self._length = self._wav.framerate
        self._adjust()
        print ('Read: rate=%d, frames=%d, duration=%.3f' %
               (self._wav.framerate, self._wav.nframes,
                self._wav.nframes/float(self._wav.framerate)))
        return

    def write(self, path, force=False):
        if self._wav is None: raise WavNoFileError
        if not force and os.path.exists(path):
            raise WavEdError('File exists: %r' % path)
        if self._start < self._end:
            nframes = self._end - self._start
        else:
            nframes = self._length
        fp = open(path, 'wb')
        writer = WaveWriter(fp,
                            nchannels=self._wav.nchannels,
                            sampwidth=self._wav.sampwidth,
                            framerate=self._wav.framerate)
        self._wav.seek(self._start)
        (_,data) = self._wav.readraw(nframes)
        writer.writeraw(data)
        writer.close()
        fp.close()
        print ('Written: %r, rate=%d, frames=%d, duration=%.3f' %
               (path, writer.framerate, nframes,
                nframes/float(writer.framerate)))
        return

    def play(self):
        if self._wav is None: raise WavNoFileError
        if self._start < self._end:
            nframes = self._end - self._start
        else:
            nframes = self._length
        fp = StringIO()
        writer = WaveWriter(fp,
                            nchannels=self._wav.nchannels,
                            sampwidth=self._wav.sampwidth,
                            framerate=self._wav.framerate)
        self._wav.seek(self._start)
        (_,data) = self._wav.readraw(nframes)
        writer.writeraw(data)
        writer.close()
        sound = pygame.mixer.Sound(buffer(fp.getvalue()))
        sound.play()
        return

    def status(self):
        if self._wav is None: raise WavNoFileError
        elif self._start < self._end:
            print 'start %d end %d' % (self._start, self._end)
        else:
            print 'start %d length %d' % (self._start, self._length)
        return

    def _getv(self, v):
        if self._wav is None: raise WavNoFileError
        if '.' in v:
            return int(float(v)*self._wav.framerate)
        else:
            return int(v)

    def _adjust(self):
        if self._wav is None: raise WavNoFileError
        self._length = (min(self._start+self._length, self._wav.nframes)-
                        self._start)
        return
        
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
                self._start = self._getv(s)
                self._adjust()
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
                self._start = self._getv(v)
                self._adjust()
                self.status()
                self.play()
            elif c == 'e':
                self._end = self._getv(v)
                self._adjust()
                self.status()
                self.play()
            elif c == 'l':
                self._length = self._getv(v)
                self._end = -1
                self._adjust()
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
