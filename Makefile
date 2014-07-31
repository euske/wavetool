# Makefile

RM=rm -f
CP=cp -f
PYTHON=python

all: wavcorr.so

clean:
	-$(RM) -r build
	-$(RM) *.pyc *.pyo
	-$(RM) wavcorr.so

wavcorr.so: wavcorr.c
	$(PYTHON) setup.py build
	$(CP) build/lib.*/wavcorr.so .

pitch.py: wavcorr.so
