#!/usr/bin/env python
import sys
import os.path
import pygame
from wavestream import WaveReader, WaveWriter, PygameWavePlayer

class WavEdError(Exception): pass
class WavNoFileError(WavEdError): pass
class WavRangeError(WavEdError): pass

def bound(x,y,z): return max(x, min(y, z))

class Cursor(object):

    def __init__(self, wav, name=None):
        self._wav = wav
        self.name = name
        self.start = 0
        self.end = 0
        self.length = None
        assert ((self.end is not None and self.length is None) or
                (self.end is None and self.length is not None))
        return

    def copy(self, name):
        cur = Cursor(self._wav, name)
        cur.start = self.start
        cur.end = self.end
        cur.length = self.length
        return cur

    def __repr__(self):
        if self.name is None:
            name = ''
        else:
            name = '%s: ' % self.name
        if self.end is not None:
            return '<%s%d-%d>' % (name, self.start, self.end)
        else:
            return '<%s%d+%d>' % (name, self.start, self.length)

    def _parse(self, v0, s):
        rel = 0
        if s.startswith('+'):
            rel = +1
            s = s[1:]
        elif s.startswith('-'):
            rel = -1
            s = s[1:]
        if '.' in s:
            d = int(float(s)*self._wav.framerate)
        else:
            d = int(s)
        if rel:
            if v0 is None: raise WavRangeError('no current value')
            return v0+d*rel
        else:
            return d

    def get_length(self):
        if self.end is not None:
            v = (self.end - self.start)
        else:
            v = self.length
        if v == 0: raise WavRangeError('empty range')
        return v

    def set_start(self, s):
        v = self._parse(self.start, s)
        self.start = bound(0, v, self._wav.nframes)
        if self.length is not None:
            self.length = bound(0, self.length, self._wav.nframes-self.start)
        return

    def set_end(self, s):
        v = self._parse(self.end, s)
        self.end = bound(0, v, self._wav.nframes)
        self.length = None
        return

    def set_length(self, s):
        v = self._parse(self.length, s)
        self.end = None
        self.length = bound(0, v, self._wav.nframes-self.start)
        return
    
class WavEd(object):

    def __init__(self):
        self._wav = None
        self._cur = None
        self._curs = {}
        return

    def close(self):
        if self._wav is not None:
            self._wav.close()
            self._wav = None
            self._cur = None
            self._curs = {}
        return

    def read(self, path):
        self.close()
        self._wav = WaveReader(path)
        self._cur = Cursor(self._wav)
        self._cur.set_length('1.0')
        self._curs = {}
        print ('Read: rate=%d, frames=%d, duration=%.3f' %
               (self._wav.framerate, self._wav.nframes,
                self._wav.nframes/float(self._wav.framerate)))
        return

    def write(self, path, force=False):
        if self._cur is None: raise WavNoFileError
        if not force and os.path.exists(path):
            raise WavEdError('File exists: %r' % path)
        nframes = self._cur.get_length()
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
            if s[0].isdigit() or s[0] in '+-':
                if self._cur is None: raise WavNoFileError
                self._cur.set_start(s)
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
                if self._cur is None: raise WavNoFileError
                if v:
                    name = v
                else:
                    name = self._cur.name+'.wav'
                self.write(name, force=(c=='W'))
            elif c == 'p':
                self.status()
                self.play()
            elif c == 's':
                if self._cur is None: raise WavNoFileError
                self._cur.set_start(v)
                self.status()
                self.play()
            elif c == 'e':
                if self._cur is None: raise WavNoFileError
                self._cur.set_end(v)
                self.status()
                self.play()
            elif c == 'l':
                if self._cur is None: raise WavNoFileError
                self._cur.set_length(v)
                self.status()
                self.play()
            elif c == 'C':
                if self._cur is None: raise WavNoFileError
                self._cur = self._cur.copy(v)
                self._curs[v] = self._cur
            elif c == 'R':
                if self._cur is None: raise WavNoFileError
                self._cur.name = v
            elif c == 'J':
                try:
                    self._cur = self._curs[v]
                except KeyError:
                    raise WavEdError('Not found: %r' % v)
                self.play()
            elif c == 'L':
                for k in sorted(self._curs.keys()):
                    print self._curs[k]
            else:
                print 'commands: q)uit, r)ead, w)rite, p)lay, s)tart, e)nd, l)ength'
                print '          C)reate, J)ump, R)ename, L)ist'
        except WavNoFileError, e:
            print 'no file'
        except WavRangeError, e:
            print 'invalid range'
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
