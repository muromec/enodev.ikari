
#global
PY=python2.7
VE=$(PY) -m virtualenv

# local
pip=env/bin/pip
py=env/bin/python

all: env env/deps

env:
	$(VE) env

env/deps: requirements.txt env
	$(pip) install -r $<
	touch $@
