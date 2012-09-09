function post_to_url(path, params, method) {
    method = method || 'post' // Set method to post by default, if not specified.

    var form = document.createElement('form')
    form.setAttribute('method', method)
    form.setAttribute('action', path)

    for(var key in params) {
        if(params.hasOwnProperty(key)) {
            var hiddenField = document.createElement('input')
            hiddenField.setAttribute('type', 'hidden')
            hiddenField.setAttribute('name', key)
            hiddenField.setAttribute('value', params[key])

            form.appendChild(hiddenField)
         }
    }

    document.body.appendChild(form)
    form.submit()
}

function dropPill(thisButton, name) {
    currentStatus = getComputedStyle(thisButton.nextSibling.nextSibling).display
    if (currentStatus == 'inline-block' || currentStatus == 'block') {
        thisButton.nextSibling.nextSibling.style.display = 'none'
        thisButton.innerHTML = name + ' ▾'
    }
    else {
        thisButton.nextSibling.nextSibling.style.display = 'inline-block'
        thisButton.innerHTML = name + ' ▴'
    }
}

function gebi(id) {
    // This shortens a much-used method name.
    return document.getElementById(id)
}

function clone(obj) {
    // Deep copy of a given obj.
    if (null == obj || "object" != typeof obj) return obj;
    var copy = obj.constructor();
    for (var attr in obj) {
        if (obj.hasOwnProperty(attr)) copy[attr] = obj[attr];
    }
    return copy;
}

function tableClear(table) {
  try {
    while (table.rows.length>0) table.deleteRow(table.rows.length-1)
  }
  catch (err) {
    // Catch: we didn't have any rows.
  }
}

function getRadioSetting (className) {
    // Get which radio button is set for a group with a given className.
    value='';
    radios = document.getElementsByClassName(className);
    for (x in radios) {if (radios[x].checked) value = radios[x].value}
    return value
}
