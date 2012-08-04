from flask import render_template, request, redirect, flash

from app import app
from models import Project
from task import defer

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
    task(name, op=opcode)
    return redirect('/projects/%s/'%name)

@defer
def task(name, op):
    print 'task', name, op
