$(function(){
    $(".feeder_page").click(function(e){
	var type = $(this).attr("type");
	var page = $(this).html();
	show_spinner(type);
	// alert("You wanna see page "+page+" of "+type+" feeders");
	$.ajax({
	    url:"/retrieveFeeders/"+type+"/"+page,
	    type:"get"
	}).done(function(data){
	    // console.log(data);
	    $("#spinner").hide();
	    $("tbody."+type+"Feeders").html(data);
	})
	e.preventDefault();
	return false;
    })
})

var pal;

function show_spinner(type){
    // I tried to be clever with the window sizes and element sizes but
    // it didn't work like I expected it to.
    var left = ($(window).width() - $("#spinner").width()) / 2;
    $("#spinner").show().css("left", left);
    function headers (type){
	return ($($("tbody."+type+"Feeders").children()[0]).outerHeight() +
		$($("tbody."+type+"Feeders").children()[1]).outerHeight())
    }
    var top = ($("#title").outerHeight() +
	       $("#toolbar").outerHeight() -
	       $("#spinner").outerHeight() +
	       headers("Public"));
    function extra (x, type){
	return ($($("tbody."+type+"Feeders").children()[2]).outerHeight() *
		$("tbody."+type+"Feeders").children().length/x);
    }
    if (type == "Public"){
	top += extra(2, "Public");
    }else{
	top += (extra(1, "Public") +
		$("#Publicfeederpages").outerHeight() +
		headers("Private") + extra(2, "Private") - 60)
    }
    $("#spinner").css("top", top);
}

function ss(){
    show_spinner("Public");
    $(window).resize(function(){
	show_spinner("Public");
    })
}
