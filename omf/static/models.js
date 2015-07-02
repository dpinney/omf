// Javascript functions shared by all OMF models.

function init() {
	// If we have input, put it back.
	if (allInputData != null) {
		restoreInputs()
		$("#modelName").prop("readonly", true)
	}
	// Depending on status, show different things.
	if (modelStatus == "finished") {
		console.log("FINISHED")
		$(".postRun").css('display', 'block')
		$(".postRunInline").css('display', 'inline-block')
	} else if (modelStatus == "running") {
		console.log("RUNNING")
		$(".running").css('display', 'block')
		$(".runningInline").css('display', 'inline-block')
		$("input").prop("readonly", true)
		$("select").prop("disabled", true)
	} else /* Stopped */ {
		if (allInputData != null) {
			$(".stopped").show()
			$(".stoppedInline").show()
		} else {
			console.log("PRERUN")
			$(".preRun").css('display', 'inline-block')
		}
	}
	// Hide buttons we don't use:
	modelUser = allInputData["user"]
	if (modelUser == "public" && currentUser != "admin") {
		$("button#deleteButton").hide();
		$("button#publishButton").hide();
		$("button#rerunButton").hide();
	}
}

function restoreInputs() {
	// Restore all the input values that were used and stored in allInputData.json
	gebi("titleText").innerHTML = allInputData.modelName
	for (index in allInputData) {
		try {document.querySelector("#" + index).value = allInputData[index]}
		catch(err){}
	}
}

function delimitNumbers(nStr) {
	// Add commas to numbers and round to a decent length.
	nStr += ''
	x = nStr.split('.')
	x1 = x[0]
	x2 = x.length > 1 ? '.' + x[1] : ''
	rgx = /(\d+)(\d{3})/
	while (rgx.test(x1)) {
		x1 = x1.replace(rgx, '$1' + ',' + '$2')
	}
	return x1 + x2
}

function cancelModel() {
	params = {user:allInputData.user,
		modelName:allInputData.modelName,
		modelType:allInputData.modelType}
	post_to_url("/cancelModel/", params, "POST")
}

function deleteModel() {
	if (confirm("Deleting this model cannot be undone. Continue?")){
		post_to_url("/delete/Model/"+allInputData.user+"/"+allInputData.modelName, {}, "POST")
	} else {
		return false
	}
}

function publishModel() {
	newName = prompt("Publish a copy with name", allInputData.modelName)
	while (! /^[\w\s]+$/.test(newName)){
		newName = prompt("Public a copy with new name, only letters, digits and underscore are allowed in the model name.\nPlease rename your new model", allInputData.modelName)
	}
	if (newName) {
		$.ajax({url:"/uniqObjName/Model/public/" + newName}).done(function(data) {
			if (data.exists) {
				alert("There is already a public Model named " + newName)
				publishModel()
			} else {
				post_to_url("/publishModel/" + allInputData.user + "/" + allInputData.modelName+"/", {"newName":newName})
			}
		})
	}
}

function duplicateModel() {
	newName = prompt("Create a duplicate with name", allInputData.modelName)
	while (! /^[\w\s]+$/.test(newName)){
		newName = prompt("Public a copy with new name, only letters, digits and underscore are allowed in the model name.\nPlease rename your new model", allInputData.modelName)
	}
	if (newName) {
		$.ajax({url:"/uniqObjName/Model/" + allInputData.user + "/" + newName}).done(function(data) {
			if (data.exists) {
				alert("There is already a model named " + newName)
				duplicateModel()
			} else {
				post_to_url("/duplicateModel/" + allInputData.user + "/" + allInputData.modelName+"/", {"newName":newName})
			}
		})
	}
}

function checkModelName() {
	var newName = modelName.value
	$.ajax({
		url: "/uniqObjName/Model/" + currentUser + "/" + newName
	}).done(function (data) {
		if (data.exists) {
			alert("You already have a Model named '" + newName + "', please choose a different name.")
		}
		else{	
			inputForm.submit()			
		}
	})	
}