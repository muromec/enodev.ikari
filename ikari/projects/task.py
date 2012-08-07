from flaskext.redtask import defer, push
from functools import partial

from models import Project
from utils import push_status, rev
import ops

@defer
def task(op, project_id, push_id):
    f = globals()['task_%s' % op]
    project = Project.get(name=project_id)
    if not project:
        # XXX: cry to log
        return

    s = partial(push_status, push_id, project)
    s._id = push_id
    f(project, s)

def task_setup(project, s):
    s('install')

    ret = ops.do_setup(
            project=project.name,
            clone_url=project.repo_url,
            domain=project.domain,
            static=project.template=='static'
    )

    if ret:
        return s(ret)

    s('ok')

    project.rev = rev(project.name)
    copy_key(project.name, s._id)

def task_up(project, s):

    s('updating')
    ret = ops.do_up(project.name)
    if ret:
        return s(ret)

    project.rev = rev(project.name)
    s('ok', rev=project.rev)

def task_clean(project, s):

    s('cleaning')

    ops.do_clean(project.name)

    project.ssh_key = None
    s('inactive')

    push(s._id, {
        "typ": "project.key",
        "key": "",
        "project": project.name,
    })

def task_key(project, s):

    ops.do_key(project.name)
    s('key')
    copy_key(project.name, s._id)
 

@defer
def copy_key(name, push_id=None):
    project = Project.get(name=name)

    project.ssh_key = ops.fetch_key(name)
    project.save()

    if not push_id:
        return

    push(push_id, {
        "typ": "project.key",
        "key": project.ssh_key,
        "project": project.name,
    })
