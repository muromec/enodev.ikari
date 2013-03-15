import os
import envoy

from pkg_resources import resource_filename
MAKEFILE = os.path.abspath(resource_filename("ikari.projects", "Makefile.ops"))


runners = {}

class LocalRunner(object):
    MAKEFILE = MAKEFILE
    def run(self, cmd):
        r = envoy.run(cmd)
        return r.status_code, r.std_out
    
    def putfile(self, fname, contents):

        fbuf = '/tmp/buf.%d' % os.getpid() # XXX

        uwsgi = open(fbuf, 'w')
        uwsgi.write(contents)
        uwsgi.close()

        envoy.run('sudo mv %s %s' % (fbuf, fname))

class SSHRunner(object):
    MAKEFILE = '/tmp/Makefile.ops'
    def __init__(self, host):
        from ssh.client import AutoAddPolicy
        import ssh
        self.client = ssh.SSHClient()
        self.client.load_host_keys('.ssh/known_hosts')
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.client.connect(host, 22, 'root', key_filename='.ssh/id_rsa')

        self.sftp = self.client.open_sftp()
        self.makefile_init()

    def makefile_init(self,):
        f = self.sftp.open(self.MAKEFILE, 'w')
        f.write(open(MAKEFILE,).read())

    def run(self, cmd):
        inp_f, out_f, err_f = self.client.exec_command(cmd)
        err = err_f.read()
        # XXX check errorcode
        if not err:
            ret = out_f.read()
            return 0, ret

        return 1, '' 
 
    def putfile(self, fname, contents):
        f = self.sftp.open(fname, 'w')
        f.write(contents)
        f.close()

def get_runner(key='local'):

    r = runners.get(key)
    if r:
        return r

    if key == 'local':
        r = LocalRunner()
    else:
        r = SSHRunner(key)
    
    runners[key] = r

    return r

def get_host(project):
    if project == 'texr':
        key = '109.234.152.149'
        return key
    elif project == 'texr-driver':
        key = '37.200.68.226'
        return key

    return 'local'

def make(project, target, env=None):
    runner = get_runner(get_host(project))

    if env:
        env = str.join(" ", [
            "%s=%s" % (k,v)
            for k, v in env.items()
        ])
    else:
        env = ""

    kw = {
            "mf": runner.MAKEFILE,
            "app": project,
            "target": target,
            "env": env,
    }
    cmd = 'make -f %(mf)s APP=%(app)s ME=%(mf)s %(env)s %(target)s -s' % kw

    status_code, std_out = runner.run(cmd)
    if status_code == 0:
        return std_out

    raise IOError("make failed %d %s" % (status_code, target))

def putfile(project, fname, contents):
    runner = get_runner(get_host(project))
    runner.putfile(fname, contents)
