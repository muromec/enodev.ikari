
from flask import render_template, request, redirect, flash, g

from ikari.app import app
from ikari.login import login_required

from models import Project
from utils import rstatus, rstatus_name
from task import task

@app.before_request
def menu():
    g.head_menu = [
            ('/projects/', 'Projects'),
    ]

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
    push_id = request.form.get('_push_id')
    if not opcode:
        return save(name)

    if not push_id:
        flash(opcode)

    task(op=opcode, project_id=name, push_id=push_id)
    return redirect('/projects/%s/'%name)

def save(name):
    project = Project.get(name=name)
    if not project:
        return 'No', 404

    project.update(request.form)
    project.save()

    flash('Saved')
    return redirect('/projects/%s/'%name)
