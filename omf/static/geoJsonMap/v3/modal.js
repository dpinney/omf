export { Modal };

class Modal {
    divElement;         // - The divElement is the outermost div that contains the modal's content
    #bannerElement;     // - The bannerElement contains the banner text. It's usually empty unless the user needs to be notified of something
    #containerElement;  // - The containerElement contains optional elements (e.g. buttons)
    #tableElement;      // - The table element is an actual table
    #titleElement;      // - The title element contains the optional title text

    /**
     * @returns {undefined}
     */
    constructor() {
        this.divElement = document.createElement('div');
        this.divElement.classList.add('js-div--modal');
        this.divElement.addEventListener('click', function(e) {
            // - Don't let clicks on the divElement cause the modalInsert to close
            e.stopPropagation();
        });
        this.#bannerElement = null;
        this.#containerElement = null;
        this.#tableElement = null;
        this.#titleElement = null;
    }
    
    /******************/
    /* Public methods */
    /******************/

    /**
     * @param {(string|Node)} banner - the banner to display
     * @param {string} [style=null] - An optional style class that styles the banner
     * @returns {undefined}
     */
    setBanner(banner, style=null) {
        if (this.#bannerElement === null) {
            this.#bannerElement = document.createElement('div');
            this.#bannerElement.classList.add('div--modalBanner');
            this.divElement.prepend(this.#bannerElement);
        }
        if (typeof banner === 'string') {
            const span = document.createElement('span');
            span.textContent = banner;
            this.#bannerElement.replaceChildren(span);
        } else if (banner instanceof Node) {
            this.#bannerElement.replaceChildren(banner);
        } else {
            throw TypeError('"banner" argument must be a string or Node.');
        }
        if (typeof style !== 'string' && style !== null) {
            throw TypeError('"style" argument must be a string or null.');
        }
        if (style !== null) {
            this.#bannerElement.classList.add(style);
        } else {
            // - HACK
            this.#bannerElement.classList.remove('caution');
        }
    }

    /**
     * @param {(string|Node)} title - the title to display
     * @param {string} [style=null] - An optional style that styles the title
     * @returns {undefined}
     */
    setTitle(title, style=null) {
        if (this.#titleElement === null) {
            this.#titleElement = document.createElement('div');
            this.#titleElement.classList.add('div--modalTitle');
        }
        if (this.#bannerElement === null) {
            this.divElement.prepend(this.#titleElement);
        } else {
            this.#bannerElement.after(this.#titleElement);
        }
        if (typeof title === 'string') {
            const span = document.createElement('span');
            span.textContent = title;
            this.#titleElement.replaceChildren(span);
        } else if (title instanceof Node) {
            this.#titleElement.replaceChildren(title);
        } else {
            throw TypeError('"title" argument must be a string or Node.');
        }
        if (typeof style !== 'string' && style !== null)  {
            throw TypeError('"style" argument must be a string or null');
        }
        if (style !== null) {
            this.#titleElement.classList.add(style);
        }
    }


    /**
     * @param {Array} elements - an array of elements that should occupy a table body row. null elements just append empty <td>/<td> elements
     * @param {string} [position='append'] - the location to insert the tBody row. Can be "prepend", "beforeEnd", or "append"
     * @returns {undefined}
     */
    insertTBodyRow(elements, position='append') {
        if (this.#tableElement === null) {
            this.#createTableElement();    
        }
        const tr = document.createElement('tr');
        elements.forEach(e => {
            const td = document.createElement('td');
            const div = document.createElement('div');
            if (typeof e === 'string') {
                const span = document.createElement('span');
                span.textContent = e;
                div.appendChild(span);
                td.appendChild(div)
            } else if (e instanceof Node) {
                div.appendChild(e);
                td.appendChild(div);
            } else if (e !== null) {
                throw Error(`The Table class only accepts arrays of null, Node, or string.`)
            }
            tr.appendChild(td);
        });
        if (position === 'prepend') {
            this.#tableElement.tBodies[0].prepend(tr);
        } else if (position === 'beforeEnd') {
            const lastNodeIndex = this.#tableElement.tBodies[0].children.length - 1;
            const lastNode = this.#tableElement.tBodies[0].children.item(lastNodeIndex);
            this.#tableElement.tBodies[0].insertBefore(tr, lastNode)
        } else if (position === 'append') {
            this.#tableElement.tBodies[0].appendChild(tr);
        } else {
            throw Error('Please specify a valid value for the "position" parameter: "prepend", "beforeEnd", or "append"')
        }
    }

    /**
     * @param {Array} elements - an array of elements that should occupy a table header row. null elements just append empty <td>/<td> elements
     * @param {string} [position='append'] - the location to insert the tHead row. Can be "prepend", "beforeEnd", or "append"
     * @returns {undefined}
     */
    insertTHeadRow(elements, position='append') {
        if (this.#tableElement === null) {
            this.#createTableElement();    
        }
        const tr = document.createElement('tr');
        elements.forEach(e => { 
            const th = document.createElement('th');
            const div = document.createElement('div');
            if (typeof e === 'string') {
                const span = document.createElement('span');
                span.textContent = e;
                div.appendChild(span);
                th.appendChild(div);
            } else if (e instanceof Node) {
                div.appendChild(e);
                th.appendChild(div);
            } else if (e !== null) {
                throw Error(`The Table class only accepts arrays of null, Node, or string.`)
            }
            tr.appendChild(th);
        });
        if (position === 'prepend') {
            this.#tableElement.tHead.prepend(tr);
        } else if (position === 'beforeEnd') {
            const lastNodeIndex = this.#tableElement.tHead.children.length - 1;
            const lastNode = this.#tableElement.tHead.children.item(lastNodeIndex);
            this.#tableElement.tHead.insertBefore(tr, lastNode)
        } else if (position === 'append') {
            this.#tableElement.tHead.appendChild(tr);
        } else {
            throw Error('Please specify a valid value for the "position" parameter: "prepend", "beforeEnd", or "append"')
        }
    }

    /**
     * 
     */
    addStyleClass(style, elementName) {
        if (typeof style !== 'string') {
            throw Error('The "style" argument must be a string');
        }
        if (typeof elementName !== 'string') {
            throw Error('The "elementName" argument must be a string');
        }
        switch (elementName) {
            case 'divElement':
                if (this.divElement !== null) {
                    this.divElement.classList.add(style);
                }
                break;
            case 'bannerElement':
                if (this.#bannerElement !== null) {
                    this.#bannerElement.classList.add(style);
                }
                break;
            case 'containerElement':
                if (this.#containerElement !== null) {
                    this.#containerElement.classList.add(style);
                }
                break;
            case 'tableElement':
                if (this.#tableElement !== null) {
                    this.#tableElement.classList.add(style);
                }
                break;
            case 'titleElement':
                if (this.#titleElement !== null) {
                    this.#titleElement.classList.add(style);
                }
                break;
            default:
                throw Error('"elementName" argument must be "divElement", "bannerElement", "containerElement", "tableElement", or "titleElement"');
        }
    }

    /**
     * 
     */
    removeStyleClass(style, elementName) {
        if (typeof style !== 'string') {
            throw Error('The "style" argument must be a string');
        }
        if (typeof elementName !== 'string') {
            throw Error('The "elementName" argument must be a string');
        }
        switch (elementName) {
            case 'divElement':
                if (this.divElement !== null) {
                    this.divElement.classList.remove(style);
                }
                break;
            case 'bannerElement':
                if (this.#bannerElement !== null) {
                    this.#bannerElement.classList.remove(style);
                }
                break;
            case 'containerElement':
                if (this.#containerElement !== null) {
                    this.#containerElement.classList.remove(style);
                }
                break;
            case 'tableElement':
                if (this.#tableElement !== null) {
                    this.#tableElement.classList.remove(style);
                }
                break;
            case 'titleElement':
                if (this.#titleElement !== null) {
                    this.#titleElement.classList.remove(style);
                }
                break;
            default:
                throw Error('"elementName" argument must be "divElement", "bannerElement", "containerElement", "tableElement", or "titleElement"');
        }
    }

   /**
    * @param {Node} e - an element to append to the element div
    * @param {string} [position='append'] - the location to insert the element row. Can be "prepend", "beforeEnd", or "append"
    * @returns {undefined}
    */
    insertElement(e, position='append') {
        if (!(e instanceof Node)) {
            throw Error('"e" argument must be instanceof Node');
        }
        if (this.#containerElement === null) {
            this.#createContainerElement();
        }
        if (position === 'prepend') {
            this.#containerElement.prepend(e);
        } else if (position === 'beforeEnd') {
            const lastNodeIndex = this.#containerElement.children.length - 1;
            const lastNode = this.#containerElement.children.item(lastNodeIndex);
            this.#containerElement.insertBefore(e, lastNode)
        } else if (position === 'append') {
            this.#containerElement.appendChild(e);
        } else {
            throw Error('Please specify a valid value for the "position" parameter: "prepend", "beforeEnd", or "append"')
        } 
    }

    /**
     * @param {boolean} [spinner=true] - whether to show the spinner
     * @param {string} [bannerText=null] - the centered text to display below the spinnner, if the spinner exists
     * @param {string} [style=null] - An optional style that styles the title and banner
     * @returns {undefined}
     */
    showProgress(showSpinner=true, bannerText=null, style=null) {
        if (typeof showSpinner !== 'boolean') {
            throw TypeError('"showSpinner" argument must be a boolean.');
        }
        if (typeof bannerText !== 'string' && bannerText !== null) {
            throw TypeError('"bannerText" argument must be a string or null.');
        }
        if (typeof style !== 'string' && style !== null) {
            throw TypeError('"style" argument must be a string or null.');
        }
        const outerDiv = document.createElement('div');
        if (showSpinner) {
            const img = document.createElement('img');
            img.src = '/static/geoJsonMap/v3/spinner.gif';
            outerDiv.appendChild(img);
        }
        if (bannerText !== null) {
            const innerDiv = document.createElement('div');
            // - I don't want span. A span gives me regular-sized font. I want banner-sized font
            //const span = document.createElement('span');
            //span.textContent = bannerText;
            innerDiv.textContent = bannerText;
            //innerDiv.appendChild(span);
            outerDiv.appendChild(innerDiv);
        }
        this.setBanner(outerDiv, style);
    }

    // *********************
    // ** Private methods ** 
    // *********************

    #createTableElement() {
        this.#tableElement = document.createElement('table');
        this.#tableElement.classList.add('table--modal');
        this.#tableElement.appendChild(document.createElement('thead'));
        this.#tableElement.appendChild(document.createElement('tbody'));
        this.divElement.appendChild(this.#tableElement);
    }

    #createContainerElement() {
        this.#containerElement = document.createElement('div');
        this.#containerElement.classList.add('div--modalElementContainer');
        this.divElement.appendChild(this.#containerElement);
    }
}