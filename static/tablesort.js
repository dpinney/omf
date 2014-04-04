
function updateTable(url, tblselector, tmpselector, dname){
    var compiled = _.template($(tmpselector).html())
    $.ajax({
        url:url
    }).done(function(data){
        $(tblselector).html("")
        data.data.forEach(function(d){
            var o = {}
            o[dname] = d
            $(tblselector).html($(tblselector).html()+compiled(o))
        })
    })
}

function updateModels(){
    updateTable("/getAllData/Model", ".Analyses", "#jsmetadata", "md")
}

function updateFeeders(){
    updateTable("/getAllData/Feeder", ".Feeders", "#feedertemplate", "feed")
}

$(function(){
    updateModels()
    updateFeeders()
    $("#mname").click(function(){
        $.ajax({
            url:"/sort/Model/name",
            type:"POST"
        }).done(updateModels)
    })
    $("#fname").click(function(){
        $.ajax({
            url:"/sort/Feeder/name",
            type:"POST"
        }).done(updateFeeders)
    })
    $("#fdate").click(function(){
        $.ajax({
            url:"/sort/Feeder/ctime",
            type:"POST"
        }).done(updateFeeders)
    })
    $("#mdate").click(function(){
        $.ajax({
            url:"/sort/Model/ctime",
            type:"POST"
        }).done(updateModels)
    })
})