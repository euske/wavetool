Wavetool
========

Wavetool is a collection of audio file manipulation tools written in Python.

waved.py
--------

CLI-based wave editor. It can be used to cut/trim a sound.

Usage:

   $ python waved.py input.wav

Commands:

  * `r` **<filename>** : Read an audio file.
  * `w` **<filename>** : Write the current range to an audio file. (W for force overwriting)
  * `p` : Play the current range of the samples.
  * `s` **<length>** : Set the starting point of the samples. 
  * `l` **<length>** : Set the length of the samples. The ending point is nullified after using this.
  * `e` **<length>** : Set the ending point of the samples. The length is nullified after using this.
  * `q` : Quit the program.

Lengths can be specified either by the number of frames (integer) or seconds (float).

genwav.wav
----------

Soundeffect generator.

Usage:

   $ python genwav.py {-S|-Q|-T|-N} [-o out.wav] [tone ...]

Options:

  `-S`: Sine wave.
  `-Q`: Square wave.
  `-T`: Triangle wave.
  `-N`: Noise.

Tones can be specified by notes (e.g. `C4`).
Multiple tones can be mixed.


pitch.py
--------

Pitch detector.

Usage:

   $ python pitch.py [-M|-F] [-n pitchmin] [-m pitchmax] wav ...

Options:

  `-M`: Male voice (equivalent to `-n 75 -m 200`).
  `-F`: Female voice (equivalent to `-n 150 -m 300`).
  `-n`: Minumum pitch.
  `-m`: Maximum pitch.

match.py
--------

Waveform pattern matcher.

Usage:

   $ python match.py [-t threshold] src.wav pitch pat1.wav pat2.wav ...

