export { SearchModal };
import { DropdownDiv } from './dropdownDiv.js';
import { FeatureController } from './featureController.js';
import { FeatureDropdownDiv } from './featureDropdownDiv.js';
import { getCirclePlusSvg, getTrashCanSvg } from './treeFeatureModal.js';
import { Modal } from './modal.js';

/**
 * - A SearchModal doesn't have an underlying Feature instance, unlike a TreeFeatureModal and a ModalFeatureModal
 */
class SearchModal {
    #controller;                        // - ControllerInterface instance for this SearchModal
    #keySelects;                        // - An array of HTMLSelectElement instances
    #modal;                             // - A single Modal instance for this SearchModal
    #observables;                       // - An array of ObservableInterface instances
    #searchResults;                     // - An array of features
    #dropdownDiv;                       // - A plain DropdownDiv instance
    #searchResultControllers;           // - The controllers that are managing the FeatureDropdownDivs displayed in the side bar
    #searchResultfeatureDropdownDivs;   // - The FeatureDropdownDivs displayed in the side bar
    #removed;                           // - Whether this SearchModal instance has already been deleted
    static #nonSearchableProperties = ['treeProps', 'formProps', 'urlProps', 'componentType'];

    /**
     * - The features that can be searched depend entirely on the features that are managed by the controller
     * @param {FeatureController} controller - a ControllerInterface instance
     * @returns {undefined}
     */
    constructor(controller) {
        if (!(controller instanceof FeatureController)) {
            throw TypeError('"controller" argument must be an instance of FeatureController');
        }
        this.#controller = controller;
        //this.#observables = null;
        // - Do this to cover when the controller is a component manager
        this.#observables = this.#controller.getObservables();
        this.#observables.forEach(ob => ob.registerObserver(this));
        this.#keySelects = [];
        this.#modal = null;
        this.#searchResults = null;
        //this.#searchResults = [...this.#observables];
        this.#dropdownDiv = new DropdownDiv();
        this.#dropdownDiv.addStyleClass('sideNav', 'divElement');
        this.#searchResultControllers = [];
        this.#searchResultfeatureDropdownDivs = [];
        this.#removed = false;
        this.renderContent();
        this.#search();
    }

    // *******************************
    // ** ObserverInterface methods **
    // *******************************

