import pwd

from flask import render_template, request, redirect, flash

from app import app
from models import Project
from task import defer
import ops

@app.route('/projects/')
def projects():
    plist = Project.all()
    return render_template('projects.html',
            project_list=plist
    )

@app.route('/projects/add', methods=['GET', 'POST'])
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

import rpyc
conn = rpyc.classic.connect("drct.whoisdb.me", 12345)
ops = conn.modules.ops
conn.modules.os.chdir('/var/')

@app.route('/projects/<name>/')
def show(name):
    project = Project.get(name=name)
    if not project:
        return "No", 404

    return render_template('project_show.html',
            project = project)

@app.route('/projects/<name>/op', methods=['POST', 'GET'])
def op(name):
    opcode = request.form.get('op', 'ya')
    flash(opcode)
    task(op=opcode, project=name)
    return redirect('/projects/%s/'%name)

@defer
def task(op, *a, **kw):
    project = Project.get(name=kw['project'])
    kw['clone_url'] = project.repo_url

    print ops
    print ops.run_op
    ops.run_op(op, *a, **kw)

    copy_key(kw['project'])

@defer
def copy_key(name):
    print 'copy ssh key back'
    project = Project.get(name=name)

    project.ssh_key = ops.fetch_key(name)
    project.save()
