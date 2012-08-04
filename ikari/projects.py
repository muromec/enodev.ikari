from flask import render_template, request, redirect, flash

from app import app
from models import Project

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

@app.route('/projects/<name>/op', methods=['POST'])
def op(name):
    if request.form:
        opcode = request.form.keys()[0]
        flash(opcode)
    return redirect('/projects/%s/'%name)
