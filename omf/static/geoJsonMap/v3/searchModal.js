export { SearchModal };
import { DropdownDiv } from './dropdownDiv.js';
import { Feature } from './feature.js';
import { FeatureController } from './featureController.js';
import { FeatureDropdownDiv } from './featureDropdownDiv.js';
import { FeatureGraph } from './featureGraph.js';
import { getCirclePlusSvg, getTrashCanSvg } from './featureEditModal.js';
import { Modal } from './modal.js';

class SearchModal {
    #configDropdownDiv;         // - A DropdownDiv instance
    #controller;                // - ControllerInterface instance for this SearchModal
    #keySelects;                // - An array of HTMLSelectElement instances
    #lineDropdownDiv;           // - A DropdownDiv instance
    #modal;                     // - A single Modal instance for this SearchModal
    #nodeDropdownDiv;           // - A DropdownDiv instance
    #observables;               // - An array of ObservableInterface instances (i.e. components) or an array containing a FeatureGraph
    #removed;                   // - Whether this SearchModal instance has already been deleted
    #searchResults;             // - An array of all of the ObservableInterface instances that matched the search. This is necessary to build additional functionality (e.g. coloring, etc.)
    static #nonSearchableProperties = ['treeProps', 'formProps', 'urlProps', 'componentType'];

    /**
     * @param {FeatureController} controller - a ControllerInterface instance
     * @param {Array} [observables=null] - an array of ObservableInterface instances (i.e. components)
     * @returns {undefined}
     */
    constructor(controller, observables=null) {
        if (!(controller instanceof FeatureController)) {
            throw TypeError('"controller" argument must be instanceof FeatureController.');
        }
        if (!(observables instanceof Array) && observables !== null) {
            throw TypeError('"observables" argument must be an array or null.');
        }
        this.#configDropdownDiv = new DropdownDiv();
        this.#configDropdownDiv.addStyleClasses(['sideNav', 'searchCategory'], 'divElement');
        this.#controller = controller;
        this.#keySelects = [];
        this.#lineDropdownDiv = new DropdownDiv();
        this.#lineDropdownDiv.addStyleClasses(['sideNav', 'searchCategory'], 'divElement');
        this.#modal = null;
        this.#nodeDropdownDiv = new DropdownDiv();
        this.#nodeDropdownDiv.addStyleClasses(['sideNav', 'searchCategory'], 'divElement');
        if (observables === null) {
            this.#observables = [controller.observableGraph];
            this.#observables[0].registerObserver(this);
        } else {
            this.#observables = observables;
            this.#observables.forEach(ob => ob.registerObserver(this));
        }
        this.#removed = false;
        this.#searchResults = [];
        this.renderContent();
        this.#search();
        this.#attachDropdownDivEventHandlers();
    }

    // *******************************
    // ** ObserverInterface methods **
    // *******************************

