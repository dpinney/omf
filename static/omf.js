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