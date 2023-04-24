export { TopTab };
'use strict';

class TopTab {
    divElement;         // Container for tabDivElement and contentDivElement;
    #contentDivElement; // Container for content. Contains other divs that contain content
    #tabDivElement;     // Container for tabs. Contains other divs that are tabs
    #tabMap;            // Mapping from tabs to content

    constructor() {
        this.divElement = document.createElement('div');
        this.divElement.classList.add('div--topTab');
        this.#tabDivElement = document.createElement('div');
        this.#tabDivElement.classList.add('div--topTabTabContainer');
        this.divElement.appendChild(this.#tabDivElement);
        this.#contentDivElement = document.createElement('div');
        this.#contentDivElement.classList.add('div--topTabContentContainer')
        this.divElement.appendChild(this.#contentDivElement);
        this.#tabMap = {};
    }

    /**
     * - Add a tab and some content
     * 
     * @param {(string|Node)} label - a string or node label a tab
     * @param {Node} content - A node (e.g. a div) that will be displayed when the tab is clicked on
     */
    addTab(label, content) {
        if (!(content instanceof Node)) {
            throw Error('"content" argument must be an instance of Node.');
        }
        if (this.#tabMap.hasOwnProperty(label)) {
            throw Error('The "label" argument must be unique across all tabs.');
        }
        const tab = document.createElement('div');
        const that = this;
        tab.addEventListener('click', function() {
            that.#selectTab(this);
        });
        const span = document.createElement('span');
        if (typeof label === 'string') {
            span.textContent = label;
        } else {
            span.appendChild(label);
        }
        tab.appendChild(span);
        this.#tabDivElement.appendChild(tab);
        this.#contentDivElement.appendChild(content);
        this.#tabMap[label] = {
            tab: tab,   
            content: content
        };
    }

    removeTab(label) {
        if (!this.#tabMap.hasOwnProperty(label)) {
            throw Error(`This TopTab does not have a tab with label ${label}`);
        }
        const {tab, content} = this.#tabMap[label];
        tab.remove();
        content.remove();
        delete this.#tabMap[label];
    }

    getTab(label) {
        return this.#tabMap[label];
    }

    // *********************
    // ** Private methods ** 
    // *********************

    /**
     * - @param {HTMLDivElement} div - The <div></div> element that was clicked. The div element has the event listener instead of the inner span (or
     *   SVG) because the whole div should be clickable, especially if I choose not to visually round off my tabs. If the inner span (or SVG) is
     *   clicked, the event will bubble up to the div
     */
    #selectTab(div) {
        Object.values(this.#tabMap).forEach(obj => {
            if (obj.tab !== div) {
                obj.tab.classList.remove('selected');   
                obj.content.classList.remove('selected');
            } else if (!(obj.tab.classList.contains('selected'))) {
                obj.tab.classList.add('selected');
                obj.content.classList.add('selected');
            }
        }); 
    }
}