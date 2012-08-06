var push_connect = function(open_fn, msg_fn) {
    var origin = location.hostname,
        ws_host = 'ws.'+origin+':8080';

    if (origin == 'localhost' || origin == '127.0.0.1') {
        ws_host = 'localhost:8080';
    }
    var ws = new WebSocket("ws://"+ws_host+"/_ws");
    ws.onopen = function() {open_fn()};
    ws.onmessage = function (evt) {msg_fn(evt)};

    return ws
}

$(document).ready(function(){
    var open_fn = function(){
        push.send('yoba');
    };
    var msg_fn = function(evt) {
        if (push.id === undefined) {
            push.id = evt.data;
            push_id_event(push.id);
            return
        }
        var msg = jQuery.parseJSON(evt.data);
        if(msg.typ == 'flash') {
            var flash_el = $("<div>");
            flash_el.addClass("alert");
            if (msg.op.substr(0, 4) === 'fail') {
                flash_el.addClass("alert-error");
            }
            if (msg.op.substr(0, 2) === 'ok') {
                flash_el.addClass("alert-success");
            }
            flash_el.text(msg.op);
            $(".alerts").append(flash_el);
            location.hash = 'alerts';
            location.hash = '';
        }
        if(msg.typ == 'project.status') {
            $("form p").text(msg.status);
            if(msg.rev !== undefined) {
                $("#form_rev_id").val(msg.rev);
            }
        }
        if(msg.typ == 'project.key') {
            $("#form_ssh_key_id").val(msg.key);
        }
    };
    var push_id_event = function(id) {
        $("input[name=_push_id]").val(id);
    };

    var push = push_connect(open_fn, msg_fn);

    $btn = $("button[name=op]");
    $btn.on('click', function() {
        location.hash = '';
        var op = $(this).val(),
            ok = function(data) {
                return true;
            };
        $.post('op', {
            "_push_id": $("input[name=_push_id]").val(),
            "op": op,
        }, ok);
        return false;
    })

})

