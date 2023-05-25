export { FeatureEditModal, getCirclePlusSvg, getTrashCanSvg, zoom };
import { Feature, UnsupportedOperationError } from './feature.js';
import { Modal } from './modal.js';
import { FeatureController } from './featureController.js';
import { LeafletLayer } from './leafletLayer.js';

class FeatureEditModal { // implements ObserverInterface, ModalInterface
    #controller;    // - ControllerInterface instance
    #keyToRow;      // - A map of property keys to table rows
    #modal;         // - A single Modal instance
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
        this.#keyToRow = {};
        this.#modal = null;
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
                this.renderContent();
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
        //this.refreshContent();
        this.renderContent();
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
        //this.refreshContent();
        this.renderContent();
    }

    // ****************************
    // ** ModalInterface methods **
    // ****************************

    getDOMElement() {
        return this.#modal.divElement;
    }

    /**
     * @returns {boolean}
     */
    isRemoved() {
        return this.#removed;
    }


    // - Here's how refreshing content could work:
    //  - The FeatureEditModal maintains an internal map of property keys to table rows (<tr> elements)
    //  - A property is deleted from an object
    //      - Currently, the entire table just re-renders
    //      - Now, the FeatureEditModal will look-up the property in its internal map. If the property exists, then remove the row from the table and
    //        remove the key from the map. If the property was only deleted from one object, but other objects still have the property, then replace
    //        the value text input after scanning all of the existing objects for that property value. If none of the other objects have the property,
    //        then delete the row on the multi-feature table.
    //  - A property is added to an object
    //      - Currently, the entire table just re-renders
    //      - Now, the FeatureEditModal will look-up the property in its internal map. If the property doesn't exist, then insert a new row into the
    //        table and insert the new key into the map. Note that the table that the user was editing will already have the new property inserted
    //        into the map and the new row inserted into the table as soon as the "change" event fires. Other tables that are observing the same
    //        feature won't have the property in their internal map, so they'll have the property added and the new row added when
    //        handleUpdatedProperty() fires. Checking for the existence of the property in the internal map is the key to not adding the same row
    //        twice to the same table. If the property was only added to one object, whether to add a new row to a multi-feature table or just update
    //        the value text input depends on the results of scanning the other objects for the same property
    //  - A property is changed on an object
    //      - Currently, the entire table just re-renders
    //      - Now, the FeatureEditModal won't have to do anything for a single object. The value text input will already reflect the current state of
    //        the object. Actually no, what about other FeatureEditModals that have the old value of the property in their value text input? I'll have
    //        to replace the old value text input with a new value text input, even in the FeatureEditModal that was changed. This is because the
    //        "original value" of the input, which is stored in the event handler, needs to be set to the new value, and the easiest way to do that is
    //        to just get a new value text input. In the case of multiple objects, I'll have to scan all of them and get a new value text input.

    /**
     * - Refresh aspects of the modal so that I don't have to re-render the whole thing
     * @returns {undefined}
     */
    refreshContent() {

    }

    /**
     * @returns {undefined}
     */
    remove() {
        if (!this.#removed) {
            this.#observables.forEach(ob => ob.removeObserver(this));
            this.#observables = null;
            this.#modal.divElement.remove();
            this.#removed = true;
        }
    }

    /**
     * - Render the modal for the first time
     * @returns {undefined}
     */
    renderContent() {
        const modal = new Modal();
        modal.addStyleClasses(['featureEditModal'], 'divElement');
        // - I don't create a value text input, so I have to decide whether to display an ID or a string here
        if (this.#observables.length === 1) {
            if (this.#observables[0].hasProperty('treeKey', 'meta')) {
                modal.insertTHeadRow([null, 'ID', this.#observables[0].getProperty('treeKey', 'meta')]);
            } else if (this.#observables[0].hasProperty('FID', 'meta')) {
                modal.insertTHeadRow([null, 'FID', this.#observables[0].getProperty('FID', 'meta').toString()]);
            } else {
                modal.insertTHeadRow([null, 'ID', '<No ID>']);
            }
        } else {
            modal.insertTHeadRow([null, 'ID', '<Multiple "ID" Values>']);
        }
        const keyToValues = {};
        this.#observables.forEach(ob => {
            // - Let non-OMD-tree features display a table
            if (ob.hasProperty('treeProps', 'meta')) {
                for (const [k, v] of Object.entries(ob.getProperties('treeProps'))) {
                    if (!keyToValues.hasOwnProperty(k)) {
                        keyToValues[k] = [v];
                    } else if (!keyToValues[k].includes(v)) {
                        keyToValues[k].push(v);
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
                if (!keyToValues.hasOwnProperty(k)) {
                    keyToValues[k] = [v];
                } else if (!keyToValues[k].includes(v)) {
                    keyToValues[k].push(v);
                }
            });
        });
        for (const [k, ary] of Object.entries(keyToValues)) {
            // - I don't create a value text input, so I have to decide whether to display the value of "object" or a string here 
            if (k === 'object') {
                if (ary.length === 1) {
                    modal.insertTHeadRow([null, 'Object', ary[0]])
                } else {
                    modal.insertTHeadRow([null, 'Object', '<Multiple "Object" Values>']);
                }
                continue;
            }
            // - Don't allow the "from", "to", or "type" properties of parent-child lines to be edited
            if (['from', 'to', 'type'].includes(k) && this.#observables.some(ob => ob.isParentChildLine())) {
                continue
            } else if (['latitude', 'longitude'].includes(k)) {
                if (this.#observables.some(ob => ob.isConfigurationObject() || ob.isLine())) {
                    continue;
                } else {
                    modal.insertTBodyRow([null, k, this.#getValueTextInput(k, keyToValues[k])], 'prepend');
                }
            } else {
                let deleteButton = null;
                if (!FeatureEditModal.#nonDeletableProperties.includes(k)) {
                    deleteButton = this.#getDeletePropertyButton(k);
                }
                modal.insertTBodyRow([deleteButton, k, this.#getValueTextInput(k, keyToValues[k])]);
            }
        }
        modal.insertTBodyRow([this.#getAddPropertyButton(), null, null], 'append', ['absolute']);
        modal.addStyleClasses(['centeredTable'], 'tableElement');
        // - Add buttons for regular features
        if (!this.#observables.some(ob => ob.isComponentFeature())) {
            modal.insertElement(this.#getDeleteFeatureDiv());
            if (!this.#observables.some(ob => ob.isConfigurationObject())) {
                modal.insertElement(this.#getZoomDiv(), 'prepend');
            }
        // - Add buttons for components
        } else {
            if (this.#observables.every(ob => ob.isConfigurationObject())) {
                modal.insertElement(this.#getAddConfigurationObjectDiv());
            } else if (this.#observables.some(ob => ob.isConfigurationObject())) {
                // - Don't add buttons. Configuration objects cannot be added because not every observable is a configuration object.
                //   Non-configuration objects cannot be added because there is at least one configuration object. The user should refine their search
                //   results, but mixing configuration and non-configuration objects isn't necessarily an error
            } else {
                if (this.#observables.every(ob => ob.isNode())) {
                    modal.insertElement(this.#getAddNodeWithCoordinatesDiv());
                    modal.insertElement(this.#getAddNodeWithMapClickDiv()); 
                } else if (this.#observables.every(ob => ob.isLine())) {
                    modal.insertElement(this.#getAddLineWithFromToDiv()); 
                } else {
                    // - Don't add buttons. The user's search returned both nodes and lines
                }
            }
        }
        modal.addStyleClasses(['verticalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex'], 'containerElement');
        if (this.#modal === null) {
            this.#modal = modal;
        } 
        if (document.body.contains(this.#modal.divElement)) {
            this.#modal.divElement.replaceWith(modal.divElement);
            this.#modal = modal;
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
     * @returns {HTMLDivElement}
     */
    #getAddConfigurationObjectDiv() {
        const btn = this.#getWideButton();
        btn.classList.add('add');
        btn.appendChild(getCirclePlusSvg());
        const span = document.createElement('span');
        span.textContent = 'Add Config Object';
        btn.appendChild(span);
        btn.addEventListener('click', () => {
            if (this.#componentsStateIsValid()) {
                this.#controller.addObservables(this.#observables.map(ob => this.#getObservableFromComponent(ob)));
            }
        });
        const div = this.#getWideButtonDiv();
        div.appendChild(btn);
        return div;
    }

    /**
     * - Add a line to the map by inputing "from" and "to" values and then clicking this button
     * @returns {HTMLDivElement}
     */
    #getAddLineWithFromToDiv() {
        const btn = this.#getWideButton();
        btn.classList.add('add');
        btn.appendChild(getCirclePlusSvg());
        const span = document.createElement('span');
        span.textContent = 'Add Line with from/to';
        btn.appendChild(span);
        btn.addEventListener('click', () => {
            if (this.#componentsStateIsValid()) {
                this.#controller.addObservables(this.#observables.map(ob => this.#getObservableFromComponent(ob)));
            }
        });
        const div = this.#getWideButtonDiv();
        div.appendChild(btn);
        return div;
    }

    /**
     * - Add a node to the map by inputing coordinates and then clicking this button
     * @returns {HTMLDivElement}
     */
    #getAddNodeWithCoordinatesDiv() {
        const btn = this.#getWideButton();
        btn.classList.add('add');
        btn.appendChild(getCirclePlusSvg());
        const span = document.createElement('span');
        span.textContent = 'Add with Coordinates';
        btn.appendChild(span);
        btn.addEventListener('click', () => {
            if (this.#componentsStateIsValid()) {
                this.#controller.addObservables(this.#observables.map(ob => this.#getObservableFromComponent(ob)));
            }
        });
        const div = this.#getWideButtonDiv();
        div.appendChild(btn);
        return div;
    }

    /**
     * - Add a node to the map by clicking on the map
     * @returns {HTMLDivElement}
     */
    #getAddNodeWithMapClickDiv() {
        const btn = this.#getWideButton();
        btn.classList.add('add');
        btn.appendChild(getCirclePlusSvg());
        const span = document.createElement('span');
        span.textContent = 'Add with Map Click';
        btn.appendChild(span);
        const that = this;
        btn.addEventListener('click', () => {
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
        const div = this.#getWideButtonDiv();
        div.appendChild(btn);
        return div;
    }
    
    /**
     * @returns {HTMLButtonElement}
     */
    #getAddPropertyButton() {
        const btn = document.createElement('button');
        btn.classList.add('add');
        btn.classList.add('horizontalFlex');
        btn.classList.add('centerMainAxisFlex');
        btn.classList.add('centerCrossAxisFlex');
        btn.appendChild(getCirclePlusSvg());
        const that = this;
        btn.addEventListener('click', function() {
            const deletePlaceholder = document.createElement('span');
            const keyInputPlaceholder = document.createElement('span');
            const valueInputPlaceholder = document.createElement('span');
            that.#modal.insertTBodyRow([deletePlaceholder, keyInputPlaceholder, valueInputPlaceholder], 'beforeEnd');
            that.#insertKeyTextInput(deletePlaceholder, keyInputPlaceholder, valueInputPlaceholder);
        });
        return btn;
    }

    /**
     * @returns {HTMLDivElement}
     */
    #getDeleteFeatureDiv() {
        const btn = this.#getWideButton();
        btn.classList.add('delete');
        btn.appendChild(getTrashCanSvg());
        const span = document.createElement('span');
        span.textContent = 'Delete';
        btn.appendChild(span);
        btn.addEventListener('click', () => {
            this.#controller.deleteObservables(this.#observables);    
        });
        const div = this.#getWideButtonDiv();
        div.appendChild(btn);
        return div;
    }
    
    /**
     * @param {string} propertyKey
     * @returns {HTMLButtonElement} a button that can be clicked on to remove a property from an ObservableInterface instance
     */
    #getDeletePropertyButton(propertyKey) {
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be a string.');
        }
        const btn = document.createElement('button');
        btn.classList.add('delete');
        btn.classList.add('horizontalFlex');
        btn.classList.add('centerMainAxisFlex');
        btn.classList.add('centerCrossAxisFlex');
        btn.appendChild(getTrashCanSvg());
        const that = this;
        btn.addEventListener('click', function(e) {
            that.#controller.deleteProperty(that.#observables, propertyKey);
            //let parentElement = this.parentElement;
            //while (!(parentElement instanceof HTMLTableRowElement)) {
            //    parentElement = parentElement.parentElement;
            //}
            //parentElement.remove();
            e.stopPropagation();
        });
        return btn;
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
            throw TypeError('"propertyKey" argument must be a string.');
        }
        if (!(propertyValues instanceof Array) && propertyValues !== null) {
            throw TypeError('"propertyValues" argument must be an array or null.');
        }
        const input = document.createElement('input');
        if (propertyValues === null) {
            //- Do nothing. A new property was just added so the value text input should be blank
        } else if (propertyValues.length === 1) {
            // - This works even if propertyValues = [""], which it can be sometimes
            input.value = propertyValues[0];
        } else {
            input.value = `<Multiple "${propertyKey}" Values>`;
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
     * @returns {HTMLDivElement}
     */
    #getZoomDiv() {
        const btn = this.#getWideButton();
        btn.appendChild(getPinSvg());
        const span = document.createElement('span');
        span.textContent = 'Zoom';
        btn.appendChild(span);
        btn.addEventListener('click', zoom.bind(null, this.#observables));
        const div = this.#getWideButtonDiv();
        div.appendChild(btn);
        return div;
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
                that.#controller.setProperty(that.#observables, inputValue, '', 'treeProps');
                this.replaceWith(document.createTextNode(inputValue));
                transitionalDeleteButton.replaceWith(that.#getDeletePropertyButton(inputValue));
                valueInputPlaceholder.replaceWith(that.#getValueTextInput(inputValue));
                originalValue = inputValue;
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
     * @param {string} propertyKey
     * @param {string} inputValue
     * @returns {boolean}
     */
    #toFromParentObjectIsValid(propertyKey, inputValue) {
        let observableKey;
        try {
            if(this.#observables.some(ob => ob.isComponentFeature())) {
                // - Components and non-components will never be together in an array of observables
                observableKey = this.#controller.observableGraph.getKeyForComponent(inputValue);
            } else {
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
                if (isNaN(+inputValue)) {
                    alert(`The value "${inputValue}" is not a valid number. A value for the "${propertyKey}" property must be a valid number.`);
                    return false;
                }
                return true;
            default:
                return true;
        }
    }
}

function getCirclePlusSvg() {
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('width', '28px');
    svg.setAttribute('height', '28px');
    svg.setAttribute('viewBox', '0 0 24 24'); 
    svg.setAttribute('fill', 'none'); 
    let path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M9 12H15');
    path.setAttribute('stroke', '#FFFFFF');
    path.setAttribute('stroke-width', '2');
    path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('stroke-linejoin', 'round');
    svg.appendChild(path);
    path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M12 9L12 15');
    path.setAttribute('stroke', '#FFFFFF');
    path.setAttribute('stroke-width', '2');
    path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('stroke-linejoin', 'round');
    svg.appendChild(path);
    path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z');
    path.setAttribute('stroke', '#FFFFFF');
    path.setAttribute('stroke-width', '2');
    svg.appendChild(path);
    return svg;
}

function getTrashCanSvg() {
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('width', '28px');
    svg.setAttribute('height', '28px');
    svg.setAttribute('viewBox', '0 0 24 24'); 
    svg.setAttribute('fill', 'none'); 
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M10 10V16M14 10V16M4 6H20M15 6V5C15 3.89543 14.1046 3 13 3H11C9.89543 3 9 3.89543 9 5V6M18 6V14M18 18C18 19.1046 17.1046 20 16 20H8C6.89543 20 6 19.1046 6 18V13M6 9V6');
    path.setAttribute('stroke', '#FFFFFF');
    path.setAttribute('stroke-width', '1.5');
    path.setAttribute('stroke-width', '1.5');
    path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('stroke-linejoin', 'round');
    svg.appendChild(path);
    return svg;
}

function getPinSvg() {
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('width', '28px');
    svg.setAttribute('height', '28px');
    svg.setAttribute('viewBox', '0 0 24 24'); 
    svg.setAttribute('fill', 'none'); 
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', '12');
    circle.setAttribute('cy', '10');
    circle.setAttribute('r', '3');
    circle.setAttribute('stroke', '#FFFFFF');
    circle.setAttribute('stroke-width', '1.5');
    circle.setAttribute('stroke-width', '1.5');
    circle.setAttribute('stroke-linecap', 'round');
    circle.setAttribute('stroke-linejoin', 'round');
    svg.appendChild(circle);
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', "M19 9.75C19 15.375 12 21 12 21C12 21 5 15.375 5 9.75C5 6.02208 8.13401 3 12 3C15.866 3 19 6.02208 19 9.75Z");
    path.setAttribute('stroke', '#FFFFFF');
    path.setAttribute('stroke-width', '1.5');
    path.setAttribute('stroke-width', '1.5');
    path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('stroke-linejoin', 'round');
    svg.appendChild(path);
    return svg;
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
        const layer = Object.values(observable.getObservers().filter(ob => ob instanceof LeafletLayer)[0].getLayer()._layers)[0];
        if (observable.isNode()) {
            const [lon, lat] = structuredClone(observable.getCoordinates());
            // - This is the max zoom without losing the map
            LeafletLayer.map.flyTo([lat, lon], 19, {duration: .3});
            if (!layer.isPopupOpen()) {
                layer.openPopup();
            }
        } else if (observable.isLine()) {
            const [[lon1, lat1], [lon2, lat2]] = observable.getCoordinates();
            LeafletLayer.map.flyToBounds([[lat1, lon1], [lat2, lon2]], {duration: .3});
            if (!layer.isPopupOpen()) {
                layer.openPopup();
            }
        } else {
            let coordinates;
            if (observable.isPolygon()) {
                coordinates = observable.getCoordinates().flat(1);
            } else if (observable.isMultiPolygon()) {
                coordinates = observable.getCoordinates().flat(2);
            } else {
                return;
            }
            const lons = [];
            const lats = [];
            coordinates.forEach(ary => { lons.push(ary[0]); lats.push(ary[1]); });
            LeafletLayer.map.flyToBounds([
                [Math.min.apply(null, lats), Math.min.apply(null, lons)],
                [Math.max.apply(null, lats), Math.max.apply(null, lons)]],
                {duration: .3});
            if (!layer.isPopupOpen()) {
                layer.openPopup();
            }
        }
    } else {
        const lons = [];
        const lats = [];
        observables.forEach(ob => {
            if (ob.isNode()) {
                const [lon, lat] = structuredClone(ob.getCoordinates());
                lons.push(lon);
                lats.push(lat);
            } else if (ob.isLine()) {
                const [[lon1, lat1], [lon2, lat2]] = structuredClone(ob.getCoordinates());
                lons.push(...[lon1, lon2]);
                lats.push(...[lat1, lat2]);
            }
        });
        LeafletLayer.map.flyToBounds([
            [Math.min.apply(null, lons), Math.min.apply(null, lats)],
            [Math.max.apply(null, lons), Math.max.apply(null, lats)],
        ]);
    }
}