from flask import request, render_template, redirect, g
from flask.ext.auth import get_current_user_data, logout

from app import app
from models import User

@app.before_request
def set_user():
    
    data = get_current_user_data()
    if data:
        g.user = User(data=data)
    else:
        g.user = None

@app.route('/login', methods=['POST', 'GET'])
def login():
    def render(**kw):
        return render_template('login.html', **kw)

    if request.method != 'POST':
        return render()

    form = User.form.login(data=request.form)
    user = User.get(login=form.login)
    if not user:
        return render(login=form.login, err="No user")

    ok = user.authenticate(form.password or '')
    if not ok:
        return render(login=form.login, err="wrong password")
        
    return redirect('/projects/')

@app.route('/logout')
def view_logout():
    logout()
    return redirect('/')


def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrap(*a, **kw):
        if not g.user or not g.user.login:
            return redirect('/login')

        return f(*a, **kw)

    return wrap
