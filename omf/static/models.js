/**
 * Initalize page
 * @param {null}
 * @return {null}
 */
function init() {
	// If we have input, put it back.
	if (allInputData != null) {
		restoreInputs()
		$("#modelName").prop("readonly", true)
	}
	// Depending on status, show different things.
	if (modelStatus == "finished") {
		console.log("FINISHED")
		$(".postRun").show()
	} else if (modelStatus == "running") {
		console.log("RUNNING")
		$(".running").show()
		$("input").prop("readonly", true)
		$("select").prop("disabled", true)
	} else /* Stopped */ {
		if (allInputData != null) {
			$(".stopped").show()
		} else {
			console.log("PRERUN")
			$(".preRun").show()
		}
	}
}

/**
 * Restore all the input values that were used and stored in allInputData.json
 * @param {null}
 * @return {null}
 */
function restoreInputs() {
	gebi("titleText").innerHTML = allInputData.modelName
	for (index in allInputData) {
		try {document.querySelector("#" + index).value = allInputData[index]}
		catch(err){}
	}
}

/**
 * Make sure each field matches its validation regex.
 * @param {null}
 * @return {boolean} returnVal
 */
function validateForm() {
	allFields = $("input")
	returnVal = true
	for (i=0; i < allFields.length; i++) {
		allFields[i].style["border-color"] = "white"
		currVal = allFields[i].value + ""
		regex = allFields[i].getAttribute("data-validRegex")
		if (regex != null && currVal.match(regex) != currVal) {
			allFields[i].style["border-color"] = "crimson"
			returnVal = false
		}
	}
	if (returnVal == false) {alert("Form values bordered in red don't match the required format.")}
	return returnVal
}

/**
 * Cancel model, hander function of "cancel" button
 * @param {null}
 * @return {null}
 */
function cancelModel() {
	params = {user:allInputData.user,
		modelName:allInputData.modelName,
		modelType:allInputData.modelType}
	post_to_url("/cancelModel/", params, "POST")
}

/**
 * Delete model, handler function of "delete" button
 * @param {null}
 * @return {null}
 */
function deleteModel() {
	if (confirm("Deleting this model cannot be undone. Continue?")){
		post_to_url("/delete/Model/"+allInputData.user+"/"+allInputData.modelName, {}, "POST")
	} else {
		return false
	}
}

/**
 * Publish model, handler function of "publish" button
 * @param {null}
 * @return {null}
 */
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

/**
 * Duplicate model, handler function of "duplicate" button
 * @param {null}
 * @return {null}
 */
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

/**
 * Little function here to get discloser triangles
 * @param {Object} clickedObject
 * @return {null}
 */
function toggleAdvanced(clickedObject) {
	siblings = clickedObject.parentNode.parentNode.parentNode.querySelectorAll('.advancedOption')
	for (i=0;i<siblings.length;i++) {
		visible = (getComputedStyle(siblings[i])['display'] == 'none')
		if (visible) {
			siblings[i].style.display='table-row'
		} else {
			siblings[i].style.display='none'
		}
	}
	if (visible) {code = 9660} else {code = 9654}
		clickedObject.textContent = String.fromCharCode(code) + ' Advanced Options'
}