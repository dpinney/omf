export { SearchModal };
import { DropdownDiv } from '../v4/ui-components/dropdown-div/dropdown-div.js';
import { Feature } from './feature.js';
import { FeatureController } from './featureController.js';
import { FeatureDropdownDiv } from './featureDropdownDiv.js';
import { FeatureGraph } from './featureGraph.js';
import { PropTable } from '../v4/ui-components/prop-table/prop-table.js';
import { IconLabelButton } from '../v4/ui-components/iconlabel-button/iconlabel-button.js';
import { LeafletLayer } from './leafletLayer.js';

class SearchModal {

    #configDropdownDiv; // - A DropdownDiv instance
    #controller;        // - ControllerInterface instance for this SearchModal
    #keySelects;        // - An array of HTMLSelectElement instances
    #lineDropdownDiv;   // - A DropdownDiv instance
    #propTable;         // - A PropTable instance
    #nodeDropdownDiv;   // - A DropdownDiv instance
    #observables;       // - An array of ObservableInterface instances (i.e. components) or an array containing a FeatureGraph
    #removed;           // - Whether this SearchModal instance has already been deleted
    #searchResults;     // - An array of all of the ObservableInterface instances that matched the search. This is necessary to build additional functionality (e.g. coloring, etc.)
    static searchModal = null;
    static componentModal = null;