    /**
     * - Remove this ObserverInterface instance (i.e. "this") from the ObservableInterface instance (i.e. "observable") that has been deleted, and
     *   perform other actions as needed
     * @param {Object} observable - an instance of ObservableInterface that this Observer is observing
     * @returns {undefined}
     */
    handleDeletedObservable(observable) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!this.#removed) {
            observable.removeObserver(this);
            this.#observables = this.#observables.filter(ob => ob !== observable);
            this.#searchResults = this.#searchResults.filter(ob => ob !== observable);
            this.#dropdownDiv.setButton(`Search Results: ${this.#searchResults.length}`, true);
            this.#dropdownDiv.buttonElement.getElementsByTagName('span')[0].classList.add('indent1');
            if (this.#observables.length === 0) {
                this.remove();
            } else {
                // - Refresh key selects, do not renderContent()
            }
        }
    }

    /**
     * - Update this ObserverInterface instance (i.e. "this") based on the coordinates of the ObservableInterface instance (i.e. "observable") that
     *   have just changed and perform other actions as needed
     * @param {Object} observable - an instance of ObservableInterface that this Observer is observing
     * @param {Array} oldCoordinates - the old coordinates of the observable prior to the change in coordinates
     * @returns {undefined}
     */
    handleUpdatedCoordinates(observable, oldCoordinates) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!(oldCoordinates instanceof Array)) {
            throw TypeError('"oldCoordinates" argument must be an array.');
        }
        // - Refresh key selects, do not renderContent()
    }

    /**
     * - Update this ObserverInstance (i.e. "this") based on the property of the ObservableInterface instance (i.e. "observable") that has just
     *   changed and perform other actions as needed
     * @param {Object} observable - the observable that this observer is observing
     * @param {string} propertyKey - the property key of the property that has been created/changed/deleted in the observable
     * @param {(string|Object)} oldPropertyValue - the previous value of the property that has been created/changed/deleted in the observable
     * @param {string} namespace - the namespace of the property that has been created/changed/deleted in the observable
     * @returns {undefined}
     */
    handleUpdatedProperty(observable, propertyKey, oldPropertyValue, namespace='treeProps') {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be a string.');
        }
        if (typeof namespace !== 'string') {
            throw TypeError('"namespace" argument must be a string.');
        }
        // - Refresh key selects, do not renderContent()
    }

    // ********************
    // ** Public methods **
    // ********************

    /**
     * - This is only supposed to be called once on page load
     * @returns {HTMLDivElement}
     */
    getDOMElement() {
        return this.#modal.divElement;
    }

    /**
     * - This is only supposed to be called once on page load
     * @returns {HTMLDivElement}
     */
    getSearchResultsElement() {
        return this.#dropdownDiv.divElement;
    }
    
    /**
     * - Some modals need to be removed, even when there is no change to the underlying FeatureGraph
     *  - A SearchModal will probably never need to be removed, but I provide this method just in case.
     * @returns {undefined}
     */
    remove() {
        // - Do not deregister this.#controller from the same observables. It's possible that the controller is managing multiple views 
        //  - The controller has its own remove() method that can be called
        if (!this.#removed) {
            this.#observables.forEach(ob => ob.removeObserver(this));
            this.#observables = null;
            this.#modal.divElement.remove();
            this.#keySelects = null;
            this.#removed = true;
        }
    }

    /**
     * @returns {undefined}
     */
    renderContent() {
        if (this.#controller.isComponentManager) {
            // - Do nothing. Components aren't created or destroyed while the user is using the interface
        } else {
            if (this.#observables !== null) {
                this.#observables.forEach(ob => ob.removeObserver(this));
            }
            this.#observables = this.#controller.observableGraph.getObservables(f => !f.isModalFeature() && !f.isComponentFeature() && f.getProperty('treeKey', 'meta') !== 'omd');
            this.#controller.setIDs(this.#observables.map(f => f.getProperty('treeKey', 'meta')));
            this.#observables.forEach(ob => ob.registerObserver(this));
        }
        const modal = new Modal();
        modal.addStyleClass('outerModal',   'divElement');
        modal.addStyleClass('searchModal',  'divElement');
        // - David doesn't want a title
        //modal.setTitle('Search Objects');
        //modal.addStyleClass('horizontalFlex',       'titleElement');
        //modal.addStyleClass('centerMainAxisFlex',   'titleElement');
        //modal.addStyleClass('centerCrossAxisFlex',  'titleElement');
        modal.insertTBodyRow([null, null, this.#getKeySelect(), this.#getOperatorSelect(), null], 'beforeEnd');
        modal.insertTBodyRow([this.#getAddRowButton()], 'append', ['absolute']);
        modal.addStyleClass('centeredTable', 'tableElement');
        modal.insertElement(this.#getSearchButton());
        modal.insertElement(this.#getRefreshButton());
        modal.addStyleClass('verticalFlex',         'containerElement');
        modal.addStyleClass('centerMainAxisFlex',   'containerElement');
        modal.addStyleClass('centerCrossAxisFlex',  'containerElement');
        if (this.#modal === null) {
            this.#modal = modal;
        } else if (document.body.contains(this.#modal.divElement)) {
            this.#modal.divElement.replaceWith(modal.divElement);
            this.#modal = modal;
        } else {
            throw Error('Error when creating a SearchModal.');
        }
    }
    
    // *********************
    // ** Private methods ** 
    // *********************

    /**
     * - Set this.#searchResults, but only populate this.#dropdownDiv.divElement with content when the button is clicked because adding all of those
     *   divs slows the page down
     * @returns {undefined}
     */
    #search() {
        // - Set this.#searchResults to be an array of a subset of the observables that are managed by this.#controller


        // - Iterate over the modal to build search criteria function
        
        // - Filter all of the observables from this.#controller using the search criteria function

        // - Set this.#searchResults equal to the returned observables

        // - Change the ids in this.#featureDropdownDivController to match those in this.#searchResults
        //  - this.#featureDropdownDivController needs to deregister itself from all of its old observables
        //  - this.#featureDropdownDivController needs to register itself on all of the new observables

        // - Call this.#featureDropdownDiv.renderContent()
        //  - this.#featureDropdownDiv will ask its controller (this.#featureDropdownDivController) for the observables it should use
        //      - this.#featureDropdownDiv needs to deregister itself from all of the old observables. It can't get that information from
        //        this.#featureDropdownDivController because this.#featureDropdowndDivController will already have had its own observables updated. To
        //        deal with this, this.#featureDropdownDiv needs to set this.#observables in the constructor. Then, in renderContent(), it will
        //        deregister itself from every observable in this.#observables, ask its controller for new observables, then register itself on the
        //        new observables and set this.#observables to equal the new observables.
        //  - Since I've already updated this.#featureDropdownDivController, this.#featureDropdownDiv should display the new search results
        //  - I shouldn't have to interact with the DOM because renderContent() will replace the old div with the new div

        // - I don't ever have to create a new FeatureController instance or a new FeaturedropdownDiv instance, so there's less risk of memory leaks
        //  - However, FeatureController needs a method to change its IDs and every observer needs to store an internal array of this.#observables
        //  - Everywhere in the application, I should only be creating new FeatureController instances on page load. I shouldn't be creating new
        //    FeatureController instances in response to button clicks or anything like that

        const searchCriteria = [];
        for (const tr of this.#modal.divElement.getElementsByTagName('tr')) {
            const keySelect = tr.querySelector('[data-role="keySelect"]');
            // - I only care about rows that have a keySelect
            if (keySelect !== null) {
                const key = keySelect[keySelect.selectedIndex].value;
                const namespace = keySelect[keySelect.selectedIndex].dataset.namespace;
                const operatorSelect = tr.querySelector('[data-role="operatorSelect"]');
                const operator = operatorSelect[operatorSelect.selectedIndex].value;
                let valueInputValue = tr.querySelector('[data-role="valueInput"]');
                if (valueInputValue !== null) {
                    valueInputValue = valueInputValue.value;
                }
                let logic = tr.querySelector('[data-role="andOrSelect"]');
                if (logic !== null) {
                    logic = logic[logic.selectedIndex].value;
                } else {
                    // - First row gets an implicit "and"
                    logic = 'and';
                }
                const searchCriterion = {
                    logic: logic,
                };
                if (operator === 'exists') {
                    searchCriterion.searchFunction = function(ob) {
                        return ob.hasProperty(key, namespace);
                    }
                }
                if (operator === '! exists') {
                    searchCriterion.searchFunction = function(ob) {
                        return !ob.hasProperty(key, namespace);
                    };
                }
                if (operator === '=') {
                    searchCriterion.searchFunction = function(ob) {
                        if (ob.hasProperty(key, namespace)) {
                            const value = ob.getProperty(key, namespace);
                            if (!isNaN(+value)) {
                                return +value === +valueInputValue;
                            } else {
                                return ob.getProperty(key, namespace) === valueInputValue;
                            }
                        }
                        return false;
                    };
                }
                if (operator === '!=') {
                    searchCriterion.searchFunction = function(ob) {
                        if (ob.hasProperty(key, namespace)) {
                            const value = ob.getProperty(key, namespace);
                            if (!isNaN(+value)) {
                                return +value !== +valueInputValue;
                            } else {
                                return ob.getProperty(key, namespace) !== valueInputValue;
                            }
                        }
                        return false;
                    };
                }
                if (operator === 'contains') {
                    searchCriterion.searchFunction = function(ob) {
                        if (ob.hasProperty(key, namespace)) {
                            return ob.getProperty(key, namespace).includes(valueInputValue);
                        }
                        return false;
                    }
                }
                if (operator === '! contains') {
                    searchCriterion.searchFunction = function(ob) {
                        if (ob.hasProperty(key, namespace)) {
                            return !ob.getProperty(key, namespace).includes(valueInputValue);
                        }
                        return false;
                    }
                }
                if (operator === '<') {
                    searchCriterion.searchFunction = function(ob) {
                        if (ob.hasProperty(key, namespace)) {
                            return +ob.getProperty(key, namespace) < +valueInputValue;
                        }
                        return false;
                    }
                }
                if (operator === '<=') {
                    searchCriterion.searchFunction = function(ob) {
                        if (ob.hasProperty(key, namespace)) {
                            return +ob.getProperty(key, namespace) <= +valueInputValue;
                        }
                        return false;
                    }
                }
                if (operator === '>') {
                    searchCriterion.searchFunction = function(ob) {
                        if (ob.hasProperty(key, namespace)) {
                            return +ob.getProperty(key, namespace) > +valueInputValue;
                        }
                        return false;
                    }
                }
                if (operator === '>=') {
                    searchCriterion.searchFunction = function(ob) {
                        if (ob.hasProperty(key, namespace)) {
                            return +ob.getProperty(key, namespace) >= +valueInputValue;
                        }
                        return false;
                    }
                }
                searchCriteria.push(searchCriterion);
            }
        }
        this.#searchResults = this.#observables.filter(function(f) {
            let flag = true;
            for (const searchCriterion of searchCriteria) {
                const result = searchCriterion.searchFunction(f);
                if (searchCriterion.logic === 'and') {
                    flag &= result;
                } else if (searchCriterion.logic === 'or') {
                    flag |= result;
                }
            }
            return flag;
        });
        this.#dropdownDiv.setButton(`Search Results: ${this.#searchResults.length}`, true);
        this.#dropdownDiv.buttonElement.getElementsByTagName('span')[0].classList.add('indent1');
        if (this.#dropdownDiv.contentDivElement.classList.contains('expanded')) {
            this.#dropdownDiv.buttonElement.click();
        }
        // - Only load seach results when button is clicked. Maybe use a web worker?
        this.#dropdownDiv.buttonElement.addEventListener('click', () => {
            if (this.#dropdownDiv.contentDivElement.classList.contains('expanded')) {
                this.#dropdownDiv.setButton('Loading search results...', true);
                this.#dropdownDiv.buttonElement.getElementsByTagName('span')[0].classList.add('indent1');
            }
            // - Use setTimeout() to make the operation non-blocking (but it still blocks)
            // - TODO: use a web worker?
            setTimeout(() => {
                if (this.#dropdownDiv.contentDivElement.classList.contains('expanded')) {
                    this.#searchResultControllers.forEach(c => c.remove());
                    this.#searchResultControllers = [];
                    this.#searchResultfeatureDropdownDivs.forEach(fd => fd.remove());
                    this.#searchResultfeatureDropdownDivs = [];
                    this.#searchResults.forEach(ob => {
                        const controller = new FeatureController(
                            this.#controller.observableGraph,
                            [ob.getProperty('treeKey', 'meta')],
                            this.#controller.isComponentManager);
                        this.#searchResultControllers.push(controller);
                        const featureDropdownDiv = new FeatureDropdownDiv(controller);
                        this.#dropdownDiv.contentDivElement.appendChild(featureDropdownDiv.getDOMElement());
                        this.#searchResultfeatureDropdownDivs.push(featureDropdownDiv);
                    });
                } else {
                    this.#searchResultControllers.forEach(c => c.remove());
                    this.#searchResultControllers = [];
                    this.#searchResultfeatureDropdownDivs.forEach(fd => fd.remove());
                    this.#searchResultfeatureDropdownDivs = [];
                }
                this.#dropdownDiv.setButton(`Search Results: ${this.#searchResults.length}`, true);
                this.#dropdownDiv.buttonElement.getElementsByTagName('span')[0].classList.add('indent1');
            }, 1);
        });
    }

    /**
     * @param {HTMLSelectElement} oldKeySelect - an old key select that should be used to set up the new key select
     * @returns {HTMLSelectElement}
     */
    #getKeySelect(oldKeySelect=null) {
        if (!(oldKeySelect instanceof HTMLSelectElement) && oldKeySelect !== null)  {
            throw TypeError('"oldKeySelect" argument must be instanceof HTMLKeySelect or null');
        }
        const keySelect = document.createElement('select');
        keySelect.dataset.role = 'keySelect';
        this.#keySelects.push(keySelect);
        const observables = this.#controller.getObservables();
        const keys = [];
        const metaKeys = [];
        observables.forEach(f => {
            Object.keys(f.getProperties('meta')).forEach(k => {
                if (!SearchModal.#nonSearchableProperties.includes(k) && !metaKeys.includes(k)) {
                    metaKeys.push(k);
                }
            });
            if (f.hasProperty('treeProps', 'meta')) {
                Object.keys(f.getProperties('treeProps')).forEach(k => {
                    if (!SearchModal.#nonSearchableProperties.includes(k) && !keys.includes(k)) {
                        keys.push(k);
                    }
                });
            }
        });
        metaKeys.sort((a, b) => a.localeCompare(b));
        keys.sort((a, b) => a.localeCompare(b));
        metaKeys.forEach(k => {
            const option = document.createElement('option');
            option.dataset.namespace = 'meta';
            if (k === 'treeKey') {
                option.text = 'ID (treeKey)';
            } else {
                option.text = k;
            }
            option.value = k;
            keySelect.add(option);
        });
        keys.forEach(k => {
            const option = document.createElement('option');
            option.dataset.namespace = 'treeProps';
            option.text = k;
            option.value = k;
            keySelect.add(option);
        });
        // - TODO: refresh key selects when data updates
        if (oldKeySelect instanceof HTMLSelectElement) {
            // - TODO: double check this is right
            const oldValue = oldKeySelect.value;
            for (const op of keySelect.options) {
                if (op.value === oldValue) {
                    op.selected = true;
                }
            }
        }
        // - Set default starting keySelect option
        for (const op of keySelect.options) {
            if (op.value === 'treeKey') {
                keySelect.selectedIndex = op.index;
            }
        }
        keySelect.classList.add('fullWidth');
        return keySelect;
    }

    /**
     * @returns {HTMLButtonElement}
     */
    #getAddRowButton() {
        const btn = document.createElement('button');
        btn.classList.add('add');
        btn.classList.add('horizontalFlex');
        btn.classList.add('centerMainAxisFlex');
        btn.classList.add('centerCrossAxisFlex');
        btn.appendChild(getCirclePlusSvg());
        const that = this;
        btn.addEventListener('click', function() {
            that.#modal.insertTBodyRow([that.#getDeleteRowButton(), that.#getAndOrSelect(), that.#getKeySelect(), that.#getOperatorSelect(), null], 'beforeEnd');
        });
        return btn;
    }

    /**
     * @returns {HTMLButtonElement}
     */
    #getDeleteRowButton() {
        const btn = document.createElement('button');
        btn.classList.add('delete');
        btn.classList.add('horizontalFlex');
        btn.classList.add('centerMainAxisFlex');
        btn.classList.add('centerCrossAxisFlex');
        btn.appendChild(getTrashCanSvg());
        const that = this;
        btn.addEventListener('click', function(e) {
            let parentElement = this.parentElement;
            while (!(parentElement instanceof HTMLTableRowElement)) {
                parentElement = parentElement.parentElement;
            }
            for (const select of parentElement.getElementsByTagName('select')) {
                if (select.dataset.role = 'keySelect') {
                    that.#keySelects = that.#keySelects.filter(s => s !== select);
                }
            }
            parentElement.remove();
            e.stopPropagation();
        });
        return btn;
    }

    /**
     * @returns {HTMLSelectElement}
     */
    #getOperatorSelect() {
        const select = document.createElement('select');
        select.dataset.role = 'operatorSelect';
        ['=', '!=', 'exists', "! exists", 'contains', "! contains", '<', '<=', '>', '>='].forEach(o => {
            const option = document.createElement('option');
            option.text = o;
            option.value = o;
            select.add(option);
        });
        select.value = 'exists';
        const that = this;
        select.addEventListener('change', function() {
            let parentElement = this.parentElement;
            while (!(parentElement instanceof HTMLTableRowElement)) {
                parentElement = parentElement.parentElement;
            }
            let valueTextInput = null;
            for (const input of parentElement.getElementsByTagName('input')) {
                if (input.dataset.role = 'valueInput') {
                    valueTextInput = input;
                }
            }
            if (['exists', '! exists'].includes(this.value)) {
                if (valueTextInput !== null) {
                    valueTextInput.remove();
                }
            } else {
                if (valueTextInput === null) {
                    parentElement.lastChild.appendChild(that.#getValueTextInput());
                }
            }
        });
        return select;
    }

    #getValueTextInput() {
        const input = document.createElement('input');
        input.dataset.role = 'valueInput';
        return input
    }

    #getAndOrSelect() {
        const select = document.createElement('select');
        select.dataset.role = 'andOrSelect';
        ['and', 'or'].forEach(o => {
            const option = document.createElement('option');
            option.text = o;
            option.value = o;
            select.add(option);
        });
        const that = this;
        return select;
    }

    #getSearchButton() {
        const btn = this.#getWideButton();
        btn.appendChild(getEyeGlassSvg());
        const span = document.createElement('span');
        span.textContent = 'Search'
        btn.appendChild(span);
        const that = this;
        btn.addEventListener('click', function() {
            that.#search();
        });
        const div = this.#getWideButtonDiv();
        div.appendChild(btn);
        return div;
    }

    // - This is a temporary hack until I figure out how to refresh everything propertly
    #getRefreshButton() {
        const btn = this.#getWideButton();
        const span = document.createElement('span');
        span.textContent = 'Refresh';
        btn.appendChild(span);
        const that = this;
        btn.addEventListener('click', function() {
            that.renderContent();
        });
        const div = this.#getWideButtonDiv();
        div.appendChild(btn);
        return div;
    }

    #getWideButton() {
        const btn = document.createElement('button');
        btn.classList.add('horizontalFlex');
        btn.classList.add('centerMainAxisFlex');
        btn.classList.add('centerCrossAxisFlex');
        btn.classList.add('fullWidth');
        return btn;
    }

    #getWideButtonDiv() {
        const div = document.createElement('div');
        div.classList.add('horizontalFlex');
        div.classList.add('centerMainAxisFlex');
        div.classList.add('centerCrossAxisFlex');
        div.classList.add('halfWidth');
        return div;
    }
}

function getEyeGlassSvg() {
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('width', '28px');
    svg.setAttribute('height', '28px');
    svg.setAttribute('viewBox', '0 0 24 24'); 
    svg.setAttribute('fill', 'none'); 
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', "M4 11C4 7.13401 7.13401 4 11 4C14.866 4 18 7.13401 18 11C18 14.866 14.866 18 11 18C7.13401 18 4 14.866 4 11ZM11 2C6.02944 2 2 6.02944 2 11C2 15.9706 6.02944 20 11 20C13.125 20 15.078 19.2635 16.6177 18.0319L20.2929 21.7071C20.6834 22.0976 21.3166 22.0976 21.7071 21.7071C22.0976 21.3166 22.0976 20.6834 21.7071 20.2929L18.0319 16.6177C19.2635 15.078 20 13.125 20 11C20 6.02944 15.9706 2 11 2Z");
    path.setAttribute('fill-rule', 'evenodd');
    path.setAttribute('clip-rule', 'evenodd');
    path.setAttribute('fill', '#FFFFFF');
    path.setAttribute('stroke-width', '1.5');
    path.setAttribute('stroke-width', '1.5');
    path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('stroke-linejoin', 'round');
    svg.appendChild(path);
    return svg
}