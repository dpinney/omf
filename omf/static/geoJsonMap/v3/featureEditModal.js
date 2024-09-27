export { FeatureEditModal, zoom };
import { Feature, UnsupportedOperationError } from './feature.js';
import { PropTable } from '../v4/ui-components/prop-table/prop-table.js';
import { FeatureController } from './featureController.js';
import { LeafletLayer } from './leafletLayer.js';
import { IconLabelButton } from '../v4/ui-components/iconlabel-button/iconlabel-button.js';

class FeatureEditModal { // implements ObserverInterface, ModalInterface

    #controller;    // - ControllerInterface instance
    #propTable;     // - A PropTable instance
    #observables;   // - An array of ObservableInterface instances
    #removed;       // - Whether this FeatureEditModal instance has already been deleted
    static #nonDeletableProperties = ['name', 'object', 'from', 'to', 'parent', 'latitude', 'longitude', 'treeKey', 'CMD_command'];

    /**
     * @param {Array} observables - an array of ObservableInterface instances
     * @param {FeatureController} controller - a ControllerInterface instance
     * @returns {undefined}
     */
    constructor(observables, controller) {
        if (!(observables instanceof Array)) {
            throw TypeError('"observables" argumnet must be an Array.');
        }
        if (!(controller instanceof FeatureController)) {
            throw Error('"controller" argument must be instanceof FeatureController');
        }
        this.#controller = controller;
        this.#propTable = null;
        this.#observables = observables;
        this.#observables.forEach(ob => ob.registerObserver(this));
        this.#removed = false;
        this.renderContent();
    }

    // *******************************
    // ** ObserverInterface methods ** 
    // *******************************

