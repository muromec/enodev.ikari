import json
import ops

from flaskext.redtask import push

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

def status(project, status):
    project.status = status
    project.save()

def push_status(push_id, project, _status, **kw):
    status(project, _status)
    if not push_id:
        return

    data = {
        "typ": "project.status",
        "status": _status,
        "project": project.name,
    }
    data.update(kw)
    push(push_id, data)

    push(push_id, {
        "typ": "flash",
        "project": project.name,
        "op": _status,
    })

