import envoy
import sys
import os
import pwd

def setup(mod):
    setup.mod = mod
setup.mod = None

__file__ = os.path.abspath(__file__)

def sudo(f, *a, **kw):

    user = kw.pop('_user', 'root')
    cwd = kw.get('_cwd', None)
    if cwd is None:
        cwd = pwd.getpwnam(user).pw_dir

    os.chdir('/')
    entry_mod = setup.mod or sys.argv[0]

    cmd = 'sudo -u %s env PYTHONPATH=%s %s %s %s %s %s %s %s' % (
            user,
            str.join(':',sys.path),
            sys.prefix+'/bin/python',
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
    return r.std_out
    

if __name__ == '__main__':
    entryname,modname,fname,args,cwd = sys.argv[1:]
    os.chdir(cwd)

    entryname = entryname.rsplit('.', 1)[0]
    mod = __import__(entryname, fromlist=['*'])

    if modname == '__main__':
        pass
    else:
        mod = __import__(modname, fromlist=['*'])

    f = getattr(mod, fname)

    args = args.split(',')
    kwargs = {}

    del os.environ['PYTHONPATH']
    ret = f(*args, **kwargs)
    print ret
