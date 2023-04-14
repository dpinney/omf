export { DropdownDiv };

class DropdownDiv {
    divElement;         // - The divElement is the outermost div that contains the DropdownDiv's button (if any) and content
    buttonElement;      // - The buttonElement is an optional button that can be clicked to expand and collapse the contentDivElement
    contentDivElement;  // - The contentDivElement is the div that expands and collapses as needed 
    
    /**
     * @returns {undefined}
     */
    constructor() {
        this.divElement = document.createElement('div');
        this.divElement.classList.add('js-div--dropdown');
        this.buttonElement = null;
        this.contentDivElement = null;
    }

    // ********************
    // ** Public methods ** 
    // ********************

   /**
    * @param {Node} e - an element to append to the content div
    * @param {string} [position='append'] - the location to insert the element row. Can be "prepend", "beforeEnd", or "append"
    * @returns {undefined}
    */
    insertElement(e, position='append') {
        if (!(e instanceof Node)) {
            throw Error('"e" argument must be instanceof Node');
        }
        if (this.contentDivElement === null) {
            this.#createContentDivElement();
        }
        if (position === 'prepend') {
            this.contentDivElement.prepend(e);
        } else if (position === 'beforeEnd') {
            const lastNodeIndex = this.contentDivElement.children.length - 1;
            const lastNode = this.contentDivElement.children.item(lastNodeIndex);
            this.contentDivElement.insertBefore(e, lastNode) 
        } else if (position === 'append') {
            this.contentDivElement.appendChild(e);
        } else {
            throw Error('Please specify a valid value for the "position" parameter: "prepend", "beforeEnd", or "append"')
        }
    }

    /**
     * @param {(string|Node)} button - the button to display
     * @param {boolean} showArrow - whether to append an arrow SVG to the button that rotates in response to clicks
     * @returns {undefined}
     */
    setButton(button, showArrow=false) {
        let svgWasRotated = false;
        if (this.buttonElement === null) {
            this.buttonElement = document.createElement('button');
            this.buttonElement.classList.add('js-button--dropdown');
            this.divElement.prepend(this.buttonElement);
            if (this.contentDivElement === null) {
                this.#createContentDivElement();
            }
            this.buttonElement.addEventListener('click', this.#getContentDivDisplayFunction());
        } else {
            const svg = this.buttonElement.lastChild;
            if (svg instanceof SVGElement) {
                if (svg.classList.contains('rotated')) {
                    svgWasRotated = true;
                }
            }
        }
        if (typeof button === 'string') {
            const span = document.createElement('span'); 
            span.textContent = button;
            this.buttonElement.replaceChildren(span);
        } else if (button instanceof Node) {
            this.buttonElement.replaceChildren(button);
        } else {
            throw TypeError('"button" argument must be a string or Node.');
        }
        if (showArrow) {
            const svg = document.createElementNS('http://www.w3.org/2000/svg','svg'); 
            svg.classList.add('js-svg--dropdown');    
            svg.setAttribute('width', '40px');
            svg.setAttribute('height', '40px');
            svg.setAttribute('viewBox', '0 0 10 10');
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', 'M4,2.5L6.5,5L4,7.5L3,6.5L4.5,5L3,3.5L4,2.5');
            svg.appendChild(path);
            if (svgWasRotated) {
                svg.classList.add('rotated');
            }
            this.buttonElement.appendChild(svg);
        }
    }

    /**
     * - Return a function that is intended to be attached to any other element to control the display of the entire DropdownDiv
     * @returns {function}
     */
    getDropdownDivShowHideFunction() {
        const that = this;
        return function() {
            that.divElement.classList.toggle('expanded');
        };
    }

    /**
     * 
     */
    addStyleClass(style) {
        if (typeof style !== 'string') {
            throw Error('The "style" argument must be a string');
        }
        this.divElement.classList.add(style);
    }

    /**
     * 
     */
    removeStyleClass(style) {
        if (typeof style !== 'string') {
            throw Error('The "style" argument must be a string');
        }
        this.divElement.classList.remove(style);
    }

    // *********************
    // ** Private methods ** 
    // *********************

    /**
     * - Return a function that is intended to be attached to the button in the DropdownDiv to control the display of the content div of the
     *   DropdownDiv
     * @returns {function}
     */
    #getContentDivDisplayFunction() {
        const that = this;
        return function() {
            // - I don't need to manage the content of this.contentDivElement because any additional event listeners added later should be managing
            //   the creation and removal of content in response to clicks
            that.contentDivElement.classList.toggle('expanded');
            that.buttonElement.classList.toggle('expanded');
            const svg = that.buttonElement.lastChild;
            if (svg instanceof SVGElement) {
                svg.classList.toggle('rotated');
            }
            if (!that.contentDivElement.classList.contains('expanded')) {
                for (const innerDiv of that.contentDivElement.getElementsByClassName('js-div--dropdown')) {
                    // - There is no button, just a content div
                    if (innerDiv.children[0] instanceof HTMLDivElement) {
                        // - I'm going to assume that if there is no button, then the creation of the content in the content div is being controlled
                        //   somewhere else, so I shouldn't clear the content div or do anything to it except visually collapse it
                        innerDiv.children[0].classList.remove('expanded');
                    } else if (innerDiv.children[0] instanceof HTMLButtonElement) {
                        // - If there is a button, then I should simulate a click on that button, but only if that button was open. If the button was
                        //   closed, don't click on it. Clicking on the button should take care of the svg if it exists
                        const contentDiv = innerDiv.children[1];
                        if (contentDiv.classList.contains('expanded')) {
                            innerDiv.children[0].click();
                        }
                        
                    }
                }
                // - Old, buggy way of handling things
                //for (const innerSvg of that.contentDivElement.getElementsByClassName('js-svg--dropdownSvg')) {
                //    innerSvg.classList.remove('rotated');    
                //}
                //for (const innerContentDiv of that.contentDivElement.getElementsByClassName('js-div--dropdownContentDiv')) {
                //    innerContentDiv.classList.remove('expanded');
                //}
            }
        }
    }

    #createContentDivElement() {
        this.contentDivElement = document.createElement('div');
        this.contentDivElement.classList.add('js-div--dropdownContent');
        this.divElement.appendChild(this.contentDivElement);
    }
}