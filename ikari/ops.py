import envoy
import pwd

def run_op(op, *a, **kw):
    ops[op](*a, **kw)

def create_user(project):
    username = 'app-%s' % project
    try:
        pwd.getpwnam(username)
        return
    except KeyError:
        pass

    envoy("useradd %s --create-home" % username)


def setup_key(project):
    username = 'app-%s' % project
    home = pwd.getpwnam(username).pw_dir

    envoy("[ -d %(ssh)s ] || sudo -u %(username)s mkdir %(ssh)s" % {
        "ssh": "%/.ssh" % home,
        "username": username,
    })

    envoy('sudo -u %s ssh-keygen -f %s/.ssh/id_rsa -N ""' % (
        username, home))

def clone_code(project, url):
    username = 'app-%s' % project
    home = pwd.getpwnam(username).pw_dir
    serve = '%s/serve' % home

    envoy('sudo -u %s git clone %s %s' % (username, url, serve))

def setup_repo(project):
    username = 'app-%s' % project
    home = pwd.getpwnam(username).pw_dir
    serve = '%s/serve' % home

    envoy('cd %(serve)s; sudo -u %(username)s buildout2.7' % {
        "serve": serve,
        "username": username,
    })


def do_setup(project, clone_url):
    create_user(project)
    setup_key(project)
    clone_code(project, clone_url)
    setup_repo(project)

ops = {
        "setup": do_setup,
}

