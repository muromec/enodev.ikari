import os
from fabric.api import run, hosts, cd
from fabric.operations import put, sudo

GEOFRONT = 'root@46.182.30.158'

@hosts(GEOFRONT)
def root_key():
    run('uname -r')
    run('mkdir -p /root/.ssh/')
    pubkey = '%s/.ssh/id_rsa.pub' % (os.getenv('HOME'))
    put(pubkey, '/root/.ssh/authorized_keys')

PKG = [
        'uwsgi',
        'uwsgi-plugin-python',
        'git',
        'python',
        'python-virtualenv',
        'python-zc.buildout',
        'nginx',
        'mongodb',
]
@hosts(GEOFRONT)
def pkg():
    run('apt-get install -y %s' % str.join(' ',PKG))


@hosts(GEOFRONT)
def app_init(name):
    run('useradd %s --create-home' % name)
    with cd('/home/%s'%name):
        sudo('mkdir .ssh || true', user=name)
        run('rm -f ./.ssh/id_rsa')
        sudo('ssh-keygen -f ./.ssh/id_rsa -N ""', user=name)

@hosts(GEOFRONT)
def app_setup(name, url):
    def r(*a):
        sudo(*a, user=name)

    with cd('/home/%s'%name):
        r('[ -d serve ] || git clone %s serve' % url)

    with cd('/home/%s/serve'%name): 
        r('buildout2.7')
