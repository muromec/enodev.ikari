import pwd
import os

import envoy
from sudo import sudo, setup

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
    home = pwd.getpwnam(username).pw_dir
    ssh =  "%s/.ssh/id_rsa.pub" % home
    if os.access(ssh, 0):
        return

    ssh_dir = "%s/.ssh/" % home
    if not os.access(ssh_dir, 0):
        os.mkdir(ssh_dir)

    envoy.run('ssh-keygen -f %s/.ssh/id_rsa -N \\"\\"' % home)

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

def setup_repo(project):
    username = 'app-%s' % project
    home = pwd.getpwnam(username).pw_dir
    serve = '%s/serve' % home
    os.chdir(serve)

    r = envoy.run('virtualenv env')
    print r.std_out
    print r.std_err

    r = envoy.run('env/bin/pip install zc.buildout')
    print r.std_out
    print r.std_err


    r = envoy.run('env/bin/buildout -s')
    print r.std_out

    print r.std_err

def do_setup(project, clone_url):
    username = 'app-%s' % project

    sudo(create_user, project)
    sudo(setup_key, project, _user=username)
    sudo(clone_code, project, clone_url, _user=username)
    sudo(setup_repo, project, _user=username)

def do_clean(project, **kw):
    username = 'app-%s' % project
    home = pwd.getpwnam(username).pw_dir

    assert home.startswith('/home/app')

    envoy.run('sudo deluser %s' % username)
    envoy.run('sudo rm -rf %s' % home)

def fetch_key(project):
    username = 'app-%s' % project
    home = pwd.getpwnam(username).pw_dir
    ssh =  "%s/.ssh/id_rsa.pub" % home

    return open(ssh).read()

setup(__name__)
