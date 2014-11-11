#!/usr/bin/env python
import sys
import os.path
import pygame
from wavestream import WaveReader
from wavestream import WaveWriter
from wavestream import PygameWavePlayer

def bound(x,y,z): return max(x, min(y, z))


##  Exceptions
##
class WavEdError(Exception): pass
class WavEdExit(WavEdError): pass
class WavNoFileError(WavEdError): pass
class WavRangeError(WavEdError): pass


##  WavCursor
##
class WavCursor(object):

    def __init__(self, wav, name=None, start=0, end=0):
        self._wav = wav
        self.name = name
        self.start = start
        self.end = end
        self.length = None
        assert ((self.end is not None and self.length is None) or
                (self.end is None and self.length is not None))
        return

    def copy(self, name):
        cur = self.__class__(self._wav, name)
        cur.start = self.start
        cur.end = self.end
        cur.length = self.length
        return cur

    @classmethod
    def fromstr(klass, wav, line):
        (name,_,v) = line.partition(' ')
        (s,_,e) = v.partition(' ')
        return klass(wav, name, int(s), int(e))

    def tostr(self):
        return '%s %d %d' % (self.name, self.start, self.get_end())

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
            v = self.end - self.start
        else:
            v = self.length
        if v == 0: raise WavRangeError('empty range')
        return v

    def get_end(self):
        if self.end is not None:
            return self.end
        else:
            return self.start + self.length

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


##  WavEd
##
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
        self._cur = WavCursor(self._wav)
        self._cur.set_length('1.0')
        self._curs = {}
        print ('Read: rate=%d, frames=%d, duration=%.3f' %
               (self._wav.framerate, self._wav.nframes,
                self._wav.nframes/float(self._wav.framerate)))
        return

    def write(self, cur, path, force=False):
        if not force and os.path.exists(path):
            raise WavEdError('File exists: %r' % path)
        nframes = cur.get_length()
        fp = open(path, 'wb')
        writer = WaveWriter(fp,
                            nchannels=self._wav.nchannels,
                            sampwidth=self._wav.sampwidth,
                            framerate=self._wav.framerate)
        self._wav.seek(cur.start)
        (_,data) = self._wav.readraw(nframes)
        writer.writeraw(data)
        writer.close()
        fp.close()
        print ('Written: %r, rate=%d, frames=%d, duration=%.3f' %
               (path, writer.framerate, nframes,
                nframes/float(writer.framerate)))
        return

    def play(self, cur):
        nframes = cur.get_length()
        player = PygameWavePlayer(nchannels=self._wav.nchannels,
                                  sampwidth=self._wav.sampwidth,
                                  framerate=self._wav.framerate)
        self._wav.seek(cur.start)
        (_,data) = self._wav.readraw(nframes)
        player.writeraw(data)
        player.close()
        return

    def show(self, cur):
        print cur
        return

    def run(self):
        self.exec_command('p')
        while 1:
            try:
                s = raw_input('> ')
                pygame.mixer.stop()
                s = s.strip()
                if s:
                    self.exec_command(s)
            except (EOFError, WavEdExit):
                break
        return

    def show_help(self):
        print 'commands: q)uit, r)ead, w)rite, p)lay, s)tart, e)nd, l)ength'
        print '          C)reate, D)elete, R)ename, J)ump, L)ist, load, save, export'
        return
    
    def exec_command(self, s):
        try:
            if s[0].isdigit() or s[0] in '+-':
                self.cmd_s(s)
                return

            (c,_,v) = s.partition(' ')
            c = 'cmd_'+c.replace('!','_f')
            if hasattr(self, c):
                getattr(self, c)(v)
            else:
                self.show_help()
        except WavEdExit, e:
            raise
        except WavNoFileError, e:
            print 'no file'
        except WavRangeError, e:
            print 'invalid range'
        except (WavEdError, IOError, ValueError), e:
            print 'error:', e
        return

    def cmd_q(self, v):
        raise WavEdExit
    
    def cmd_r(self, v):
        self.read(v)
        if self._cur is None: raise WavNoFileError
        self.show(self._cur)
        self.play(self._cur)
        return
    
    def cmd_w_f(self, v):
        self.cmd_w(v, force=True)
        return
    
    def cmd_w(self, v, force=False):
        if self._cur is None: raise WavNoFileError
        if v:
            name = v
        else:
            name = self._cur.name+'.wav'
        self.write(self._cur, name, force=force)
        return
    
    def cmd_p(self, v):
        if self._cur is None: raise WavNoFileError
        self.show(self._cur)
        self.play(self._cur)
        return
    
    def cmd_s(self, v):
        if self._cur is None: raise WavNoFileError
        self._cur.set_start(v)
        self.show(self._cur)
        self.play(self._cur)
        return
    
    def cmd_e(self, v):
        if self._cur is None: raise WavNoFileError
        self._cur.set_end(v)
        self.show(self._cur)
        self.play(self._cur)
        return
    
    def cmd_l(self, v):
        if self._cur is None: raise WavNoFileError
        self._cur.set_length(v)
        self.show(self._cur)
        self.play(self._cur)
        return
    
    def cmd_C(self, v):
        if self._cur is None: raise WavNoFileError
        self._cur = self._cur.copy(v)
        self._curs[v] = self._cur
        return

    def cmd_D(self, v):
        try:
            del self._curs[v]
        except KeyError:
            raise WavEdError('Not found: %r' % v)
        return
    
    def cmd_R(self, v):
        if self._cur is None: raise WavNoFileError
        self._cur.name = v
        return
    
    def cmd_J(self, v):
        try:
            self._cur = self._curs[v]
        except KeyError:
            raise WavEdError('Not found: %r' % v)
        self.play(self._cur)
        return
    
    def cmd_L(self, v):
        if v:
            try:
                print self._curs[v]
            except KeyError:
                raise WavEdError('Not found: %r' % v)
        else:
            for k in sorted(self._curs.keys()):
                print self._curs[k]
        return

    def cmd_load(self, v):
        if self._wav is None: raise WavNoFileError
        fp = file(v, 'r')
        for line in fp:
            c = WavCursor.fromstr(self._wav, line.rstrip())
            self._curs[c.name] = c
        fp.close()
        return
    
    def cmd_save(self, v):
        fp = file(v, 'w')
        for k in sorted(self._curs.keys()):
            c = self._curs[k]
            fp.write('%s\n' % c.tostr())
        fp.close()
        return

    def cmd_export(self, v):
        for k in sorted(self._curs.keys()):
            c = self._curs[k]
            try:
                self.write(c, c.name+'.wav')
            except WavEdError, e:
                print e
        return
    

# main
def main(argv):
    import getopt
    #pygame.mixer.pre_init(22050, -16, 1)
    pygame.mixer.init()
    def usage():
        print 'usage: %s [-d] [-r ranges] [file ...]' % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'dr:')
    except getopt.GetoptError:
        return usage()
    debug = 0
    for (k, v) in opts:
        if k == '-d': debug += 1
        elif k == '-r': pass
    waved = WavEd()
    if args:
        waved.read(args.pop(0))
    waved.run()
    waved.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
