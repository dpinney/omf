function fit_table(){
	var raw_height = $("#selBody").height()+$("#daButtons").height()+$("#selHead").height();
	var win_height = window.innerHeight * 0.6;
	$("#selected").css("height", win_height > raw_height ? raw_height : win_height)
    // $("#selected").css("border", "1px solid black");
}

$(window).resize(fit_table);

function create_table (){
	deselect();
	for (prop in treeData){
		if (prop == "object" || prop == "module"){
			$("#objmod").html(prop)
			$("#value").html(treeData[prop])
	}else if (prop != 'from' && prop != 'to' && prop != 'parent' && prop != 'file'){ // Avoid editing machine-written properties!
		var valueEl
		if (prop == "configuration"){
			valueEl = $("<a>").html(treeData[prop]).attr("href", "#").click(function(e){
				var myname = $(this).html()
				
				$("#searchTerm").val("\"name\":\""+myname+"\"")
				findNext()
				var theButton = $.makeArray($("button")).filter(function(b){return $(b).html().indexOf("Find") > -1})[0]
				var dispStatus = theButton.nextSibling.nextSibling.style.display
				if(dispStatus == "" || dispStatus == "none")
					dropPillAndStay(theButton, "Find")
				e.preventDefault()
				return false
			})
		}
		else
			valueEl = treeData[prop]
		$("#body").append($("<tr>")
			.append($("<td>").html(prop))
			.append($("<td>").html(valueEl)))
	}
	
}
}

function selectNode(){
	create_table();
	$("#selected").show();
	$("#selected table").show()
	fit_table();
}

function deselect(){
	$("#objmod, #value, #body").html("")
	$("#selected").css("height", "auto");
	$("#editButtonRow").show()
	$("#otherButtons").hide();
	$("#selected table").hide()
	$("#selected").hide();
}

function validation(selector, testfunc, error_msg){
	var invalid = false;
	$.makeArray($(selector)).forEach(function(e){
		if (testfunc(e)){
			$(e).css("border", "1px solid red");
			if(!invalid)
				$(e).focus();
			invalid = true;
		}
	})
	if (invalid){
		alert(error_msg);
	}
	return invalid;
}

function validate_blanks(selector){
	return validation(selector, function(e){
		return $(e).val().trim() == "";
	})
}

function validate_name(selector){
	return validation(selector, function(e){
		var m = $(e).val().match(/[A-z0-9_]+/);
		return m == null || m  != $(e).val();
	}, "Invalid field values.  Letters, numbers, underscores, no spaces.")
}

$(function(){
	var delete_prop_button = $("<button>")
	.addClass("deleteButton")
	.addClass("deleteProperty")
	.html("╳")

	$("#selected").hide();
	$("#editButton").click(function(e){
		$("#editButtonRow").hide();
		$("#otherButtons").show();
		$("#body").html("")
		for (prop in treeData){
			if (prop != "object" && prop != "module"){
				var tr = $("<tr>")
				.append($("<td>").addClass("propertyName").html(prop))
				.append($("<td>")
					.append($("<input>")
						.val(treeData[prop])
						.attr("name", prop)
						.attr("type", "text")))
				if (prop != "name")
					tr.prepend($("<td>")
						.append(delete_prop_button.clone()))
				else
					tr.prepend($("<td>"))
				$("#body").append(tr);
			}
		}
		console.log(treeData);
	})
	$("#cancelButton").click(function(e){
		$("#editButtonRow").show();
		$("#otherButtons").hide();
		$("#body").html("");
		selectNode();
	})
	$("#saveObject").click(function(e){
		if (validate_blanks("#body input"))
			return;
		if(validate_name(".newPropertyName"))
			return;
		function isNameAlreadyUsed(testValue) {
	    // Helper function to make sure we don't make non-unique names.
	    for (leaf in tree) {
	    	for (attrKey in tree[leaf]) {
	    		if (attrKey == 'name' && tree[leaf][attrKey] == testValue) {
	    			return true
	    		}
	    	}
	    }
	    return false
	}
	var propNames = $("#body td.propertyName");
	for(i=0; i<propNames.length; i++){
		var key = propNames[i].innerHTML;
		var newValue = $("#body input[name="+key+"]").val();
		var oldValue = treeData[key];
		if (key=='name') {
		// 1. If the name is already the name of something else, skip the renaming.
		if (isNameAlreadyUsed(newValue) && oldValue != newValue) {
		    // cell.innerHTML = oldValue
		    $("#body input[name=name]").val(oldValue);
		    alert('Please choose a unique name.');
		}
		else {
			treeData[key] = newValue
		    // cell.innerHTML = newValue
		    // k.innerHTML = key
		    // 2. If the name is unique, go through EVERY attribute in the tree and replace the old name with the new one.
		    
		    for (leaf in tree) {
		    	for (attrKey in tree[leaf]) {
		    		if (oldValue == tree[leaf][attrKey]) {console.log(tree[leaf]); tree[leaf][attrKey] = newValue}
		    	}
		    }
		    // 3. Go through the nodes and replace the name there too. UGH!
		    nodeIndex = findIndex(nodes, 'name', oldValue)
		    if (nodeIndex != "") {nodes[nodeIndex]['name'] = newValue}
		}
}else{
	treeData[key] = newValue;
}
}
Object.keys(treeData).filter(function(e){
	return $.makeArray(propNames).map(function(x){
		return x.innerHTML;
	}).indexOf(e) == -1;
}).forEach(function(e){
	if (e != "object" && e != "module")
		delete treeData[e];
})
$.makeArray($("#body input.newPropertyName")).map(function(e){
	return e.value;
}).forEach(function(e, i){
	if (e.trim() != "")
		treeData[e] = $("#body input.newPropertyValue")[i].value;
})
$("#otherButtons").hide();
$("#editButtonRow").show();
selectNode();
})
$(document).on("click", ".deleteProperty", function(e){
	$(this).parent().parent().remove();
})
$("#addAttribute").click(function(e){
	if (validate_blanks(".newPropertyName, .newPropertyValue"))
		return;
	var new_name = $("<input>")
	.addClass("newPropertyName")
	.attr("type", "text");
	
	$("#body").append($("<tr>")
		.append($("<td>")
			.append(delete_prop_button.clone()))
		.append($("<td>")
			.append(new_name))
		.append($("<td>")
			.append($("<input>")
				.addClass("newPropertyValue")
				.attr("type", "text"))));
	fit_table();
	new_name.focus();
})
$("#deleteObject").click(function(e){
	deleteObject(ti);
})
})
