import os

from flask import render_template

import envoy

from pkg_resources import resource_filename
MAKEFILE = os.path.abspath(resource_filename("ikari.projects", "Makefile.ops"))

def create_user(project):
    return make(project, 'create_user')

def setup_key(project):
    return make(project, 'setup_key')

def clone_code(project, url):
    return make(project, 'clone_code', env={"URL":url})

def setup_repo(project):
    return make(project, 'setup_repo')

class Conf(object):
    def __init__(self, project):
        self.project = project

    @property
    def username(self):
        return 'app-%s' % self.project

    @property
    def uid(self):
        return make(self.project, 'fetch_uid')

    @property
    def home(self):
        return '/home/%s' % self.username

    @property
    def serve(self):
        return '%s/serve' % self.home

    @property
    def sock(self):
        return "/tmp/%s.stats.sock" % self.username

    @property
    def sock_stat(self):
        return "/tmp/%s.stats.sock" % self.username

    @property
    def venv(self):
        return '%s/env' % self.serve

    def export(self):
        return {
                key:getattr(self, key)
                for key in self.__class__.keys()
        }

def setup_uwsgi(project):
    conf = Conf(project)

    entry = "entry.py" # XXX
    for f in ['entry.py', 'bin/django.wsgi', 'bin/entry', 'main.py']:
        path = "%s/%s" % (conf.serve, f)
        if os.access(path, 0):
            entry = path
            break

    source = open(entry).read()
    import re

    r = re.search('as application|application = |import application', source)
    cname = 'application' if r else 'app'


    ini = render_template('conf/uwsgi.ini',
            entry=entry, callable=cname,
            **conf.export())

    putfile('%s/uwsgi.ini' % conf.home, ini)
    
def putfile(fname, contents):

    fbuf = '/tmp/buf.%d' % os.getpid()

    uwsgi = open(fbuf, 'w')
    uwsgi.write(contents)
    uwsgi.close()

    envoy.run('sudo mv %s %s' % (fbuf, fname))

def setup_nginx(project, domain, static=False):
    conf = Conf(project)

    nginx = render_template('conf/nginx.conf',
            domains= domain,
            **conf.export()
    )

    fname = '/etc/nginx/sites-enabled/%s' % conf.username
    putfile(fname, nginx)

    envoy.run('sudo /etc/init.d/nginx reload')

def do_setup(project, clone_url, domain, static=False):

    create_user(project)
    setup_key(project)
    try:
        clone_code(project, clone_url)
    except IOError:
        return 'fail-clone'

    if static:
        setup_nginx(project, domain, static=True)
        return

    try:
        setup_repo(project)
    except IOError:
        return 'fail-repo'

    setup_uwsgi(project)
    setup_nginx(project, domain)

def do_clean(project):
    return make(project, 'app_clean')

def do_key(project, **kw):
    setup_key(project)

def update_code(project):
    return make(project, 'update_code')

def do_up(project):

    try:
        oldrev = fetch_rev(project)
        update_code(project)
    except IOError:
        return 'fail-update'

    rev = fetch_rev(project)
    if rev and (rev == oldrev):
        return

    setup_repo(project)
    setup_uwsgi(project)

def fetch_key(project):
    return make(project, 'fetch_key')

def fetch_status():
    return make('-', 'fetch_status')

def fetch_status_app(name):
    try:
        return make(name, 'fetch_status_app')
    except IOError:
        return

def fetch_rev(name):
    return make(name, 'fetch_rev')

def make(project, target, env=None):
    if env:
        env = str.join(" ", [
            "%s=%s" % (k,v)
            for k, v in env.items()
        ])
    else:
        env = ""

    kw = {
            "mf": MAKEFILE,
            "app": project,
            "target": target,
            "env": env,
    }
    cmd = 'make -f %(mf)s APP=%(app)s ME=%(mf)s %(env)s %(target)s -s' % kw

    r = envoy.run(cmd)
    if r.status_code == 0:
        return r.std_out

    raise IOError("make failed %d %r" %(r.status_code, r.std_err))