    /**
     * @param {FeatureController} controller - a ControllerInterface instance
     * @param {Array} [observables=null] - an array of ObservableInterface instances (i.e. components)
     * @returns {undefined}
     */
    constructor(controller, observables=null) {
        if (!(controller instanceof FeatureController)) {
            throw TypeError('The "controller" argument must be instanceof FeatureController.');
        }
        if (!(observables instanceof Array) && observables !== null) {
            throw TypeError('The "observables" argument must be an array or null.');
        }
        this.#controller = controller;
        this.#keySelects = [];
        this.#propTable = null;
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
        this.#configDropdownDiv = new DropdownDiv();
        this.#setupDropdownDiv(this.#configDropdownDiv, 'Configuration objects');
        this.#nodeDropdownDiv = new DropdownDiv();
        this.#setupDropdownDiv(this.#nodeDropdownDiv, 'Nodes');
        this.#lineDropdownDiv = new DropdownDiv();
        this.#setupDropdownDiv(this.#lineDropdownDiv, 'Lines');
        this.#search();
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
            throw TypeError('The "observable" argument must be instanceof Feature.');
        }
        this.#searchResults = this.#searchResults.filter(ob => ob !== observable);
        this.refreshContent();
        const {configs, nodes, lines} = this.#getCategorizedSearchResults();
        this.#configDropdownDiv.div.firstChild.getElementsByClassName('label')[0].textContent = `Configuration objects: ${configs.length}`;
        this.#nodeDropdownDiv.div.firstChild.getElementsByClassName('label')[0].textContent = `Nodes: ${nodes.length}`;
        this.#lineDropdownDiv.div.firstChild.getElementsByClassName('label')[0].textContent = `Lines: ${lines.length}`;
    }

    /**
     * @param {Feature} observable - an ObservableInterface instance. While this SearchModal is an observer of the FeatureGraph, the FeatureGraph
     *      calls this function with a Feature argument
     * @returns {undefined}
     */
    handleNewObservable(observable) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!(observable instanceof Feature)) {
            throw TypeError('The "observable" argument must be instanceof FeatureGraph.');
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
            throw TypeError('The "observable" argument must be instanceof Feature or FeatureGraph.');
        }
        if (!(oldCoordinates instanceof Array)) {
            throw TypeError('The "oldCoordinates" argument must be an array.');
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
            throw TypeError('The "observable" argument must be instanceof Feature or FeatureGraph.');
        }
        if (typeof propertyKey !== 'string') {
            throw TypeError('The "propertyKey" argument must be a string.');
        }
        if (typeof namespace !== 'string') {
            throw TypeError('The "namespace" argument must be a string.');
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
        return this.#propTable.div;
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
        const that = this;
        keySelects.forEach(oldKeySelect => {
            const index = this.#keySelects.indexOf(oldKeySelect);
            if (index > -1) {
                this.#keySelects.splice(index, 1);
            }
            const newKeySelect = this.#getKeySelect(oldKeySelect);
            oldKeySelect.replaceWith(newKeySelect);
            that.#handleKeySelectChange(newKeySelect);
        });
    }

    /**
     * @returns {undefined}
     */
    remove() {
        if (!this.#removed) {
            this.#configDropdownDiv.div.remove();
            this.#configDropdownDiv = null;
            this.#controller = null;
            this.#keySelects = null;
            this.#lineDropdownDiv.div.remove();
            this.#lineDropdownDiv = null;
            this.#propTable.div.remove();
            this.#propTable = null;
            this.#nodeDropdownDiv.div.remove();
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
        const propTable = new PropTable();
        propTable.div.classList.add('searchModal');
        const keySelect = this.#getKeySelect();
        propTable.insertTBodyRow({elements: [this.#getAddRowButton(), null, keySelect, this.#getOperatorSelect(), this.#getValueTextInput()]});
        this.#handleKeySelectChange(keySelect);
        const searchButton = this.#getSearchButton();
        const resetButton = this.#getResetButton();
        const div = document.createElement('div');
        div.append(searchButton);
        div.append(resetButton);
        propTable.insertTBodyRow({elements: [div], colspans: [5]});
        if (this.#propTable === null) {
            this.#propTable = propTable;
        }
        if (document.body.contains(this.#propTable.div)) {
            this.#propTable.div.replaceWith(propTable.div);
            this.#propTable = propTable;
        }
    }

    // ********************
    // ** Public methods **
    // ********************

    /**
     * @returns {undefined}
     */
    addHighlights() {
        for (const ob of this.#searchResults) {
            if (ob.isNode()) {
                const path = Object.values(ob.getObservers().filter(o => o instanceof LeafletLayer)[0].getLayer()._layers)[0];
                path.setStyle({
                    color: '#7FFF00'
                });
            } else if (ob.isLine()) {
                const path = Object.values(ob.getObservers().filter(o => o instanceof LeafletLayer)[0].getLayer()._layers)[0];
                if (!path.options.hasOwnProperty('originalColor')) {
                    path.options.originalColor = path.options.color;
                }
                path.setStyle({
                    color: '#7FFF00'
                });
            }
        }
    }

    /**
     * - Filter the layer groups so that only the search results are shown
     */
    filterLayerGroups() {
        LeafletLayer.nodeLayers.clearLayers();
        LeafletLayer.nodeClusterLayers.clearLayers();
        LeafletLayer.lineLayers.clearLayers();
        LeafletLayer.parentChildLineLayers.clearLayers();
        for (const observable of this.#searchResults) {
            if (observable.isNode() && !observable.isConfigurationObject()) {
                const ll = observable.getObservers().filter(observer => observer instanceof LeafletLayer)[0];
                if (LeafletLayer.clusterControl._on) {
                    LeafletLayer.nodeClusterLayers.addLayer(ll.getLayer());
                } else {
                    LeafletLayer.nodeLayers.addLayer(ll.getLayer());
                }
            } else if (observable.isLine()) {
                const ll = observable.getObservers().filter(observer => observer instanceof LeafletLayer)[0];
                if (observable.isParentChildLine()) {
                    LeafletLayer.parentChildLineLayers.addLayer(ll.getLayer());
                } else {
                    LeafletLayer.lineLayers.addLayer(ll.getLayer());
                }
            }
        }
        // - Force redraw
        for (const layer of [LeafletLayer.parentChildLineLayers, LeafletLayer.lineLayers, LeafletLayer.nodeLayers, LeafletLayer.nodeClusterLayers]) {
            LeafletLayer.map.removeLayer(layer);
            LeafletLayer.map.addLayer(layer);
        }
    }

    /**
     * - The search results should be able to be inserted anywhere in the DOM, not just directly below the search widget
     * @returns {HTMLDivElement}
     */
    getConfigSearchResultsDiv() {
        return this.#configDropdownDiv.div;
    }

    /**
     * - The search results should be able to be inserted anywhere in the DOM, not just directly below the search widget
     * @returns {HTMLDivElement}
     */
    getLineSearchResultsDiv() {
        return this.#lineDropdownDiv.div;
    }

    /**
     * - The search results should be able to be inserted anywhere in the DOM, not just directly below the search widget
     * @returns {HTMLDivElement}
     */
    getNodeSearchResultsDiv() {
        return this.#nodeDropdownDiv.div;
    }

    /**
     * @returns {undefined}
     */
    removeHighlights() {
        for (const ob of this.#observables[0].getObservables()) {
            if (ob.isNode()) {
                const path = Object.values(ob.getObservers().filter(o => o instanceof LeafletLayer)[0].getLayer()._layers)[0];
                path.setStyle({
                    color: 'black'
                });
            } else if (ob.isLine()) {
                const path = Object.values(ob.getObservers().filter(o => o instanceof LeafletLayer)[0].getLayer()._layers)[0];
                if (path.options.hasOwnProperty('colorModalColor')) {
                    path.setStyle({
                        color: path.options.colorModalColor
                    });
                } else if (path.options.hasOwnProperty('originalColor')) {
                    path.setStyle({
                        color: path.options.originalColor
                    });
                }
            }
        }
    }

    // *********************
    // ** Private methods **
    // *********************

    /**
     * - Create FeatureDropdownDivs and append them to the specified DropdownDiv
     * @param {DropdownDiv} dropdownDiv
     * @param {Array} observables
     * @returns {undefined}
     */
    #appendFeatureDropdownDivs(dropdownDiv, observables) {
        if (!(dropdownDiv instanceof DropdownDiv)) {
            throw TypeError('The "dropdownDiv" argument must be instanceof DropdownDiv.');
        }
        if (!(observables instanceof Array)) {
            throw TypeError('The "observables" argument must instanceof Array.');
        }
        for (const ob of observables) {
            const featureDropdownDiv = new FeatureDropdownDiv(ob, this.#controller);
            dropdownDiv.insertElement({element: featureDropdownDiv.getDOMElement()});
        }
    }

    /**
     * @returns {HTMLButtonElement}
     */
    #getAddRowButton() {
        let button = new IconLabelButton({paths: IconLabelButton.getCirclePlusPaths(), viewBox: '0 0 24 24', tooltip: 'Add search criterion'});
        button.button.classList.add('-green');
        button.button.getElementsByClassName('icon')[0].classList.add('-white');
        button = button.button;
        button.addEventListener('click', () => {
            const keySelect = this.#getKeySelect();
            this.#propTable.insertTBodyRow({elements: [this.#getDeleteRowButton(), this.#getAndOrSelect(), keySelect, this.#getOperatorSelect(), this.#getValueTextInput()], position: 'beforeEnd'});
            this.#handleKeySelectChange(keySelect);
        });
        return button;
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
        let button = new IconLabelButton({paths: IconLabelButton.getTrashCanPaths(), viewBox: '0 0 24 24', tooltip: 'Delete search criterion'});
        button.button.classList.add('-red');
        button.button.getElementsByClassName('icon')[0].classList.add('-white');
        button = button.button;
        if (this.#observables[0] instanceof FeatureGraph) {
            button.classList.add('searchModalDeleteButton');
        } else {
            button.classList.add('componentModalDeleteButton');
        }
        const that = this;
        button.addEventListener('click', function(e) {
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
        return button;
    }

    /**
     * @param {HTMLSelectElement} oldKeySelect - an old key select that should be used to set up the new key select
     * @returns {HTMLSelectElement}
     */
    #getKeySelect(oldKeySelect=null) {
        if (!(oldKeySelect instanceof HTMLSelectElement) && oldKeySelect !== null)  {
            throw TypeError('The "oldKeySelect" argument must be instanceof HTMLKeySelect or null.');
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
    #getResetButton() {
        let button = new IconLabelButton({paths: IconLabelButton.getCircularArrowPaths(), viewBox: '-4 -4 24 24', text: 'Clear', tooltip: 'Clear the search criteria. Also unloads search results which makes the interface faster.'});
        button.button.classList.add('-blue');
        button.button.getElementsByClassName('icon')[0].classList.add('-white');
        button.button.getElementsByClassName('label')[0].classList.add('-white');
        button = button.button;
        button.addEventListener('click', () => {
            if (this.#observables[0] instanceof FeatureGraph) {
                document.querySelectorAll('button.searchModalDeleteButton').forEach(button => button.click());
                document.querySelectorAll('input.searchModalValueInput').forEach(input => input.value = '');
            } else {
                document.querySelectorAll('button.componentModalDeleteButton').forEach(button => button.click());
                document.querySelectorAll('input.componentModalValueInput').forEach(input => input.value = '');
            }
            this.#search();
        });
        return button;
    }

    /**
     * @returns {HTMLButtonElement}
     */
    #getSearchButton() {
        let button = new IconLabelButton({paths: IconLabelButton.getMagnifyingGlassPaths(), viewBox: '0 0 24 24', text: 'Search', tooltip: 'Search objects'})
        button.button.classList.add('-blue');
        button.button.getElementsByClassName('icon')[0].classList.add('-white');
        button.button.getElementsByClassName('label')[0].classList.add('-white');
        button = button.button;
        button.addEventListener('click', () => {
            this.#search();
        });
        return button;
    }

    /**
     * - x
     * @param {Array} searchCriteria - an array of search criteria
     * @returns {Function}
     */
    #getSearchFunction(searchCriteria) {
        if (!(searchCriteria instanceof Array)) {
            throw TypeError('The "searchCriteria" argumet must be instanceof Array.');
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

    #getValueTextInput() {
        const input = document.createElement('input');
        input.dataset.role = 'valueInput';
        if (this.#observables[0] instanceof FeatureGraph) {
            input.classList.add('searchModalValueInput');
        } else {
            input.classList.add('componentModalValueInput');
        }
        return input
    }

    /**
     * - This has to be a function because it's used as an event handler and it's called separately on page load to supply a correct operator select
     * @param {HTMLSelectElement} select
     * @returns {undefined}
     */
    #handleKeySelectChange(select) {
        if (!(select instanceof HTMLSelectElement)) {
            throw TypeError('The "select" argument must be instanceof HTMLSelectElement');
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
     * - Perform the following actions:
     *  1) Use the old/current search results to remove every FeatureDropdownDiv that is currently in the DOM
     *  2) Reset the Leaflet layer groups
     *  3) Set the new search results
     *  4) If needed, filter the Leaflet layer groups
     *  5) Set the text on the three main DropdownDivs to show the number of search results per category
     *  6) If any of the three main DropdownDivs are already expanded when the search is run, then create new FeatureDropdownDivs based on the search
     *     results and append them to the DOM for that cateogry
     * @returns {undefined}
     */
    #search() {
        // - Clear the old FeatureDropdownDivs
        //  - One time I saw a bug where an observable had multiple FeatureDropdownDiv observers, so just remove all of them
        this.#searchResults.forEach(observable => observable.getObservers().filter(observer => observer instanceof FeatureDropdownDiv).forEach(fdd => fdd.remove()));
        // - Clear the old search results
        this.#searchResults = [];
        if (this.#observables[0] instanceof FeatureGraph) {
            // - 2024-11-10: disabled show/hide search results and replaced it with highlight/un-highlight search results
            //LeafletLayer.resetLayerGroups(this.#controller);
            this.removeHighlights();
        }
        // - Clear the old search criteria and build new search criteria
        const searchCriteria = [];
        for (const tr of this.#propTable.div.getElementsByTagName('tr')) {
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
                                return value.toString().toLowerCase() !== valueInputValue.toLowerCase();
                            }
                        }
                        return false;
                    };
                }
                if (operator === 'contains') {
                    searchCriterion.searchFunction = function(ob) {
                        // - TODO: I really should use a JavaScript symbol or something instead of "searchModalSearchAllFields"
                        if (key === 'searchModalSearchAllFields') {
                            for (const [key, val] of Object.entries(ob.getProperties(namespace))) {
                                if (val.toString().toLowerCase().includes(valueInputValue.toLowerCase()) || key.toString().toLowerCase().includes(valueInputValue.toLowerCase())) {
                                    return true;
                                }
                            }
                            if (ob.getProperty('treeKey', 'meta').toString().toLowerCase().includes(valueInputValue.toLowerCase())) {
                                return true;
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
                            if (ob.getProperty('treeKey', 'meta').toString().toLowerCase().includes(valueInputValue.toLowerCase())) {
                                return false;
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
        // - Only filter the layer groups if the user wants to view the search results
        let showSearchResults = document.querySelector('input[type="radio"][name="circuitDisplay"][value="displaySearch"]');
        // - If showSearchResults is null, it's because this is the first search that happens during page load
        if (showSearchResults === null) {
            showSearchResults = false;
        } else {
            showSearchResults = showSearchResults.checked;
        }
        if (this.#observables[0] instanceof FeatureGraph && showSearchResults) {
            // - 2024-11-10: disabled show/hide search results and replaced it with highlight/un-highlight search results
            //this.filterLayerGroups();
            this.addHighlights();
        }
        // - Don't attach event handlers here because then I'll be adding a new event handler after every search!
        const {configs, nodes, lines} = this.#getCategorizedSearchResults();
        for (const [dropdown, features, buttonText] of [[this.#configDropdownDiv, configs, 'Configuration objects'], [this.#nodeDropdownDiv, nodes, 'Nodes'], [this.#lineDropdownDiv, lines, 'Lines']]) {
            dropdown.div.firstChild.getElementsByClassName('label')[0].textContent = `${buttonText}: ${features.length}`
            // - Only create FeatureDropdownDivs and append them to the DOM if 1) this search category DropdownDiv is expanded (which it always
            //   initially is NOT on page load) and 2)
            if (dropdown.isExpanded()) {
                this.#appendFeatureDropdownDivs(dropdown, features);
            }
        }
    }

    /**
     * - Set up a vanilla DropdownDiv so that it can act as a search category
     * @returns {undefined}
     */
    #setupDropdownDiv(dropdownDiv, buttonText) {
        if (!(dropdownDiv instanceof DropdownDiv)) {
            throw TypeError('The "dropdownDiv" argument must be instance of DropdownDiv.');
        }
        if (!['Configuration objects', 'Nodes', 'Lines'].includes(buttonText)) {
            throw Error('');
        }
        const dropdownDivButton = new IconLabelButton({paths: IconLabelButton.getChevronPaths(), viewBox: '0 0 24 24', text: buttonText, textPosition: 'prepend'});
        dropdownDivButton.button.classList.add('-clear');
        const that = this;
        const outerFunc = function(div) {
            if (div.lastChild.classList.contains('-expanded')) {
                div.firstChild.getElementsByClassName('icon')[0].classList.add('-rotated');
                // - If the user clicked "search" while this category was already expanded, then this.#search() already removed all of the old
                //   FeatureDropdownDivs and appended new FeatureDropdownDivs
                // - If the user clicked "search" while this category was not expanded, then this.#search() already removed all of the old
                //   FeatureDropdownDivs
                // - Therefore, THIS function should only append new FeatureDropdownDivs if this category was just expanded as a result of clicking on
                //   the category button AND there are no children
                if (div.lastChild.children.length === 0) {
                    div.firstChild.getElementsByClassName('label')[0].textContent = 'Loading search results...';
                    setTimeout(() => {
                        const {configs, nodes, lines} = that.#getCategorizedSearchResults();
                        if (buttonText === 'Configuration objects') {
                            that.#appendFeatureDropdownDivs(dropdownDiv, configs);
                            div.firstChild.getElementsByClassName('label')[0].textContent = `Configuration objects: ${configs.length}`;
                        } else if (buttonText === 'Nodes') {
                            that.#appendFeatureDropdownDivs(dropdownDiv, nodes);
                            div.firstChild.getElementsByClassName('label')[0].textContent = `Nodes: ${nodes.length}`;
                        } else {
                            that.#appendFeatureDropdownDivs(dropdownDiv, lines);
                            div.firstChild.getElementsByClassName('label')[0].textContent = `Lines: ${lines.length}`;
                        }
                        // - Option to expand every nested DropdownDiv
                        //for (const dropdownDiv of div.getElementsByClassName('dropdown-div')) {
                        //    if (!dropdownDiv.lastChild.classList.contains('-expanded')) {
                        //        dropdownDiv.firstChild.click();
                        //    }
                        //}
                    });
                }
            } else {
                div.firstChild.getElementsByClassName('icon')[0].classList.remove('-rotated');
                // - Option to retract every nested DropdownDiv
                for (const dropdownDiv of div.getElementsByClassName('dropdown-div')) {
                    if (dropdownDiv.lastChild.classList.contains('-expanded')) {
                        dropdownDiv.firstChild.click();
                    }
                }
            }
        };
        dropdownDivButton.button.addEventListener('click', dropdownDiv.getToggleFunction({outerFunc: outerFunc}));
        dropdownDiv.div.prepend(dropdownDivButton.button);
    }
}