
#global
PY=python2.7
VE=$(PY) -m virtualenv

# local
pip=env/bin/pip
py=env/bin/python

all: env env/deps

env:
	$(VE) env

formgear:
	git clone git@github.com:xen/formgear.git 

env/deps: requirements.txt env formgear
	$(pip) install -r $<
	touch $@
