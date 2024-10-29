export { DropdownDiv };

/**
 * - A DropdownDiv cannot just be one div because there is always needs to be something to click on to show/hide the div. At a minimum, there must be
 *   a container div and an inner content div
 */
class DropdownDiv {

    div;
    #contentDiv

    constructor() {
        this.div = document.createElement('div');
        this.div.classList.add('dropdown-div');
        this.#contentDiv = document.createElement('div');
        this.#contentDiv.classList.add('contentdiv');
        this.div.append(this.#contentDiv);
    }

    /**
     * - Insert an element into the content div. If I want to add an element to this div, just use DOM access methods
     */
    insertElement({element=null, position='append'}={}) {
        if (!(element instanceof Node)) {
            throw Error('The "element" argument must be instanceof Node.');
        }
        if (!['append', 'beforeEnd', 'prepend'].includes(position)) {
            throw Error('The "position" argument must be "append", "beforeEnd", or "prepend".');
        }
        if (position === 'prepend') {
            this.#contentDiv.prepend(element);
        } else if (position === 'beforeEnd') {
            const lastNodeIndex = this.#contentDiv.children.length - 1;
            const lastNode = this.#contentDiv.children.item(lastNodeIndex);
            this.#contentDiv.insertBefore(element, lastNode) 
        } else {
            this.#contentDiv.append(element);
        }
    }

    /**
     * - Return a function that can be attached to something (e.g. a button) to control the display of a DropdownDiv. The DropdownDiv shouldn't care
     *   what element uses this function (e.g. a button with a chevron svg vs. a button with a lightning bolt svg)
     * @param {Function} outerFunc - A function that is called with this "dropdown-div" div as an argument. There can be no innerFunc. The outerFunc
     *  is capable of grabbing all of the inner nested DropdownDivs and acting on them. It's too confusing to have an innerFunc as well. 
     * @returns {Function} A function that can control the display of the DropdownDiv
     *
     * E.g. say that when the outer contentdiv is closed, all nested contentdivs should also close. If THIS function first removes "-expanded" from a
     * nested contentdiv before calling the innerFunc with the nested DropdownDiv, how will the innerFunc click on the button of the nested
     * DropdownDiv without erroneously re-adding the "-expanded" class to the nested contentdiv? The innerFunc wouldn't know how to handle this
     * without also knowing whether THIS function removed the "-expanded" class BEFORE the innerFunc was called or AFTER the innerFunc was called.
     * Since the innerFunc has to know about the implementation of THIS function, it's better to omit the argument entirely
     */
    getToggleFunction({outerFunc=null}={}) {
        const that = this;
        return function() {
            that.#contentDiv.classList.toggle('-expanded');
            if (outerFunc !== null) {
                outerFunc(that.div);
            }
        }
    }

    isExpanded() {
        return this.#contentDiv.classList.contains('-expanded');
    }
}