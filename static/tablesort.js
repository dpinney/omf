
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

function attachEvt(selector, dataType, attr){
    $(selector).click(function(){
        $.ajax({
            url:"/sort/"+dataType+"/"+attr,
            type:"POST"
        }).done(function(){
            if (dataType == "Model"){
                updateModels()
            }
            if (dataType == "Feeder"){
                updateFeeders()
            }
                
        })
    })
}

$(function(){
    updateModels()
    updateFeeders()
    var setup = [
        ["#mname", "Model", "name"],
        ["#mdate", "Model", "ctime"],
        ["#fname", "Feeder", "name"],
        ["#fdate", "Feeder", "ctime"],
    ]
    setup.forEach(function(e){
        attachEvt(e[0], e[1], e[2])
    })
})