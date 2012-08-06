import os
import json

from flask import render_template, request, redirect, flash

from ikari.app import app
from ikari.login import login_required
from models import Project
from flaskext.redtask import defer

def get_ops():
    username = os.getenv('USER') or ''
    if 'ikari' in username:
        import ops
        return ops

    import rpyc
    global conn ## XXX no refs to conn
    conn = rpyc.classic.connect("drct.whoisdb.me", 12345)
    ops = conn.modules.ops
    conn.modules.os.chdir('/var/')
    return ops

ops = get_ops()

def rstatus(name=None):
    _status = ops.fetch_status()
    if not _status:
        return {}
    status = json.loads(_status)

    status_dict = {
            v['id'].split('/')[-2]:v
            for v in status['vassals']
    }
    if name:
        return status_dict.get('app-%s' % name)

    return status_dict

def rstatus_name(name):
    _status = ops.fetch_status_app(name)
    if not _status:
        return

    try:
        status = json.loads(_status)
    except ValueError:
        return

    wcount = 0
    wfail = 0
    err = 0
    req = 0

    workers = status['workers']

    for w in workers:
        if w['status'] == 'cheap':
            continue

        wcount += 1
        err += w[u'exceptions']
        req += w['requests']
        if not w['apps']:
            wfail += 1

    if wfail:
        s = 'fail'
    elif err:
        s = 'warn'
        if err == req:
            s = 'fail'
    elif not wcount:
        s = 'idle'
    else:
        s = 'ok'

    status = {
            "wcount": wcount,
            "wfail": wfail,
            "err": err,
            "req": req,
            "state": s,
    }

    return status

def rev(name):
    return ops.fetch_rev(name)

@app.route('/projects/')
@login_required
def projects():
    plist = Project.all()
    status_dict = rstatus()

    for p in plist:
        p._alive = ('app-%s' % p.name) in status_dict
        if p._alive:
            p._stats = rstatus_name(p.name)
            if not p._stats:
                p._alive = False
        else:
            p._stats = None

        if not p._alive and p.status=='ok':
            p.status='fail'

        p._rev = rev(p.name)

    return render_template('projects.html',
            project_list=plist,
    )

@app.route('/projects/add', methods=['GET', 'POST'])
@login_required
def add():
    form = Project.form.add

    if request.method == 'POST':
        proj = Project.form.add(request.form)
        if proj.validate():
            proj.save()
            return redirect('/projects')

        form = proj

    return render_template('project_add.html',
            form = form
    )


@app.route('/projects/<name>/')
@login_required
def show(name):
    project = Project.get(name=name)
    if not project:
        return "No", 404

    (project._field('status')).locked = True
    status = rstatus_name(name)

    return render_template('project_show.html',
            project=project, status=status)

@app.route('/projects/<name>/op', methods=['POST', 'GET'])
@login_required
def op(name):
    opcode = request.form.get('op')
    if not opcode:
        return save(name)

    flash(opcode)
    task(op=opcode, project=name)
    return redirect('/projects/%s/'%name)

def save(name):
    project = Project.get(name=name)
    if not project:
        return 'No', 404

    project.update(request.form)
    project.save()

    flash('Saved')
    return redirect('/projects/%s/'%name)

def status(project, status):
    project.status = status
    project.save()

@defer
def task(op, *a, **kw):
    project = Project.get(name=kw['project'])

    if op == 'setup':

        status(project, 'install')

        ops.do_setup(
                project=project.name,
                clone_url=project.repo_url,
                domain=project.domain,
                static=project.template=='static'
        )
        status(project, 'ok')

        copy_key(kw['project'])


    elif op == 'clean':

        status(project, 'ok')

        ops.do_clean(*a, **kw)

        project.ssh_key = None
        project.status = 'inactive'
        project.save()

    elif op == 'key':

        ops.do_key(*a, **kw)
        status(project, 'key')
        copy_key(kw['project'])


@defer
def copy_key(name):
    project = Project.get(name=name)

    project.ssh_key = ops.fetch_key(name)
    project.save()