    /**
     * - Remove this ObserverInterface instance (i.e. "this") from the ObservableInterface instance (i.e. "observable") that has been deleted, and
     *   perform other actions as needed
     * @param {Feature} observable - an ObservableInterface instance. While this SearchModal is an observer of the FeatureGraph, the FeatureGraph
     *      calls this function with a Feature argument
     * @returns {undefined}
     */
    handleDeletedObservable(observable) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!(observable instanceof Feature)) {
            throw TypeError('"observable" argument must be instanceof Feature.');
        }
        this.#searchResults = this.#searchResults.filter(ob => ob !== observable);
        this.refreshContent();
        const {configs, nodes, lines} = this.#getCategorizedSearchResults();
        [
            [this.#configDropdownDiv, configs, 'Configuration objects'],
            [this.#nodeDropdownDiv, nodes, 'Nodes'],
            [this.#lineDropdownDiv, lines, 'Lines']
        ].forEach(ary => {
            ary[0].setButton(`${ary[2]}: ${ary[1].length}`, true);
        });
    }

    /**
     * @param {Feature} observable - an ObservableInterface instance. While this SearchModal is an observer of the FeatureGraph, the FeatureGraph
     *      calls this function with a Feature argument
     * @returns {undefined}
     */
    handleNewObservable(observable) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!(observable instanceof Feature)) {
            throw TypeError('"observable" argument must be instanceof FeatureGraph.');
        }
        this.refreshContent();
    }

    /**
     * - Update this ObserverInterface instance (i.e. "this") based on the coordinates of the ObservableInterface instance (i.e. "observable") that
     *   have just changed and perform other actions as needed
     * @param {Feature} observable - an ObservableInterface instance
     * @param {Array} oldCoordinates - the old coordinates of the observable prior to the change in coordinates
     * @returns {undefined}
     */
    handleUpdatedCoordinates(observable, oldCoordinates) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!(observable instanceof Feature) && !(observable instanceof FeatureGraph)) {
            throw TypeError('"observable" argument must be instanceof Feature or FeatureGraph.');
        }
        if (!(oldCoordinates instanceof Array)) {
            throw TypeError('"oldCoordinates" argument must be an array.');
        }
        this.refreshContent();
    }

    /**
     * - Update this ObserverInstance (i.e. "this") based on the property of the ObservableInterface instance (i.e. "observable") that has just
     *   changed and perform other actions as needed
     * @param {Feature} observable - an ObservableInterface instance
     * @param {string} propertyKey - the property key of the property that has been created/changed/deleted in the observable
     * @param {(string|Object)} oldPropertyValue - the previous value of the property that has been created/changed/deleted in the observable
     * @param {string} namespace - the namespace of the property that has been created/changed/deleted in the observable
     * @returns {undefined}
     */
    handleUpdatedProperty(observable, propertyKey, oldPropertyValue, namespace='treeProps') {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        // - A SearchModal can either directly observer Features or a FeatureGraph. Since in both cases the SearchModal response is the same, this is
        //   a special case where the observable can be one of two classes
        if (!(observable instanceof Feature) && !(observable instanceof FeatureGraph)) {
            throw TypeError('"observable" argument must be instanceof Feature or FeatureGraph.');
        }
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be a string.');
        }
        if (typeof namespace !== 'string') {
            throw TypeError('"namespace" argument must be a string.');
        }
        this.refreshContent();
    }

    // ****************************
    // ** ModalInterface methods **
    // ****************************

    /**
     * @returns {HTMLDivElement}
     */
    getDOMElement() {
        return this.#modal.divElement;
    }

    /**
     * @returns {boolean}
     */
    isRemoved() {
        return this.#removed;
    }

    /**
     * @returns {undefined}
     */
    refreshContent() {
        const keySelects = [...this.#keySelects];
        keySelects.forEach(oldKeySelect => {
            const index = this.#keySelects.indexOf(oldKeySelect);
            if (index > -1) {
                this.#keySelects.splice(index, 1);
            }
            const newKeySelect = this.#getKeySelect(oldKeySelect);
            oldKeySelect.replaceWith(newKeySelect);
        });
    }

    /**
     * @returns {undefined}
     */
    remove() {
        if (!this.#removed) {
            this.#configDropdownDiv.divElement.remove();
            this.#configDropdownDiv = null;
            this.#controller = null;
            this.#keySelects = null;
            this.#lineDropdownDiv.divElement.remove();
            this.#lineDropdownDiv = null;
            this.#modal.divElement.remove(); 
            this.#modal = null;
            this.#nodeDropdownDiv.divElement.remove();
            this.#nodeDropdownDiv = null;
            this.#observables.forEach(ob => ob.removeObserver(this));
            this.#observables = null;
            this.#removed = true;
        }
    }
 
    /**
     * @returns {undefined}
     */
    renderContent() {
        const modal = new Modal();
        modal.addStyleClasses(['outerModal', 'searchModal'], 'divElement');
        modal.insertTBodyRow([null, null, this.#getKeySelect(), this.#getOperatorSelect(), null], 'beforeEnd');
        modal.insertTBodyRow([this.#getAddRowButton()], 'append', ['absolute']);
        modal.addStyleClasses(['centeredTable'], 'tableElement');
        modal.insertElement(this.#getSearchButton());
        modal.addStyleClasses(['verticalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex'], 'containerElement');
        if (this.#modal === null) {
            this.#modal = modal;
        } 
        if (document.body.contains(this.#modal.divElement)) {
            this.#modal.divElement.replaceWith(modal.divElement);
            this.#modal = modal;
        }
    }

    // ********************
    // ** Public methods **
    // ********************

    /**
     * @returns {HTMLDivElement}
     */
    getConfigSearchResultsDiv() {
        return this.#configDropdownDiv.divElement;
    }

    /**
     * @returns {HTMLDivElement}
     */
    getLineSearchResultsDiv() {
        return this.#lineDropdownDiv.divElement;
    }

    /**
     * @returns {HTMLDivElement}
     */
    getNodeSearchResultsDiv() {
        return this.#nodeDropdownDiv.divElement;
    }
    
    // *********************
    // ** Private methods ** 
    // *********************

    /**
     * @param {DropdownDiv} dropdownDiv
     * @param {Array} observables
     * @returns {undefined}
     */
    #appendFeatureDropdownDivs(dropdownDiv, observables) {
        if (!(dropdownDiv instanceof DropdownDiv)) {
            throw TypeError('"dropdown" argument must be instanceof DropdownDiv');
        }
        if (!(observables instanceof Array)) {
            throw TypeError('"observables" argument must be an Array');
        }
        observables.forEach(ob => {
            const featureDropdownDiv = new FeatureDropdownDiv(ob, this.#controller);
            dropdownDiv.contentDivElement.appendChild(featureDropdownDiv.getDOMElement())
        });
    }

    /**
     * - The event handler must itself call this.#getCategorizedSearchResults() in order to get the current set of search results
     * @returns {undefined}
     */
    #attachDropdownDivEventHandlers() {
        [[this.#configDropdownDiv, 'Configuration objects'], [this.#nodeDropdownDiv, 'Nodes'], [this.#lineDropdownDiv, 'Lines']].forEach(ary => {
            ary[0].buttonElement.addEventListener('click', () => {
                if (ary[0].isExpanded() && ary[0].contentDivElement.children.length === 0) {
                    ary[0].setButton('Loading search results...', true);
                    setTimeout(() => {
                        const {configs, nodes, lines} = this.#getCategorizedSearchResults();
                        if (ary[1] === 'Configuration objects') {
                            this.#appendFeatureDropdownDivs(ary[0], configs);
                            ary[0].setButton(`${ary[1]}: ${configs.length}`, true);
                        } else if (ary[1] === 'Nodes') {
                            this.#appendFeatureDropdownDivs(ary[0], nodes);
                            ary[0].setButton(`${ary[1]}: ${nodes.length}`, true);
                        } else if (ary[1] === 'Lines') {
                            this.#appendFeatureDropdownDivs(ary[0], lines);
                            ary[0].setButton(`${ary[1]}: ${lines.length}`, true);
                        }
                    }, 1);
                }
            });
        });
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
     * @returns {HTMLSelectElement}
     */
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

    /**
     * @returns {Object}
     */
    #getCategorizedSearchResults() {
        const configs = [];
        const nodes = [];
        const lines = [];
        this.#searchResults.forEach(ob => {
            if (ob.isConfigurationObject()) {
                configs.push(ob);
            } else if (ob.isNode()) {
                nodes.push(ob);
            } else if (ob.isLine()) {
                lines.push(ob);
            } else {
                throw TypeError('"The observable was not a configuration object, node, or line.');
            }
        });
        return {
            'configs': configs,
            'nodes': nodes,
            'lines': lines
        }
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
     * @param {HTMLSelectElement} oldKeySelect - an old key select that should be used to set up the new key select
     * @returns {HTMLSelectElement}
     */
    #getKeySelect(oldKeySelect=null) {
        if (!(oldKeySelect instanceof HTMLSelectElement) && oldKeySelect !== null)  {
            throw TypeError('"oldKeySelect" argument must be instanceof HTMLKeySelect or null.');
        }
        const keySelect = document.createElement('select');
        keySelect.dataset.role = 'keySelect';
        this.#keySelects.push(keySelect);
        const keys = [];
        const metaKeys = [];
        let observables;
        if (this.#observables[0] instanceof FeatureGraph) {
            observables = this.#observables[0].getObservables();
        } else {
            observables = this.#observables;
        }
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
        for (const op of keySelect.options) {
            if (op.value === 'treeKey') {
                keySelect.selectedIndex = op.index;
            }
        }
        if (oldKeySelect instanceof HTMLSelectElement) {
            const oldValue = oldKeySelect.value;
            for (const op of keySelect.options) {
                if (op.value === oldValue) {
                    keySelect.selectedIndex = op.index;
                }
            }
        }
        keySelect.classList.add('fullWidth');
        return keySelect;
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

    /**
     * @returns {HTMLButtonElement}
     */
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

    /**
     * - x
     * @param {Array} searchCriteria - an array of search criteria
     * @returns {Function}
     */
    #getSearchFunction(searchCriteria) {
        if (!(searchCriteria instanceof Array)) {
            throw TypeError('"searchCriteria" argumet must be an array.');
        }
        const func = function(ob) {
            if (ob.getProperty('treeKey', 'meta') === 'omd') {
                return false;
            }
            let flag = true;
            for (const searchCriterion of searchCriteria) {
                const result = searchCriterion.searchFunction(ob);
                if (searchCriterion.logic === 'and') {
                    flag &= result;
                } else if (searchCriterion.logic === 'or') {
                    flag |= result;
                }
            }
            return flag;
        };
        //return func;
        return func.bind(this);
    }

    #getValueTextInput() {
        const input = document.createElement('input');
        input.dataset.role = 'valueInput';
        return input
    }

    /**
     * @returns {HTMLButtonElement}
     */
    #getWideButton() {
        const btn = document.createElement('button');
        btn.classList.add('horizontalFlex');
        btn.classList.add('centerMainAxisFlex');
        btn.classList.add('centerCrossAxisFlex');
        btn.classList.add('fullWidth');
        return btn;
    }

    /**
     * @returns {HTMLDivElement}
     */
    #getWideButtonDiv() {
        const div = document.createElement('div');
        div.classList.add('horizontalFlex');
        div.classList.add('centerMainAxisFlex');
        div.classList.add('centerCrossAxisFlex');
        div.classList.add('halfWidth');
        return div;
    }

    /**
     * - x
     * @returns {undefined}
     */
    #search() {
        // - Clear the old FeatureDropdownDivs
        this.#searchResults.forEach(observable => {
            // - One time I saw a bug where an observable had multiple FeatureDropdownDiv observers, so just remove all of them
            observable.getObservers().filter(observer => observer instanceof FeatureDropdownDiv).forEach(fdd => fdd.remove());
        });
        // - Clear the old search results
        this.#searchResults = [];
        // - Clear the old search criteria and build new search criteria
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
                                return value === valueInputValue;
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
                                return value !== valueInputValue;
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
        // - Run the search for normal features
        if (this.#observables[0] instanceof FeatureGraph) {
            this.#searchResults = this.#observables[0].getObservables(this.#getSearchFunction(searchCriteria));
        // - Run the search for components
        } else {
            this.#searchResults = this.#observables.filter(this.#getSearchFunction(searchCriteria));
        }
        // - Don't attach event handlers here because then I'll be adding a new event handler after every search!
        const {configs, nodes, lines} = this.#getCategorizedSearchResults();
        [
            [this.#configDropdownDiv, configs, 'Configuration objects'],
            [this.#nodeDropdownDiv, nodes, 'Nodes'],
            [this.#lineDropdownDiv, lines, 'Lines']
        ].forEach(ary => {
            ary[0].setButton(`${ary[2]}: ${ary[1].length}`, true);
            if (ary[0].isExpanded() && ary[0].contentDivElement.children.length === 0) {
                this.#appendFeatureDropdownDivs(ary[0], ary[1]);
            }
        });
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