    /**
     * - Remove this ObserverInterface instance (i.e. "this") from the ObservableInterface instance (i.e. "observable") that has been deleted, and
     *   perform other actions as needed
     * @param {Feature} observable - an ObservableInterface instance
     * @returns {undefined}
     */
    handleDeletedObservable(observable) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!(observable instanceof Feature)) {
            throw TypeError('"observable" argument must be instanceof Feature.');
        }
        if (!this.#removed) {
            observable.removeObserver(this);
            const index = this.#observables.indexOf(observable);
            if (index > -1) {
                this.#observables.splice(index, 1);
            } else {
                throw Error('The observable was not found in this.#observables.');
            }
            if (this.#observables.length === 0) {
                this.remove();
            } else {
                this.refreshContent();
            }
        }
    }

    /**
     *
     */
    handleNewObservable(observable) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        throw new UnsupportedOperationError();
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
        if (!(observable instanceof Feature)) {
            throw TypeError('"observable" argument must be instanceof Feature.');
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
        if (!(observable instanceof Feature)) {
            throw TypeError('"observable" argument must be instanceof Feature.');
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
     * - Refresh aspects of the modal so that I don't have to re-render the whole thing
     * @returns {undefined}
     */
    refreshContent() {
        const tableState = {};
        // - Don't grab a row that was added with the "+" button, if it exists
        //[...this.#modal.divElement.getElementsByTagName('tr')].filter(tr => tr.querySelector('span[data-property-key]') !== null).forEach(tr => {
        [...this.#propTable.div.getElementsByTagName('tr')].filter(tr => tr.querySelector('span[data-property-key]') !== null).forEach(tr => {

            const span = tr.getElementsByTagName('span')[0];
            let namespace = span.dataset.propertyNamespace;
            // - latitude and longitude don't exist in any property namespace
            if (namespace === undefined) {
                namespace = null;
            }
            tableState[span.dataset.propertyKey] = {
                propertyNamespace: namespace,
                propertyTableRow: tr,
                // - This is either an input or a span
                propertyValueElement: tr.children[2].children[0].children[0]
            }
        });
        const tableKeys = Object.keys(tableState);
        const observablesState = this.#getKeyToValuesMapping();
        for (const [key, ary] of Object.entries(observablesState.meta)) {
            const valueElement = tableState[key].propertyValueElement;
            if (valueElement instanceof HTMLSpanElement) {
                valueElement.textContent = ary.join(',');
            } else {
                // - Only the treeKey should be in the meta namespace and the treeKey only ever displays with a span
                throw Error()
            }
        }
        for (const [key, ary] of Object.entries(observablesState.treeProps)) {
            // - First, compare the observables' state to the table state. If the observables' state has a property that is not in the table state,
            //   add a row to the table
            if (!tableKeys.includes(key)) {
                // - Don't let unintended properties show up when a FeatureEditModal refreshes due to a marker being dragged
                if (['from', 'to'].includes(key)) {
                    if (!this.#observables.every(ob => ob.isLine() && !ob.isParentChildLine())) {
                        continue;
                    }
                }
                if (key === 'type' && !this.#observables.every(ob => ob.isParentChildLine())) {
                    continue;
                }
                if (key === 'parent' && !this.#observables.every(ob => ob.isChild())) {
                    continue;
                }
                const keySpan = document.createElement('span');
                keySpan.textContent = key;
                keySpan.dataset.propertyKey = key;
                keySpan.dataset.propertyNamespace = 'treeProps';
                //this.#modal.insertTBodyRow([this.#getDeletePropertyButton(key), keySpan, this.#getValueTextInput(key, ary)], 'beforeEnd');
                this.#propTable.insertTBodyRow({elements: [this.#getDeletePropertyButton(key), keySpan, this.#getValueTextInput(key, ary)], position: 'beforeEnd'});

            } else {
                // - If the table has the key, update the display of the values for that key
                const valueElement = tableState[key].propertyValueElement;
                if (valueElement instanceof HTMLInputElement) {
                    valueElement.replaceWith(this.#getValueTextInput(key, ary));
                } else if (valueElement instanceof HTMLSpanElement) {
                    valueElement.textContent = ary.join(', ');
                }
            }
        }
        for (const [key, ary] of Object.entries(observablesState.coordinates)) {
            // - Don't add latitude or longitude rows to tables that didn't already have those rows, just update the existing inputs
            if (tableKeys.includes(key)) {
                const valueElement = tableState[key].propertyValueElement;
                if (valueElement instanceof HTMLInputElement) {
                    valueElement.replaceWith(this.#getValueTextInput(key, ary));
                }
            }
        }
        // - Now compare the table's state to the observables' state. If the table's state has a property that is not in the observables' state,
        //   remove the row from the table
        const observablesKeysFromAllNamespaces = [];
        for (const obj of Object.values(observablesState)) {
            observablesKeysFromAllNamespaces.push(...Object.keys(obj))
        }
        for (const [key, obj] of Object.entries(tableState)) {
            if (!observablesKeysFromAllNamespaces.includes(key)) {
                obj.propertyTableRow.remove();
            }
        }
    }

    /**
     * @returns {undefined}
     */
    remove() {
        if (!this.#removed) {
            this.#observables.forEach(ob => ob.removeObserver(this));
            this.#observables = null;
            this.#propTable.div.remove();
            this.#removed = true;
        }
    }

    /**
     * - Render the modal for the first time
     * @returns {undefined}
     */
    renderContent() {
        const propTable = new PropTable();
        propTable.div.classList.add('featureEditModal');
        if (this.#observables[0].hasProperty('treeKey', 'meta')) {
            this.#renderOmfFeatures(propTable);
        } else {
            this.#renderArbitraryFeatures(propTable);
        }
        propTable.div.addEventListener('click', function(e) {
            // - Don't let clicks on the table cause the popup to close
            e.stopPropagation();
        });
        if (this.#propTable === null) {
            this.#propTable = propTable;
        }
        if (document.body.contains(this.#propTable.div)) {
            this.#propTable.div.replaceWith(propTable.div);
            this.#propTable = propTable;
        }
    }

    // *********************
    // ** Private methods ** 
    // *********************

    /**
     * @returns {boolean}
     */
    #componentsStateIsValid() {
        for (const ob of this.#observables) {
            for (const [k, v] of Object.entries(ob.getProperties('treeProps'))) { 
                if (!this.#valueTextInputIsValid(k, v)) {
                    return false;
                }
            }
        }
        return true;
    }

    /**
     * - Add a configuration object to the data. Components arrive with bad data. That's why I have to validate a component twice: once during any
     *   value input changes and once when the button is clicked. I assume that regular features arrive with valid data. That's why I only validate
     *   when an input changes
     * @returns {HTMLButtonElement}
     */
    #getAddConfigurationObjectButton() {
        let button = new IconLabelButton({paths: IconLabelButton.getCirclePlusPaths(), viewBox: '0 0 24 24', text: 'Add config object'});
        button.button.classList.add('-green');
        button.button.getElementsByClassName('icon')[0].classList.add('-white');
        button.button.getElementsByClassName('label')[0].classList.add('-white');
        button = button.button;
        button.addEventListener('click', () => {
            if (this.#componentsStateIsValid()) {
                this.#controller.addObservables(this.#observables.map(ob => this.#getObservableFromComponent(ob)));
            }
        });
        return button;
    }

    /**
     * - Add a line to the map by inputing "from" and "to" values and then clicking this button
     * @returns {HTMLButtonElement}
     */
    #getAddLineWithFromToButton() {
        let button = new IconLabelButton({paths: IconLabelButton.getCirclePlusPaths(), viewBox: '0 0 24 24', text: 'Add line with from/to', tooltip: 'Add a new line by entering the name of a node for the "from" property and entering the name of another node in the "to" property'});
        button.button.classList.add('-green');
        button.button.getElementsByClassName('icon')[0].classList.add('-white');
        button.button.getElementsByClassName('label')[0].classList.add('-white');
        button = button.button;
        button.addEventListener('click', () => {
            if (this.#componentsStateIsValid()) {
                this.#controller.addObservables(this.#observables.map(ob => this.#getObservableFromComponent(ob)));
            }
        });
        return button;
    }

    /**
     * - Add a node to the map by inputing coordinates and then clicking this button
     * @returns {HTMLDivElement}
     */
    //#getAddNodeWithCoordinatesDiv() {
    //    const btn = this.#getWideButton();
    //    btn.classList.add('add');
    //    btn.appendChild(getCirclePlusSvg());
    //    const span = document.createElement('span');
    //    span.textContent = 'Add with coordinates';
    //    btn.appendChild(span);
    //    btn.addEventListener('click', () => {
    //        if (this.#componentsStateIsValid()) {
    //            this.#controller.addObservables(this.#observables.map(ob => this.#getObservableFromComponent(ob)));
    //        }
    //    });
    //    const div = this.#getWideButtonDiv();
    //    div.appendChild(btn);
    //    return div;
    //}

    /**
     * - Add a node to the map by clicking on the map
     * @returns {HTMLDivElement}
     */
    #getAddNodeWithMapClickButton() {
        let button = new IconLabelButton({paths: IconLabelButton.getCirclePlusPaths(), viewBox: '0 0 24 24', text: 'Add object with map click', tooltip: 'Click this button, then click on the map to create a new instance of this object'});
        button.button.classList.add('-green');
        button.button.getElementsByClassName('icon')[0].classList.add('-white');
        button.button.getElementsByClassName('label')[0].classList.add('-white');
        button = button.button;
        const that = this;
        button.addEventListener('click', () => {
            const mapDiv = document.getElementById('map');
            mapDiv.style.cursor = 'crosshair';
            LeafletLayer.map.on('click', function(e) {
                LeafletLayer.map.off('click');
                mapDiv.style.removeProperty('cursor');
                if (that.#componentsStateIsValid()) {
                    that.#controller.addObservables(that.#observables.map(ob => that.#getObservableFromComponent(ob, [e.latlng.lat, e.latlng.lng])));
                }
            });
        });
        return button;
    }
    
    /**
     * @returns {HTMLButtonElement}
     */
    #getAddPropertyButton() {
        let button = new IconLabelButton({paths: IconLabelButton.getCirclePlusPaths(), viewBox: '0 0 24 24', tooltip: 'Add new property'});
        button.button.classList.add('-green');
        button.button.getElementsByClassName('icon')[0].classList.add('-white');
        button = button.button;
        const that = this;
        button.addEventListener('click', function() {
            const deletePlaceholder = document.createElement('span');
            const keyInputPlaceholder = document.createElement('span');
            const valueInputPlaceholder = document.createElement('span');
            that.#propTable.insertTBodyRow({elements: [deletePlaceholder, keyInputPlaceholder, valueInputPlaceholder], position: 'beforeEnd'});
            that.#insertKeyTextInput(deletePlaceholder, keyInputPlaceholder, valueInputPlaceholder);
        });
        return button;
    }

    /**
     * @returns {HTMLDivElement}
     */
    #getDeleteFeatureButton() {
        let button = new IconLabelButton({paths: IconLabelButton.getTrashCanPaths(), viewBox: '0 0 24 24', tooltip: 'Delete object'});
        button.button.classList.add('-red');
        button.button.getElementsByClassName('icon')[0].classList.add('-white');
        button = button.button;
        button.addEventListener('click', () => {
            this.#controller.deleteObservables(this.#observables);    
        });
        return button;
    }
    
    /**
     * @param {string} propertyKey
     * @returns {HTMLButtonElement} a button that can be clicked on to remove a property from an ObservableInterface instance
     */
    #getDeletePropertyButton(propertyKey) {
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be a string.');
        }
        let button = new IconLabelButton({paths: IconLabelButton.getTrashCanPaths(), viewBox: '0 0 24 24', tooltip: 'Delete property'});
        button.button.classList.add('-red');
        button.button.getElementsByClassName('icon')[0].classList.add('-white');
        button = button.button;
        const that = this;
        button.addEventListener('click', function(e) {
            that.#controller.deleteProperty(that.#observables, propertyKey);
            // - This is code is required for a transitionalDeleteButton to remove the row
            let parentElement = this.parentElement;
            while (!(parentElement instanceof HTMLTableRowElement)) {
                parentElement = parentElement.parentElement;
            }
            parentElement.remove();
            e.stopPropagation();
        });
        return button;
    }

    /**
     * - Iterate through all of the observables and map each property key to all unique values for that (treeProps) property key across all of the
     *   observables. Also includes treeKey, longitude, and latitude values
     * @returns {Object}
     */
    #getKeyToValuesMapping() {
        const keyToValues = {
            meta: {},
            treeProps: {},
            coordinates: {}
        };
        this.#observables.forEach(ob => {
            const treeKey = ob.getProperty('treeKey', 'meta');
            if (!keyToValues.meta.hasOwnProperty('treeKey')) {
                keyToValues.meta.treeKey = [treeKey];
            } else if (!keyToValues.meta.treeKey.includes(treeKey)) {
                keyToValues.meta.treeKey.push(treeKey);
            }
            if (ob.hasProperty('treeProps', 'meta')) {
                for (const [k, v] of Object.entries(ob.getProperties('treeProps'))) {
                    if (!keyToValues.treeProps.hasOwnProperty(k)) {
                        keyToValues.treeProps[k] = [v];
                    } else if (!keyToValues.treeProps[k].includes(v)) {
                        keyToValues.treeProps[k].push(v);
                    }
                }
            }
            let coordinatesArray = [];
            if (ob.isNode()) {
                const [lon, lat] = ob.getCoordinates();
                coordinatesArray = [['longitude', +lon], ['latitude', +lat]];
            }
            if (ob.isLine()) {
                const [[lon_1, lat_1], [lon_2, lat_2]] = ob.getCoordinates();
                coordinatesArray = [['longitude', +lon_1], ['latitude', +lat_1], ['longitude', +lon_2], ['latitude', +lat_2]];
            }
            coordinatesArray.forEach(ary => {
                const k = ary[0];
                const v = ary[1];
                if (!keyToValues.coordinates.hasOwnProperty(k)) {
                    keyToValues.coordinates[k] = [v];
                } else if (!keyToValues.coordinates[k].includes(v)) {
                    keyToValues.coordinates[k].push(v);
                }
            });
        });
        return keyToValues;
    }

    /**
     * - TODO: move this into the controller? Wouldn't be so bad if I did. Actually I should because of mass add. But mass add should just be another
     *   button so this function can stay here.
     * @param {Feature} component - a component feature
     * @param {Array} [coordinates=null] - an array of coordinates in [<lat>, <lon>] format that the new feature should have instead of the
     *      coordinates that were in the component 
     * @returns {Feature} a feature that can be added to the graph
     */
    #getObservableFromComponent(component, coordinates=null) {
        if (!(component instanceof Feature)) {
            throw TypeError('"component" argument must be instanceof Feature.');
        }
        const geometry = {
            type: 'Point'
        };;
        const observable = new Feature({
            geometry: geometry,
            properties: {
                treeKey: component.getProperty('treeKey', 'meta'),
                treeProps: structuredClone(component.getProperties('treeProps'))
            },
            type: 'Feature'
        });
        // - Start with whatever coordinates were in the text inputs
        let featureCoordinates = structuredClone(component.getCoordinates());
        // - If coordinates were provided, use those instead
        if (coordinates !== null) {
            featureCoordinates = [coordinates[1], coordinates[0]];
        }
        // - If the component is a line, get the coordinates of its nodes
        if (component.isLine()) {
            geometry.type = 'LineString';
            const fromKey = this.#controller.observableGraph.getKeyForComponent(observable.getProperty('from'));
            const toKey = this.#controller.observableGraph.getKeyForComponent(observable.getProperty('to'));
            const { sourceLat, sourceLon, targetLat, targetLon } = this.#controller.observableGraph.getLineLatLon(fromKey, toKey);
            featureCoordinates = [[sourceLon, sourceLat], [targetLon, targetLat]];
        }
        geometry.coordinates = featureCoordinates;
        return observable;
    }

    /**
     * - Return a text input that can be viewed in a modal
     * @param {string} propertyKey
     * @param {Array} [propertyValues=null]
     * @returns {HTMLInputElement} a text input that can be edited on to change a property value in an ObservableInterface instance
     */
    #getValueTextInput(propertyKey, propertyValues=null) {
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be typeof string.');
        }
        if (!(propertyValues instanceof Array) && propertyValues !== null) {
            throw TypeError('"propertyValues" argument must be instanceof Array or null.');
        }
        const input = document.createElement('input');
        input.addEventListener('mousedown', (e) => {
            e.stopPropagation(e);
        });
        if (propertyValues === null) {
            //- Do nothing. A new property was just added so the value text input should be blank
        } else if (propertyValues.length === 1) {
            // - This works even if propertyValues = [""], which it can be sometimes
            input.value = propertyValues[0];
        } else {
            //input.value = `<Multiple "${propertyKey}" values>`;
            input.value = propertyValues.join(', ');
        }
        let originalValue = input.value;
        const that = this;
        input.addEventListener('change', function() {
            const inputValue = this.value.trim();
            if (that.#valueTextInputIsValid(propertyKey, inputValue)) {
                that.#observables.forEach(ob => {
                    if (['latitude', 'longitude'].includes(propertyKey)) {
                        if (ob.isNode()) {
                            const [lon, lat] = ob.getCoordinates();
                            if (propertyKey === 'latitude') {
                                that.#controller.setCoordinates([ob], [lon, inputValue]);
                            } else {
                                that.#controller.setCoordinates([ob], [inputValue, lat]);
                            }
                        } else if (ob.isLine()) {
                            const [[lon, lat], [lon_1, lat_1]] = ob.getCoordinates(); 
                            if (propertyKey === 'latitude') {
                                that.#controller.setCoordinates([ob], [[lon, inputValue], [lon_1, inputValue]]);
                            } else {
                                that.#controller.setCoordinates([ob], [[inputValue, lat], [inputValue, lat_1]]);
                            }
                        }
                    } else if (['from', 'to', 'parent'].includes(propertyKey)) {
                        that.#controller.setProperty([ob], propertyKey, inputValue);
                    } else {
                        that.#controller.setProperty([ob], propertyKey, inputValue);
                    }
                });
                originalValue = inputValue;
            } else {
                this.value = originalValue;
            }
        });
        return input;
    }
    
    /**
     * @returns {HTMLButtonElement}
     */
    #getZoomButton() {
        let button = new IconLabelButton({paths: IconLabelButton.getPinPaths(), viewBox: '0 0 24 24', tooltip: 'Zoom to object'});
        button.button.classList.add('-blue');
        button.button.getElementsByClassName('icon')[0].classList.add('-white');
        button = button.button;
        button.addEventListener('click', zoom.bind(null, this.#observables));
        return button;
    }

    /**
     * @param {Node} deletePlaceholder - a document node that will be replaced by a "delete property" button
     * @param {Node} keyInputPlaceholder - a document node that will be replaced by this key input
     * @param {Node} valueInputPlaceholder - a document node that will be replaced by a value input 
     * @returns {undefined}
     */
    #insertKeyTextInput(deletePlaceholder, keyInputPlaceholder, valueInputPlaceholder) {
        const input = document.createElement('input');
        keyInputPlaceholder.replaceWith(input);
        const transitionalDeleteButton = this.#getDeletePropertyButton('');
        deletePlaceholder.replaceWith(transitionalDeleteButton);
        const that = this;
        let originalValue = input.value;
        input.addEventListener('change', function () {
            const inputValue = this.value.trim();
            // - If the input value isn't valid, just don't create a text input for the value and don't update the feature's properties
            if (that.#keyTextInputIsValid(inputValue)) {
                let parentElement = this.parentElement;
                while (!(parentElement instanceof HTMLTableRowElement)) {
                    parentElement = parentElement.parentElement;
                }
                parentElement.remove();
                that.#controller.setProperty(that.#observables, inputValue, '', 'treeProps');
            } else {
                input.value = originalValue;
            }
        });
    }

    /**
     * @param {string} inputValue
     * @returns {boolean}
     */
    #keyTextInputIsValid(inputValue) {
        // - I am no longer always converting to lowercase because names are case-sensitive and therefore other properties should be too
        if (FeatureEditModal.#nonDeletableProperties.includes(inputValue)) {
            alert(`The following properties cannot be added to objects: ${FeatureEditModal.#nonDeletableProperties}.`);
            return false;
        } else if (inputValue === '') {
            return false;
        } else if (this.#observables.some(ob => ob.hasProperty(inputValue))) {
            if (this.#observables.length === 1) {
                alert(`The property "${inputValue}" could not be added because this object already has this property.`);
            } else {
                alert(`The property "${inputValue}" could not be added because one or more objects already has this property.`);
            }
            return false;
        }
        return true;
    }

    /**
     * - Render normal features
     */
    #renderOmfFeatures(propTable) {
        const keyToValues = this.#getKeyToValuesMapping();
        for (const [key, ary] of Object.entries(keyToValues.meta)) {
            const keySpan = document.createElement('span');
            keySpan.textContent = 'ID';
            keySpan.dataset.propertyKey = 'treeKey';
            keySpan.dataset.propertyNamespace = 'meta';
            if (ary.length === 1) {
                propTable.insertTHeadRow({elements: [null, keySpan, ary[0].toString()], position: 'prepend'})
            } else {
                propTable.insertTHeadRow({elements: [null, keySpan, ary.join(',')], position: 'prepend'});
            }
        }
        for (const [key, ary] of Object.entries(keyToValues.treeProps)) {
            const keySpan = document.createElement('span');
            if (['object'].includes(key)) {
                keySpan.textContent = key;
                keySpan.dataset.propertyKey = key;
                keySpan.dataset.propertyNamespace = 'treeProps';
                if (ary.length === 1) {
                    propTable.insertTHeadRow({elements: [null, keySpan, ary[0].toString()]});
                } else {
                    propTable.insertTHeadRow({elements: [null, keySpan, ary.join(', ')]});
                }
                continue;
            }
            if (['from', 'to'].includes(key)) {
                if (!this.#observables.every(ob => ob.isLine() && !ob.isParentChildLine())) {
                    continue;
                }
            }
            if (key === 'type' && !this.#observables.every(ob => ob.isParentChildLine())) {
                continue;
            }
            if (key === 'parent' && !this.#observables.every(ob => ob.isChild())) {
                continue;
            }
            keySpan.textContent = key;
            keySpan.dataset.propertyKey = key;
            keySpan.dataset.propertyNamespace = 'treeProps';
            let deleteButton = null;
            if (!FeatureEditModal.#nonDeletableProperties.includes(key)) {
                deleteButton = this.#getDeletePropertyButton(key);
            }
            propTable.insertTBodyRow({elements: [deleteButton, keySpan, this.#getValueTextInput(key, ary)]});
        }
        // - We don't allow the coordinates of multiple objects to be changed with multiselect
        if (this.#observables.length === 1) {
            for (const [key, ary] of Object.entries(keyToValues.coordinates)) {
                const keySpan = document.createElement('span');
                if (['latitude', 'longitude'].includes(key)) {
                    if (!this.#observables.every(ob => ob.isNode() && !ob.isConfigurationObject())) {
                        continue;
                    } else {
                        keySpan.textContent = key;
                        keySpan.dataset.propertyKey = key;
                        // - longitude and latitude aren't in any property namespace
                        propTable.insertTBodyRow({elements: [null, keySpan, this.#getValueTextInput(key, ary)], position: 'prepend'});
                    }
                }
            }
        }
        // - I need this div to applying consistent CSS styling
        const div = document.createElement('div');
        if (this.#observables.every(ob => !ob.isComponentFeature()) && this.#observables.every(ob => !ob.isConfigurationObject())) {
            const zoomButton = this.#getZoomButton();
            const deleteButton = this.#getDeleteFeatureButton();
            div.append(zoomButton);
            div.append(deleteButton);
            propTable.insertTBodyRow({elements: [this.#getAddPropertyButton(), null, div]});
        } else if (this.#observables.every(ob => !ob.isComponentFeature())) {
            div.append(this.#getDeleteFeatureButton());
            propTable.insertTBodyRow({elements: [this.#getAddPropertyButton(), null, div]});
        // - Add buttons for components
        } else {
            if (this.#observables.every(ob => ob.isConfigurationObject())) {
                div.append(this.#getAddConfigurationObjectButton());
                propTable.insertTBodyRow({elements: [div], colspans: [3]});
            } else if (this.#observables.some(ob => ob.isConfigurationObject())) {
                // - Don't add buttons. Configuration objects cannot be added because not every observable is a configuration object.
                //   Non-configuration objects cannot be added because there is at least one configuration object. The user should refine their search
                //   results, but mixing configuration and non-configuration objects isn't necessarily an error
            } else {
                if (this.#observables.every(ob => ob.isNode())) {
                    div.append(this.#getAddNodeWithMapClickButton());
                    propTable.insertTBodyRow({elements: [div], colspans: [3]});
                } else if (this.#observables.every(ob => ob.isLine())) {
                    div.append(this.#getAddLineWithFromToButton())
                    propTable.insertTBodyRow({elements: [div], colspans: [3]});
                } else {
                    // - Don't add buttons. The user's search returned both nodes and lines
                }
            }
        }
    }

    /**
     * - Render arbitrary features
     */
    #renderArbitraryFeatures(propTable) {
        for (const [key, val] of Object.entries(this.#observables[0].getProperties('meta'))) {
            if (key === 'TRACT') {
                propTable.insertTHeadRow({elements: [null, null, 'Census Tract', val.toString()], position: 'prepend'});
            } else if (key === 'SOVI_SCORE') {
                propTable.insertTBodyRow({elements: [null, null, 'Social Vulnerability Score', val.toString()]});
            } else if (key === 'SOVI_RATNG') {
                propTable.insertTBodyRow({elements: [null, null, 'Social Vulnerability Rating', val.toString()]});
            } else {
                propTable.insertTBodyRow({elements: [null, null, key, val.toString()]});
            }
        }
    }

    /**
     * @param {string} propertyKey
     * @param {string} inputValue
     * @returns {boolean}
     */
    #toFromParentObjectIsValid(propertyKey, inputValue) {
        let observableKey;
        try {
            if (this.#observables.every(ob => ob.isComponentFeature())) {
                observableKey = this.#controller.observableGraph.getKeyForComponent(inputValue);
            } else if (this.#observables.every(ob => !ob.isComponentFeature())) {
                observableKey = this.#controller.observableGraph.getKey(inputValue, this.#observables[0].getProperty('treeKey', 'meta'));
                // - This is commented out because it's fine if different objects in the search selection will return different keys. If there are
                //   different keys for the same name, the FeatureGraph should just return the correct key for each object. Actually it's not. What if a
                //   configuration object and a non-configuration object share a name? I could write logic that decides whether returning multiple keys is
                //   okay (e.g. do both keys point to non-configuration objects?) but that would be annoying. Just return false if there are multiple keys
                if (this.#observables.some(ob => this.#controller.observableGraph.getKey(inputValue, ob.getProperty('treeKey', 'meta')) !== observableKey)) {
                    alert(`The value of the "${propertyKey}" property cannot be set to "${inputValue}" because multiple objects have that value for their
                        "name" property. Either ensure that value for the "${propertyKey}" property is a unique name, or change the value of the
                        "name" property of other object(s) to ensure the name is unique.`);
                    return false;
                }
            } else {
                throw Error('Components and non-components should never be together in this.#observables');
            }
        } catch {
            alert(`No object has the value "${inputValue}" for the "name" property. Ensure that the value for the "${propertyKey}" property matches an existing name.`);
            return false;
        }
        if (observableKey.startsWith('parentChild:')) {
            alert(`The value "${inputValue}" is the name of a parent-child line. Parent-child line names cannot be used as a value for the "${propertyKey}" property.`);
            return false;
        }
        const observable = this.#controller.observableGraph.getObservable(observableKey);
        if (observable.isConfigurationObject()) {
            alert(`The value "${inputValue}" is the name of a configuration object. Configuration object names cannot be used as a value for the "${propertyKey}" property.`);
            return false;
        }
        // - Components are not in the graph, so the observable cannot be a component feature
        return true;
    } 

    /**
     * - Validate the just-inputed value for a value text input
     * @param {string} propertyKey
     * @param {string} inputValue
     * @returns {boolean} whether the propertyKey and value are valid from a domain perspective
     */
    #valueTextInputIsValid(propertyKey, inputValue) {
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be typeof string.');
        }
        if (typeof inputValue !== 'string') {
            throw TypeError('"inputValue" argument must be typeof string.');
        }
        // - I am no longer always converting to lowercase because names are case-sensitive and therefore other properties should be too
        switch (propertyKey) {
            case 'type':
                inputValue = inputValue.toLowerCase();
                if (inputValue === 'parentchild') {
                    alert('The "type" property may not have a value of "parentChild".');
                    return false;
                }
                return true;
            case 'treeKey':
                alert('The "treeKey" property cannot be changed.');
                return false;
            case 'name':
                if (this.#observables.length > 1) {
                    alert('The "name" property cannot be edited for multiple objects simultaneously.');
                    return false;
                } else {
                    if (inputValue.trim() === '') {
                        alert('The "name" property cannot be blank.');
                        return false;
                    }
                    if (this.#controller.observableGraph.getObservables(ob => ob.hasProperty('name') && ob.getProperty('name') === inputValue).length > 0) {
                        alert(`The "name" property must be unique for all objects. The name "${inputValue}" is already used by another object.`);
                        return false;
                    }
                }
                return true;
            case 'from':
            case 'to':
                // - Test. It works
                //[...this.#modal.divElement.getElementsByTagName('tr')].forEach(tr => {
                //    [...tr.getElementsByTagName('span')].forEach(span => {
                //        if (span.textContent === propertyKey) {
                //            tr.getElementsByTagName('input')[0].classList.add('invalid');
                //        }
                //    });
                //});
                // - Test
                if (!this.#observables.every(ob => ob.isLine())) {
                    alert(`The value of the "${propertyKey}" property cannot be edited for non-line objects. Ensure your search includes only line objects.`);
                    return false;
                }
                if (!this.#toFromParentObjectIsValid(propertyKey, inputValue)) {
                    return false;
                }
                if (propertyKey === 'from' && this.#observables.some(ob => ob.getProperty('to') === inputValue)) {
                    if (this.#observables.length === 1) {
                        alert(`This line already has the value "${inputValue}" for the property "to". Lines may not begin and end on the same object.`);
                    } else {
                        alert(`One or more objects already has the value "${inputValue}" for the property "to". Lines may not begin and end on the same object.`);
                    }
                    return false;
                }
                if (propertyKey === 'to' && this.#observables.some(ob => ob.getProperty('from') === inputValue)) {
                    if (this.#observables.length === 1) {
                        alert(`This line already has the value "${inputValue}" for the property "from". Lines may not begin and end on the same object.`);
                    } else {
                        alert(`One or more objects already has the value "${inputValue}" for the property "from". Lines may not begin and end on the same object.`);
                    }
                    return false;
                }
                return true;
            case 'parent':
                if (!this.#observables.every(ob => ob.isChild())) {
                    alert(`The value of the "${propertyKey}" property cannot be edited for non-child objects. Ensure your search includes only child objects.`);
                    return false;
                }
                return this.#toFromParentObjectIsValid(propertyKey, inputValue);
            case 'latitude':
            case 'longitude':
                if (this.#observables.some(ob => ob.isConfigurationObject())) {
                    if (this.#observables.length === 1) {
                        alert(`This object is a configuration object. The property "${propertyKey}" cannot be set for configuration objects because they aren't shown on the map.`);
                    } else {
                        alert(`One or more objects are configuration objects. The property "${propertyKey}" cannot be set for configuration objects because they aren't shown on the map.`);
                    }
                    return false;
                }
                if (inputValue === '' || isNaN(+inputValue)) {
                    alert(`The value "${inputValue}" is not a valid number. A value for the "${propertyKey}" property must be a valid number.`);
                    return false;
                }
                return true;
            default:
                return true;
        }
    }
}

/**
 * - There's no need to create a function that returns a function if I use Function.prototype.bind() propertly
 * @param {Array} observables - an array of ObservableInterface instances
 * @returns {undefined}
 */
function zoom(observables) {
    if (!(observables instanceof Array)) {
        throw TypeError('"observables" argument must be instanceof Array.');
    }
    if (observables.length === 1) {
        const observable = observables[0];
        const layer = observable.getObservers().filter(ob => ob instanceof LeafletLayer)[0];
        const leafletLayer = Object.values(layer.getLayer()._layers)[0];
        if (observable.isNode()) {
            const [lon, lat] = structuredClone(observable.getCoordinates());
            // - The max zoom level without losing the map is 19
            LeafletLayer.map.flyTo([lat, lon], 19, {duration: .3});
            layer.bindPopup();
            if (!leafletLayer.isPopupOpen()) {
                leafletLayer.openPopup();
            }
        } else if (observable.isLine()) {
            const [[lon1, lat1], [lon2, lat2]] = observable.getCoordinates();
            LeafletLayer.map.flyTo([(lat1 + lat2) / 2, (lon1 + lon2) / 2], 19, {duration: .3});
            if (!leafletLayer.isPopupOpen()) {
                leafletLayer.openPopup();
            }
        } else {
            throw Error('Zoom button is only supported for nodes and lines.');
            //let coordinates;
            //if (observable.isPolygon()) {
            //    coordinates = observable.getCoordinates().flat(1);
            //} else if (observable.isMultiPolygon()) {
            //    coordinates = observable.getCoordinates().flat(2);
            //} else {
            //    return;
            //}
            //const lons = [];
            //const lats = [];
            //coordinates.forEach(ary => { lons.push(ary[0]); lats.push(ary[1]); });
            //LeafletLayer.map.flyToBounds([
            //    [Math.min.apply(null, lats), Math.min.apply(null, lons)],
            //    [Math.max.apply(null, lats), Math.max.apply(null, lons)]],
            //    {duration: .3});
            //if (!leafletLayer.isPopupOpen()) {
            //    leafletLayer.openPopup();
            //}
        }
    } else {
        const lons = [];
        const lats = [];
        observables.forEach(ob => {
            if (ob.isNode()) {
                const [lon, lat] = ob.getCoordinates();
                lons.push(lon);
                lats.push(lat);
            } else if (ob.isLine()) {
                const [[lon1, lat1], [lon2, lat2]] = ob.getCoordinates();
                lons.push(...[lon1, lon2]);
                lats.push(...[lat1, lat2]);
            }
        });
        LeafletLayer.map.flyToBounds([
            [Math.min.apply(null, lats), Math.min.apply(null, lons)],
            [Math.max.apply(null, lats), Math.max.apply(null, lons)],
            19,
            {duration: .3}
        ]);
    }
}