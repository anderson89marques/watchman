/**
 * Created by anderson on 23/03/16.
 */
var ws = new WebSocket(location.href.replace('http', 'ws').replace('control', 'ws'));
console.log('ws://' + location.host + '/ws');
console.log(location.href.replace('http', 'ws').replace('control', 'ws'));

status_exit = {"OK": "success", "WARNING": "warning", "CRITICAL": "danger", "WAITING": "info"};

function add_status_color(exit_tag, exit_status){
    console.log(exit_tag, exit_status);
    var info = exit_tag.hasClass("info");
    var success = exit_tag.hasClass("success");
    var warning = exit_tag.hasClass("warning");
    var danger = exit_tag.hasClass("danger");
    if(info){
        exit_tag.removeClass("info");
    }else if(success){
        exit_tag.removeClass("success");
    }else if(warning){
        exit_tag.removeClass("warning");
    }else if(danger){
        exit_tag.removeClass("danger");
    }
    exit_tag.addClass(status_exit[exit_status]);
}

function add_all_colors(){
    console.log("All Color");
    var trs = $(".panel.panel-default tbody").find("tr");
    console.log(trs);

    for(var i = 0;i < trs.size(); i++){
        var tds = $(trs[i]).find("td");
        if(tds.size() > 0){
            add_status_color($(tds[1]), $(tds[1]).text()) // $(tds[1]).text() tem o exite_status
        }
    }
}

// Adicionando as cores dos exit_status
add_all_colors();

// Atualizando as tables com informações gerais
control_total_services();

function control_total_services(){
    var trs = $(".panel.panel-default tbody").find("tr");
    console.log(trs.size());

    var contOK = 0;
    var contWar = 0;
    var contCri = 0;
    var contWai = 0;
    var contTotalProblems = 0;

    for(var i = 0;i < trs.size(); i++){
        var tds = $(trs[i]).find("td");
        if(tds.size() > 0){

            if($(tds[1]).text() === "OK"){
                contOK++;
            } else if($(tds[1]).text() === "WARNING"){
                contWar++;
                contTotalProblems++;
            } else if($(tds[1]).text() === "CRITICAL"){
                contCri++;
                contTotalProblems++;
            } else if($(tds[1]).text() === "WAITING"){
                contWai++;
                contTotalProblems++;
            }
        }
    }

    $("#totServices").find("td.success").text(contOK);
    $("#totServices").find("td.warning").text(contWar);
    $("#totServices").find("td.danger").text(contCri);
    $("#totServices").find("td.info").text(contWai);
    $("#totAll").find("td.danger").text(contTotalProblems);
}

ws.onmessage = function (event) {
    var resp = JSON.parse(event.data);
    console.log("ONmessage");
    var tr_id = "#" + resp.host_name + resp.name;
    var tds = $(tr_id).find("td");
    add_status_color($(tds[1]), resp.exit_status);

    $(tds[1]).text(resp.exit_status);
    $(tds[2]).text(resp.exit_status_info);
    $(tds[3]).text(resp.last_update);

    control_total_services();
};


$(".start_btn").on("click", function(e){ start_job(e)});
$(".stop_btn").on("click", function(e){ stop_job(e)});
$(".remove_btn").on("click", function(e){ remove_job(e)});

function start_job(e){
    send_actions(e, "Start");
}

function stop_job(e){
    send_actions(e, "Stop");
}

function remove_job(e){
    send_actions(e, "Remove");
}


function send_actions(e, act){
    var tr = $(e.target).parent().parent().parent();
    console.log($(tr));
    var td = $(tr).find("td")[0];
    var td_start = $(tr).find("td")[6];
    var bt_start = $(td_start).find("button");
    var td_stop = $(tr).find("td")[7];
    var bt_stop = $(td_stop).find("button");

    console.log($(td));
    console.log($(bt_start));
    var service_name = $(td).text();
    console.log(service_name);

    $.ajax({
        url: "/action",
        type: "Post",
        data:{action: act, serv_name: service_name},
        success: function(data){
            console.log(data);
            if(data === "Stop"){
                $(bt_start).attr("disabled", false);
                $(bt_start).css({"background-color": "#4cae4c"});

                $(bt_stop).attr("disabled", true);
                $(bt_stop).css({"background-color": "#ac2925"});
            }else if(data == "Start"){
                $(bt_start).attr("disabled", true);
                $(bt_start).css({"background-color": "#ac2925"});

                $(bt_stop).attr("disabled", false);
                $(bt_stop).css({"background-color": "#4cae4c"});
            }
        }
    });
}