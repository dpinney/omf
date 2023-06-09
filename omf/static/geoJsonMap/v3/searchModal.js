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
        modal.addStyleClasses(['searchModal'], 'divElement');
        const keySelect = this.#getKeySelect();
        modal.insertTBodyRow([this.#getAddRowButton(), null, keySelect, this.#getOperatorSelect(), this.#getValueTextInput()], 'beforeEnd');
        this.#handleKeySelectChange(keySelect);
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
            const keySelect = that.#getKeySelect();
            that.#modal.insertTBodyRow([that.#getDeleteRowButton(), that.#getAndOrSelect(), keySelect, that.#getOperatorSelect(), that.#getValueTextInput()], 'append');
            that.#handleKeySelectChange(keySelect);
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
                if (!['attachments', 'componentType', 'formProps', 'hiddenLinks', 'hiddenNodes', 'layoutVars', 'links', 'name2', 'nodes', 'owner', 'syntax',
                    'treeProps', 'urlProps'].includes(k) && !metaKeys.includes(k)) {
                    metaKeys.push(k);
                }
            });
            if (f.hasProperty('treeProps', 'meta')) {
                Object.keys(f.getProperties('treeProps')).forEach(k => {
                    if (![].includes(k) && !keys.includes(k)) {
                        keys.push(k);
                    }
                });
            }
        });
        // - Add fake key to search all fields
        const option = document.createElement('option');
        option.dataset.namespace = 'treeProps';
        option.text = '<All Fields>';
        option.value = 'searchModalSearchAllFields';
        keySelect.add(option);
        keySelect.addEventListener('change', this.#handleKeySelectChange.bind(this, keySelect));
        // - Add regular keys
        metaKeys.sort((a, b) => a.localeCompare(b));
        keys.sort((a, b) => a.localeCompare(b));
        metaKeys.forEach(k => {
            const option = document.createElement('option');
            option.dataset.namespace = 'meta';
            if (k === 'treeKey') {
                option.text = 'ID';
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
            if (op.value === 'searchModalSearchAllFields') {
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
            const valueTextInput = parentElement.querySelector('input[data-role="valueInput"]');
            if (['exists', '! exists'].includes(this.value)) {
                if (valueTextInput !== null) {
                    valueTextInput.remove();
                }
            } else {
                if (valueTextInput === null) {
                    parentElement.lastChild.lastChild.appendChild(that.#getValueTextInput());
                }
            }
        });
        for (const op of select.options) {
            if (op.value === 'contains') {
                select.selectedIndex = op.index;
            }
        }
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
        return func.bind(this);
    }

    /**
     * @returns {HTMLButtonElement}
     */
    #getSettingsButton() {
        const btn = document.createElement('button');
        btn.classList.add('horizontalFlex');
        btn.classList.add('centerMainAxisFlex');
        btn.classList.add('centerCrossAxisFlex');
        btn.appendChild(getGearSvg());
        const that = this;
        btn.addEventListener('click', function() {
            // - TODO: use a settings modal
        });
        return btn;
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
     * - This has to be a function because it's used as an event handler and it's called separately on page load to supply a correct operator select
     * @param {HTMLSelectElement} select
     * @returns {undefined}
     */
    #handleKeySelectChange(select) {
        if (!(select instanceof HTMLSelectElement)) {
            throw TypeError('"select" argument must be instanceof HTMLSelectElement');
        }
        let parentElement = select.parentElement;
        while (!(parentElement instanceof HTMLTableRowElement)) {
            parentElement = parentElement.parentElement;
        }
        const valueTextInput = parentElement.querySelector('input[data-role="valueInput"]');
        const operatorSelect = parentElement.querySelector('select[data-role="operatorSelect"]');
        // - This corresponds to the "<All Fields>" option being selected
        if (select.selectedIndex === 0) {
            if (valueTextInput === null) {
                parentElement.lastChild.lastChild.appendChild(this.#getValueTextInput());
            }
            const newOperatorSelect = document.createElement('select');
            newOperatorSelect.dataset.role = 'operatorSelect';
            ['contains', '! contains'].forEach(o => {
                const option = document.createElement('option');
                option.text = o;
                option.value = o;
                newOperatorSelect.add(option);
            });
            newOperatorSelect.value = 'contains';
            operatorSelect.replaceWith(newOperatorSelect);
        } else {
            const oldValue = operatorSelect.value;
            const newOperatorSelect = this.#getOperatorSelect();
            newOperatorSelect.value = oldValue;
            operatorSelect.replaceWith(newOperatorSelect);
        }
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
                                //return value === valueInputValue;
                                return value.toString().toLowerCase() === valueInputValue.toLowerCase();
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
                                //return value !== valueInputValue;
                                return value.toString().toLowerCase() !== valueInputValue.toLowerCase();
                            }
                        }
                        return false;
                    };
                }
                if (operator === 'contains') {
                    searchCriterion.searchFunction = function(ob) {
                        if (key === 'searchModalSearchAllFields') {
                            for (const [key, val] of Object.entries(ob.getProperties(namespace))) {
                                if (val.toString().toLowerCase().includes(valueInputValue.toLowerCase()) || key.toString().toLowerCase().includes(valueInputValue.toLowerCase())) {
                                    return true;
                                }
                            }
                        } else if (ob.hasProperty(key, namespace)) {
                            return ob.getProperty(key, namespace).toString().toLowerCase().includes(valueInputValue.toLowerCase());
                        }
                        return false;
                    }
                }
                if (operator === '! contains') {
                    searchCriterion.searchFunction = function(ob) {
                        if (key === 'searchModalSearchAllFields') {
                            for (const [key, val] of Object.entries(ob.getProperties(namespace))) {
                                if (val.toString().toLowerCase().includes(valueInputValue.toLowerCase()) || key.toString().toLowerCase().includes(valueInputValue.toLowerCase())) {
                                    return false;
                                }
                            }
                            return true;
                        } else if (ob.hasProperty(key, namespace)) {
                            return !ob.getProperty(key, namespace).toString().toLowerCase().includes(valueInputValue.toLowerCase());
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

/**
 * - https://www.svgrepo.com
 */
function getEyeGlassSvg() {
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('width', '22px');
    svg.setAttribute('height', '22px');
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

/**
 * - https://www.svgrepo.com
 */
function getGearSvg() {
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('width', '22px');
    svg.setAttribute('height', '22px');
    svg.setAttribute('viewBox', '0 0 32 32');
    svg.setAttribute('fill', 'none');
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M29 11.756h-1.526c-0.109-0.295-0.229-0.584-0.361-0.87l1.087-1.076c0.441-0.389 0.717-0.956 0.717-1.587 0-0.545-0.206-1.042-0.545-1.417l0.002 0.002-3.178-3.178c-0.373-0.338-0.87-0.544-1.415-0.544-0.632 0-1.199 0.278-1.587 0.718l-0.002 0.002-1.081 1.080c-0.285-0.131-0.573-0.251-0.868-0.36l0.008-1.526c0.003-0.042 0.005-0.091 0.005-0.141 0-1.128-0.884-2.049-1.997-2.109l-0.005-0h-4.496c-1.119 0.059-2.004 0.981-2.004 2.11 0 0.049 0.002 0.098 0.005 0.147l-0-0.007v1.524c-0.295 0.109-0.584 0.229-0.87 0.361l-1.074-1.084c-0.389-0.443-0.957-0.722-1.589-0.722-0.545 0-1.042 0.206-1.416 0.545l0.002-0.002-3.179 3.179c-0.338 0.373-0.544 0.87-0.544 1.415 0 0.633 0.278 1.2 0.719 1.587l0.002 0.002 1.078 1.079c-0.132 0.287-0.252 0.576-0.362 0.872l-1.525-0.007c-0.042-0.003-0.091-0.005-0.14-0.005-1.128 0-2.050 0.885-2.11 1.998l-0 0.005v4.495c0.059 1.119 0.982 2.005 2.111 2.005 0.049 0 0.098-0.002 0.146-0.005l-0.007 0h1.525c0.109 0.295 0.229 0.584 0.361 0.87l-1.084 1.071c-0.443 0.39-0.721 0.958-0.721 1.592 0 0.545 0.206 1.043 0.545 1.418l-0.002-0.002 3.179 3.178c0.339 0.337 0.806 0.545 1.322 0.545 0.007 0 0.014-0 0.021-0h-0.001c0.653-0.013 1.24-0.287 1.662-0.722l0.001-0.001 1.079-1.079c0.287 0.132 0.577 0.252 0.873 0.362l-0.007 1.524c-0.003 0.042-0.005 0.091-0.005 0.14 0 1.128 0.885 2.050 1.998 2.11l0.005 0h4.496c1.118-0.060 2.003-0.981 2.003-2.109 0-0.050-0.002-0.099-0.005-0.147l0 0.007v-1.526c0.296-0.11 0.585-0.23 0.872-0.362l1.069 1.079c0.423 0.435 1.009 0.709 1.66 0.723l0.002 0h0.002c0.006 0 0.014 0 0.021 0 0.515 0 0.982-0.207 1.323-0.541l3.177-3.177c0.335-0.339 0.541-0.805 0.541-1.32 0-0.009-0-0.018-0-0.028l0 0.001c-0.013-0.651-0.285-1.236-0.718-1.658l-0.001-0-1.080-1.081c0.131-0.285 0.251-0.573 0.36-0.868l1.525 0.007c0.042 0.003 0.090 0.005 0.139 0.005 1.129 0 2.051-0.885 2.11-1.999l0-0.005v-4.495c-0.060-1.119-0.981-2.004-2.11-2.004-0.049 0-0.098 0.002-0.147 0.005l0.007-0zM28.75 17.749l-2.162-0.011c-0.026 0-0.048 0.013-0.074 0.015-0.093 0.009-0.179 0.026-0.261 0.053l0.008-0.002c-0.31 0.068-0.565 0.263-0.711 0.527l-0.003 0.005c-0.048 0.071-0.091 0.152-0.124 0.238l-0.003 0.008c-0.008 0.024-0.027 0.041-0.034 0.066-0.23 0.804-0.527 1.503-0.898 2.155l0.025-0.048c-0.014 0.025-0.013 0.054-0.026 0.080-0.029 0.063-0.053 0.138-0.071 0.215l-0.001 0.008c-0.023 0.072-0.040 0.156-0.048 0.242l-0 0.005c-0.002 0.027-0.004 0.058-0.004 0.089 0 0.209 0.061 0.404 0.166 0.568l-0.003-0.004c0.045 0.088 0.096 0.163 0.154 0.232l-0.001-0.002c0.017 0.019 0.022 0.043 0.040 0.061l1.529 1.531-2.469 2.467-1.516-1.529c-0.020-0.021-0.048-0.027-0.069-0.046-0.060-0.050-0.128-0.096-0.2-0.135l-0.006-0.003c-0.195-0.109-0.429-0.173-0.677-0.173-0.002 0-0.004 0-0.006 0h0c-0.076 0.008-0.145 0.022-0.211 0.040l0.009-0.002c-0.102 0.020-0.192 0.050-0.276 0.089l0.007-0.003c-0.022 0.011-0.047 0.010-0.069 0.022-0.606 0.346-1.307 0.644-2.043 0.859l-0.070 0.017c-0.027 0.008-0.045 0.027-0.071 0.037-0.084 0.033-0.157 0.071-0.224 0.116l0.004-0.003c-0.075 0.041-0.139 0.085-0.199 0.135l0.002-0.002c-0.053 0.052-0.102 0.11-0.145 0.171l-0.003 0.004c-0.103 0.113-0.176 0.254-0.206 0.411l-0.001 0.005c-0.024 0.074-0.043 0.16-0.051 0.249l-0 0.005c-0.002 0.026-0.015 0.048-0.015 0.075l-0.001 2.162h-3.491l0.011-2.156c0-0.028-0.014-0.052-0.016-0.079-0.008-0.092-0.026-0.177-0.052-0.258l0.002 0.008c-0.068-0.313-0.265-0.57-0.531-0.717l-0.006-0.003c-0.070-0.047-0.15-0.089-0.235-0.122l-0.008-0.003c-0.024-0.008-0.042-0.027-0.067-0.034-0.806-0.23-1.507-0.528-2.161-0.9l0.048 0.025c-0.023-0.013-0.050-0.012-0.073-0.023-0.072-0.033-0.156-0.061-0.244-0.079l-0.008-0.001c-0.092-0.029-0.198-0.045-0.308-0.045-0.221 0-0.426 0.066-0.597 0.18l0.004-0.002c-0.076 0.040-0.141 0.084-0.201 0.134l0.002-0.002c-0.021 0.019-0.048 0.025-0.068 0.045l-1.529 1.529-2.47-2.469 1.532-1.516c0.020-0.020 0.027-0.047 0.045-0.067 0.053-0.063 0.101-0.134 0.142-0.209l0.003-0.006c0.037-0.058 0.071-0.124 0.099-0.194l0.003-0.008c0.038-0.14 0.062-0.301 0.066-0.467l0-0.003c-0.008-0.083-0.023-0.158-0.044-0.231l0.002 0.009c-0.020-0.094-0.047-0.177-0.083-0.255l0.003 0.007c-0.012-0.025-0.011-0.052-0.025-0.076-0.347-0.605-0.645-1.305-0.858-2.041l-0.017-0.068c-0.007-0.026-0.027-0.045-0.036-0.070-0.034-0.086-0.072-0.16-0.118-0.228l0.003 0.005c-0.040-0.074-0.084-0.138-0.133-0.197l0.002 0.002c-0.052-0.053-0.109-0.101-0.169-0.144l-0.004-0.003c-0.060-0.051-0.128-0.097-0.2-0.136l-0.006-0.003c-0.057-0.026-0.126-0.049-0.196-0.066l-0.008-0.002c-0.077-0.026-0.167-0.045-0.259-0.053l-0.005-0c-0.026-0.002-0.047-0.015-0.073-0.015l-2.162-0.001v-3.492l2.162 0.011c0.16-0.002 0.311-0.035 0.45-0.092l-0.008 0.003c0.054-0.024 0.099-0.048 0.142-0.075l-0.005 0.003c0.090-0.047 0.168-0.1 0.239-0.16l-0.002 0.001c0.043-0.039 0.082-0.079 0.118-0.122l0.002-0.002c0.056-0.065 0.106-0.138 0.147-0.215l0.003-0.007c0.027-0.047 0.054-0.102 0.076-0.159l0.003-0.008c0.010-0.028 0.029-0.050 0.037-0.078 0.23-0.805 0.527-1.506 0.899-2.159l-0.025 0.048c0.014-0.024 0.013-0.052 0.025-0.076 0.031-0.067 0.057-0.147 0.075-0.229l0.001-0.008c0.020-0.086 0.032-0.185 0.032-0.287 0-0.317-0.113-0.607-0.3-0.834l0.002 0.002c-0.017-0.020-0.023-0.045-0.042-0.063l-1.527-1.529 2.469-2.469 1.518 1.531c0.055 0.045 0.116 0.087 0.18 0.122l0.006 0.003c0.042 0.033 0.089 0.065 0.138 0.094l0.006 0.003c0.16 0.088 0.35 0.142 0.551 0.148l0.002 0 0.005 0.001c0.012 0 0.023-0.009 0.034-0.009 0.186-0.008 0.359-0.056 0.513-0.135l-0.007 0.003c0.022-0.011 0.047-0.006 0.070-0.018 0.605-0.346 1.305-0.645 2.041-0.858l0.069-0.017c0.025-0.007 0.042-0.026 0.066-0.034 0.091-0.035 0.17-0.076 0.243-0.125l-0.004 0.003c0.069-0.038 0.128-0.079 0.183-0.124l-0.002 0.002c0.058-0.056 0.11-0.117 0.156-0.183l0.003-0.004c0.046-0.056 0.089-0.119 0.126-0.185l0.003-0.006c0.028-0.062 0.053-0.135 0.070-0.21l0.002-0.008c0.024-0.073 0.042-0.158 0.050-0.247l0-0.005c0.002-0.027 0.015-0.049 0.015-0.076l0.001-2.162h3.491l-0.011 2.156c-0 0.028 0.014 0.051 0.015 0.079 0.008 0.093 0.026 0.178 0.052 0.26l-0.002-0.008c0.019 0.084 0.044 0.157 0.075 0.227l-0.003-0.008c0.040 0.073 0.082 0.136 0.13 0.194l-0.002-0.002c0.048 0.070 0.101 0.131 0.158 0.187l0 0c0.053 0.044 0.112 0.084 0.174 0.12l0.006 0.003c0.068 0.046 0.147 0.087 0.23 0.119l0.008 0.003c0.025 0.009 0.043 0.028 0.069 0.035 0.804 0.229 1.503 0.527 2.155 0.899l-0.047-0.025c0.022 0.012 0.046 0.007 0.068 0.018 0.147 0.076 0.32 0.124 0.503 0.132l0.003 0c0.012 0 0.024 0.009 0.036 0.009l0.028-0.008c0.193-0.008 0.372-0.059 0.531-0.143l-0.007 0.003c0.059-0.033 0.109-0.066 0.156-0.104l-0.003 0.002c0.068-0.037 0.127-0.076 0.181-0.12l-0.002 0.002 1.531-1.528 2.469 2.47-1.531 1.516c-0.020 0.020-0.027 0.047-0.046 0.068-0.053 0.063-0.101 0.134-0.142 0.209l-0.003 0.006c-0.084 0.123-0.138 0.272-0.148 0.434l-0 0.002c-0.013 0.056-0.020 0.121-0.020 0.187 0 0.097 0.016 0.19 0.045 0.277l-0.002-0.006c0.020 0.094 0.047 0.176 0.083 0.254l-0.003-0.007c0.012 0.025 0.011 0.053 0.025 0.078 0.347 0.604 0.645 1.303 0.858 2.038l0.017 0.068c0.008 0.030 0.028 0.052 0.038 0.080 0.024 0.062 0.049 0.113 0.077 0.163l-0.003-0.006c0.211 0.397 0.619 0.665 1.090 0.674l0.001 0 2.162 0.001zM16 10.75c-2.899 0-5.25 2.351-5.25 5.25s2.351 5.25 5.25 5.25c2.899 0 5.25-2.351 5.25-5.25v0c-0.004-2.898-2.352-5.246-5.25-5.25h-0zM16 18.75c-1.519 0-2.75-1.231-2.75-2.75s1.231-2.75 2.75-2.75c1.519 0 2.75 1.231 2.75 2.75v0c-0.002 1.518-1.232 2.748-2.75 2.75h-0z');
    path.setAttribute('fill', '#FFFFFF');
    path.setAttribute('stroke-width', '1.5');
    path.setAttribute('stroke-width', '1.5');
    path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('stroke-linejoin', 'round');
    svg.appendChild(path);
    return svg;
}