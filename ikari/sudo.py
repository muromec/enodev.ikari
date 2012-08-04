import envoy
import sys
import os
import pwd

def setup(mod):
    setup.mod = mod
setup.mod = None

def sudo(f, *a, **kw):

    user = kw.pop('_user', 'root')
    cwd = kw.get('_cwd', None)
    if cwd is None:
        cwd = pwd.getpwnam(user).pw_dir

    os.chdir('/')
    print 'run', f, f.__module__, sys.argv, sys.executable
    entry = sys.modules['__main__']
    path = [os.path.dirname(entry.__file__)]+sys.path
    entry_mod = setup.mod or sys.argv[0]

    cmd = 'sudo -u %s env PYTHONPATH=%s %s %s %s %s %s %s %s' % (
            user,
            str.join(':',path),
            sys.executable,
            __file__,
            entry_mod,
            f.__module__,
            f.__name__,
            str.join(',', a),
            cwd,
    )
    r = envoy.run(cmd)
    print '>> ', r.std_out
    print '>! ', r.std_err
    return r
    

if __name__ == '__main__':
    entryname,modname,fname,args,cwd = sys.argv[1:]
    os.chdir(cwd)

    entryname = entryname.rsplit('.', 1)[0]
    print entryname
    mod = __import__(entryname, fromlist=['*'])

    if modname == '__main__':
        pass
    else:
        mod = __import__(modname, fromlist=['*'])

    f = getattr(mod, fname)

    args = args.split(',')
    kwargs = {}

    del os.environ['PYTHONPATH']
    f(*args, **kwargs)
