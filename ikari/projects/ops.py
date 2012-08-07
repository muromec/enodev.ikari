import pwd
import os
from socket import *

import envoy
from enodev.sudo import sudo, setup as sudo_setup

def create_user(project):
    username = 'app-%s' % project
    try:
        pwd.getpwnam(username)
        return
    except KeyError:
        pass

    envoy.run("useradd %s --create-home" % username)


def setup_key(project):
    return make(project, 'setup_key')

def clone_code(project, url):
    return make(project, clone_code, env={"URL":url})

def setup_repo(project):
    return make(project, 'setup_repo')

def setup_uwsgi(project):
    tpl_f = '/var/lib/ikari/uwsgi.ini'
    tpl = open(tpl_f).read()

    username = 'app-%s' % project
    home = pwd.getpwnam(username).pw_dir
    rel = open('%s/reload' % home, 'w')
    rel.write('')
    rel.close()

    uid = pwd.getpwnam(username).pw_uid
    serve = '%s/serve' % home

    entry = "entry.py" # XXX
    for f in ['entry.py', 'bin/django.wsgi', 'bin/entry', 'main.py']:
        path = "%s/%s" % (serve, f)
        if os.access(path, 0):
            entry = path
            break

    source = open(entry).read()
    import re

    r = re.search('as application|application = |import application', source)
    cname = 'application' if r else 'app'

    ini = tpl %{
            "entry": entry,
            "sock": "/tmp/%s.sock" % username,
            "stats_sock": "/tmp/%s.stats.sock" % username,
            "home": home,
            "serve": serve,
            "uid": uid,
            "callable": cname,
    }

    if os.access('%s/env/bin/activate' % serve, 0):
        ini += '\nvenv = %s/env\n' % serve

    uwsgi = open('%s/uwsgi.ini' % home, 'w')
    uwsgi.write(ini)
    uwsgi.close()

def setup_nginx(project, domain, static=False):
    tpl_f = '/var/lib/ikari/'
    if static:
        tpl_f += 'nginx-static.conf'
    else:
        tpl_f += 'nginx.conf'

    tpl = open(tpl_f).read()
    
    username = 'app-%s' % project
    home = pwd.getpwnam(username).pw_dir

    sock = "/tmp/%s.sock" % username
    serve = '%s/serve' % home

    conf = tpl % {
            "project": project,
            "domains": domain,
            "sock": sock,
            "serve": serve,
    }

    nginx = open('/etc/nginx/sites-enabled/%s' % username, 'w')
    nginx.write(conf)
    nginx.close()

    envoy.run('sudo /etc/init.d/nginx reload')

def do_setup(project, clone_url, domain, static=False):

    sudo(create_user, project)
    setup_key(project)
    try:
        clone_code(project, clone_url)
    except IOError:
        return 'fail-clone'

    if static:
        sudo(setup_nginx, project, domain, static=True)
        return

    try:
        setup_repo(project)
    except IOError:
        return 'fail-repo'

    sudo(setup_uwsgi, project)
    sudo(setup_nginx, project, domain)

def do_clean(project):
    username = 'app-%s' % project
    home = pwd.getpwnam(username).pw_dir
    serve = '%s/serve' % home

    nconf = '/etc/nginx/sites-enabled/%s' % username,
    uini = '%s/uwsgi.ini' % home

    assert home.startswith('/home/app')
    envoy.run('sudo rm -rf %s/reload %s/.ssh %s %s %s'%(
        home, home, serve, uini, nconf))

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
    sudo(setup_uwsgi, project)

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
            "mf": "./ikari/projects/Makefile.ops",
            "app": project,
            "target": target,
            "env": env,
    }
    cmd = 'make -f %(mf)s APP=%(app)s ME=%(mf)s %(env)s %(target)s -s' % kw

    r = envoy.run(cmd)
    if r.status_code == 0:
        return r.std_out

    raise IOError("make failed %d %r" %(r.status_code, r.std_err))

sudo_setup(__name__)
