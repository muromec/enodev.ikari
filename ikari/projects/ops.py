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
    username = 'app-%s' % project
    ssh_a = '/var/lib/ikari/keys/%s' % username

    if not os.access(ssh_a, 0):
        envoy.run('ssh-keygen -f %s -N \\"\\"' % ssh_a)

    try:
        home = pwd.getpwnam(username).pw_dir
    except KeyError:
        return

    ssh_dir = "%s/.ssh/" % home
    ssh_h = "%s/.ssh/id_rsa" % home

    if not os.access(ssh_dir, 0):
        os.mkdir(ssh_dir)

    if not os.access(ssh_h, 0):
        envoy.run('cp %s %s' % (ssh_a, ssh_h))
        envoy.run('cp %s.pub %s.pub' % (ssh_a, ssh_h))

    envoy.run('chown %s -R %s' % (username, ssh_dir))

def clone_code(project, url):
    username = 'app-%s' % project
    home = pwd.getpwnam(username).pw_dir
    serve = '%s/serve' % home

    cmd = "git clone %(url)s %(serve)s" % {
        "home": home,
        "username": username,
        "url": url,
        "serve": serve,
    }
    r = envoy.run(cmd, timeout=10)
    print cmd
    print r.std_err
    print r.std_out
    print r.history

def setup_repo_buildout(project):
    print 'setup bb'

    r = envoy.run('env/bin/pip install zc.buildout')
    print r.std_out
    print r.std_err


    r = envoy.run('env/bin/buildout -s')
    print r.std_out
    print r.std_err

def setup_repo_venv(project):
    print 'setup venv'
    r = envoy.run('env/bin/pip install -r requirements.txt')
    print r.std_out
    print r.std_err

def setup_repo(project):
    username = 'app-%s' % project
    home = pwd.getpwnam(username).pw_dir
    serve = '%s/serve' % home
    os.chdir(serve)

    r = envoy.run('virtualenv env')
    print r.std_out
    print r.std_err

    if os.access('buildout.cfg', 0):
        setup_repo_buildout(project)
    elif os.access('requirements.txt', 0):
        setup_repo_venv(project)

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
    for f in ['entry.py', 'bin/entry', 'main.py']:
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
    username = 'app-%s' % project

    sudo(create_user, project)
    sudo(setup_key, project)
    sudo(clone_code, project, clone_url, _user=username)
    if static:
        sudo(setup_nginx, project, domain, static=True)
        return

    sudo(setup_repo, project, _user=username)
    sudo(setup_uwsgi, project)
    sudo(setup_nginx, project, domain)

def do_clean(project, **kw):
    username = 'app-%s' % project
    home = pwd.getpwnam(username).pw_dir
    serve = '%s/serve' % home

    nconf = '/etc/nginx/sites-enabled/%s' % username,
    uini = '%s/uwsgi.ini' % home

    assert home.startswith('/home/app')
    envoy.run('sudo rm -rf %s/reload %s/.ssh %s %s %s'%(
        home, home, serve, uini, nconf))

def do_key(project, **kw):
    sudo(setup_key, project)

def update_code(project):
    username = 'app-%s' % project
    home = pwd.getpwnam(username).pw_dir
    serve = '%s/serve' % home

    os.chdir(serve)

    envoy.run("git reset --hard")
    envoy.run("git pull --rebase")

def do_up(project):
    username = 'app-%s' % project

    sudo(update_code, project, _user=username)
    sudo(setup_repo, project, _user=username)
    sudo(setup_uwsgi, project)

def fetch_key(project):
    username = 'app-%s' % project
    ssh_a_pub = '/var/lib/ikari/keys/%s.pub' % username

    return open(ssh_a_pub).read()

def fetch_status():
    tcpsoc = socket(AF_INET, SOCK_STREAM)
    try:
        tcpsoc.connect(('localhost', 1235))
    except error:
        return

    data = ''
    while True:
        c = tcpsoc.recv(1024)
        if not c:
            break
        data += c

    tcpsoc.close()
    return data

def fetch_status_app(name):
    s = socket(AF_UNIX, SOCK_STREAM)

    try:
        s.connect("/tmp/app-%s.stats.sock" % name)
    except:
        return
    
    data = ''
    while True:
        c = s.recv(1024)
        if not c:
            break
        data += c

    s.close()
    return data

def _fetch_rev(name):
    username = 'app-%s' % name
    home = pwd.getpwnam(username).pw_dir
    serve = '%s/serve' % home
    os.chdir(serve)

    f = '%h %s'
    r = envoy.run("git log --format=\\'%s\\' -n 1" % f)
    return r.std_out

def fetch_rev(name):
    username = 'app-%s' % name
    return sudo(_fetch_rev, name, user=username).strip()

sudo_setup(__name__)
