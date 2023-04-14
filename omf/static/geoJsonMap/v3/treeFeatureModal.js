export { TreeFeatureModal, getCirclePlusSvg, getTrashCanSvg };
import { Modal } from './modal.js';
import { FeatureController } from './featureController.js';
import { LeafletLayer } from './leafletLayer.js';

class TreeFeatureModal { // implements ObserverInterface
    #controller;    // - ControllerInterface instance
    #modal;         // - A single Modal instance
    #observables;   // - An array of ObservableInterface instances
    #removed;       // - Whether this TreeFeatureModal instance has already been deleted
    static #nonDeletableProperties = ['name', 'object', 'from', 'to', 'parent', 'latitude', 'longitude', 'treeKey'];
    
    /**
     * @param {FeatureController} controller - a ControllerInterface instance
     * @returns {undefined}
     */
    constructor(controller) {
        if (!(controller instanceof FeatureController)) {
            throw Error('"controller" argument must be an instance of FeatureController');
        }
        this.#controller = controller;
        this.#modal = null;
        this.#observables = null;
        this.#removed = false;
        this.renderContent();
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
            if (this.#observables.length === 0) {
                this.remove();
            } else {
                this.renderContent();
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
        this.renderContent();
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
        this.renderContent();
    }

    // *********************
    // ** Public methods ** 
    // *********************

    getDOMElement() {
        return this.#modal.divElement;
    }

    remove() {
        // - Do not deregister this.#controller from the same observables. It's possible that the controller is managing multiple views 
        //  - The controller has its own remove() method that can be called
        if (!this.#removed) {
            this.#observables.forEach(ob => ob.removeObserver(this));
            this.#observables = null;
            this.#modal.divElement.remove();
            this.#removed = true;
        }
    }

    /**
     * @returns {undefined}
     */
    renderContent() {
        if (this.#observables !== null) {
            this.#observables.forEach(ob => ob.removeObserver(this));
        }
        this.#observables = this.#controller.getObservables();
        this.#observables.forEach(ob => ob.registerObserver(this));
        const modal = new Modal();
        modal.addStyleClass('treeFeatureModal', 'divElement');
        //modal.setTitle('Edit Object');
        const treePropsMap = {};
        const coordinatesMap = {
            'longitudes': [],
            'latitudes': []
        };
        this.#observables.forEach(ob => {
            for (const [k, v] of Object.entries(ob.getProperties('treeProps'))) {
                if (!treePropsMap.hasOwnProperty(k)) {
                    treePropsMap[k] = [v];
                } else if (!treePropsMap[k].includes(v)) {
                    treePropsMap[k].push(v);
                }
            }
            const longitudes = [];
            const latitudes = [];
            if (ob.isNode()) {
                const [lon, lat] = ob.getCoordinates();
                longitudes.push(+lon);
                latitudes.push(+lat);
            }
            if (ob.isLine()) {
                const [[lon_1, lat_1], [lon_2, lat_2]] = ob.getCoordinates();
                longitudes.push(+lon_1);
                longitudes.push(+lon_2);
                latitudes.push(+lat_1);
                latitudes.push(+lat_2);
            }
            for (const lon of longitudes) {
                if (!coordinatesMap.longitudes.includes(lon)) {
                    coordinatesMap.longitudes.push(lon);
                }
            }
            for (const lat of latitudes) {
                if (!coordinatesMap.latitudes.includes(lat)) {
                    coordinatesMap.latitudes.push(lat);
                }
            }
        });
        if (this.#observables.length === 1) {
            modal.insertTHeadRow([null, 'ID', this.#observables[0].getProperty('treeKey', 'meta')]);
        } else {
            modal.insertTHeadRow([null, 'ID', '<Multiple "ID" Values>']);
        }
        for (const [k, ary] of Object.entries(treePropsMap)) {
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
            }
            let deleteButton = null;
            // - Components should allow properties to be deleted
            //  - There will be a "Reset Component" button in the modal that will restore all of the Component's default values
            if (!TreeFeatureModal.#nonDeletableProperties.includes(k)) {
                deleteButton = this.#getDeletePropertyButton(k);
            }
            modal.insertTBodyRow([deleteButton, k, this.#createValueTextInput(k, treePropsMap[k])]);
        }
        if (!this.#controller.hasConfigurationObjects() && !this.#controller.hasLines()) {
            modal.insertTBodyRow([null, 'longitude', this.#createValueTextInput('longitude', coordinatesMap.longitudes)], 'prepend');
            modal.insertTBodyRow([null, 'latitude', this.#createValueTextInput('latitude', coordinatesMap.latitudes)], 'prepend');
        }
        modal.insertTBodyRow([this.#getAddPropertyButton(), null, null]);
        // - Add buttons for regular features
        if (!this.#controller.hasComponents()) {
            if (!this.#controller.hasConfigurationObjects()) {
                modal.insertElement(this.#getZoomButton());
            }
            modal.insertElement(this.#getDeleteFeatureButton())
        // - Add buttons for components
        } else {
            if (this.#controller.hasConfigurationObjects()) {
                if (this.#controller.hasNodes() || this.#controller.hasLines()) {
                    throw Error('"A FeatureController that is a component manager should not control both configuration objects and non-configuration objects');
                }
                modal.insertElement(this.#getAddConfigurationObjectButton());
            } else {
                if (this.#controller.hasNodes() && this.#controller.hasLines()) {
                    throw Error('"A FeatureController that is a component manager should not control both nodes and lines');
                }
                if (this.#controller.hasNodes()) {
                    modal.insertElement(this.#getAddNodeWithCoordinatesButton());
                    modal.insertElement(this.#getAddNodeWithMapClickButton());
                } else if (this.#controller.hasLines()) {
                    modal.insertElement(this.#getAddLineWithFromToButton());
                }
            }
        }
        modal.addStyleClass('centeredTable',        'tableElement');
        modal.addStyleClass('verticalFlex',         'containerElement');
        modal.addStyleClass('centerMainAxisFlex',   'containerElement');
        modal.addStyleClass('centerCrossAxisFlex',  'containerElement');
        if (this.#modal === null) {
            this.#modal = modal;
        } else if (document.body.contains(this.#modal.divElement)) {
            this.#modal.divElement.replaceWith(modal.divElement);
            this.#modal = modal;
        } else {
            throw Error('Error when creating a TreeFeatureModal.');
        }
    }
    
    // *********************
    // ** Private methods ** 
    // *********************

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
        btn.appendChild(getTrashCanSvg());
        const that = this;
        btn.addEventListener('click', function(e) {
            that.#controller.deleteProperty(propertyKey, 'treeProps');
            let parentElement = this.parentElement;
            while (!(parentElement instanceof HTMLTableRowElement)) {
                parentElement = parentElement.parentElement;
            }
            parentElement.remove();
            e.stopPropagation();
        });
        return btn;
    }

    /**
     * - Is this function signature good?
     */
    #valueTextInputIsValid(propertyKey, inputValue) {
        // - I am no longer always converting to lowercase because names are case-sensitive and therefore other properties should be too
        switch (propertyKey) {
            case 'type':
                inputValue = inputValue.toLowerCase();
                if (inputValue === 'parentchild') {
                    alert('The "type" property may not have a value of "parentChild"');
                    return false;
                }
                return true;
            case 'treeKey':
                alert('The "treeKey" property cannot be changed');
                return false;
            case 'name':
                if (this.#observables.length > 1) {
                    alert('The "name" property cannot be edited for multiple objects simultaneously');
                    return false;
                } else {
                    if (inputValue.trim() === '') {
                        alert('The "name" property cannot be blank');
                        return false;
                    }
                    if (this.#controller.observableGraph.getObservables().some(ob => ob.hasProperty('name') && ob.getProperty('name') === inputValue)) {
                        alert(`The "name" property must be unique for all objects. The name "${inputValue}" is already used by another object.`);
                        return false;
                    }
                    return true;
                }
            case 'from':
            case 'to':
            case 'parent':
                let observableKey;
                try {
                    if (this.#controller.isComponentManager) {
                        // - Components aren't in the graph, so they have to use this method and if there are multiple objects with the given name
                        //   then the component gets whichever one is arbitrary first (for now)
                        observableKey = this.#controller.observableGraph.getKeyForComponent(inputValue);
                    } else {
                        // - It shouldn't matter which ObservableInterface instance is asking for the key, so just grab the first observable
                        observableKey = this.#controller.observableGraph.getKey(inputValue, this.#observables[0].getProperty('treeKey', 'meta'));
                    }
                } catch {
                    alert(`No object with the name "${inputValue}" exists for the property key "${propertyKey}".`);
                    return false;
                }
                if (observableKey.startsWith('parentChild:')) {
                    alert('Parent-child lines cannot be used as "from", "to", or "parent" values.');
                    return false;
                }
                const observable = this.#controller.observableGraph.getObservable(observableKey);
                if (observable.isConfigurationObject()) {
                    alert(`The object "${inputValue}" is a configuration object, so it cannot be used in "from", "to", or "parent" properties.`);
                    return false;
                }
                if (observable.isComponentFeature()) {
                    // - This should never happen because components aren't in the graph
                    alert(`The object "${inputValue}" is a component, so it cannot be used in "from", "to", or "parent" properties.`);
                    return false;
                }
                if (observable.isModalFeature()) {
                    alert(`The object "${inputValue}" is a modal feature, so it cannot be used in "from", "to", or "parent" properties.`);
                    return false;
                }
                return true;
            case 'latitude':
            case 'longitude':
                if (isNaN(+inputValue)) {
                    alert(`A value for "${propertyKey}" must be a valid number.`);
                    return false;
                }
                return true;
            default:
                return true;
        }
    }

    /**
     * - Return a text input that can be viewed in a modal
     * @param {string} propertyKey
     * @param {Array} propertyValues
     * @returns {HTMLButtonElement} a text input that can be edited on to change a property in an ObservableInterface instance
     */
    #createValueTextInput(propertyKey, propertyValues) {
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be a string.');
        }
        propertyValues = typeof propertyValues !== 'undefined' ? propertyValues : [];
        if (!(propertyValues instanceof Array)) {
            throw TypeError('"propertyKey" argument must be a string.');
        }
        const input = document.createElement('input');
        if (propertyValues.length === 0) {
            // - Do nothing
        } else if (propertyValues.length === 1) {
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
                            that.#controller.setIDs([ob.getProperty('treeKey', 'meta')]);
                            if (propertyKey === 'latitude') {
                                that.#controller.setCoordinates([lon, inputValue]);
                            } else {
                                that.#controller.setCoordinates([inputValue, lat]);
                            }
                            that.#controller.setIDs(that.#observables.map(ob => ob.getProperty('treeKey', 'meta')));
                        } else if (ob.isLine()) {
                            const [[lon, lat], [lon_1, lat_1]] = ob.getCoordinates(); 
                            that.#controller.setIDs([ob.getProperty('treeKey', 'meta')]);
                            if (propertyKey === 'latitude') {
                                that.#controller.setCoordinates([[lon, inputValue], [lon_1, inputValue]]);
                            } else {
                                that.#controller.setCoordinates([[inputValue, lat], [inputValue, lat_1]]);
                            }
                            that.#controller.setIDs(that.#observables.map(ob => ob.getProperty('treeKey', 'meta')));
                        }
                    } else if (['from', 'to', 'parent'].includes(propertyKey)) {
                        // - If I'm mass editing nodes and lines together, I don't want to try and set the "from" property on nodes or the
                        //   "parent" property on lines
                        if (ob.hasProperty(propertyKey)) {
                            that.#controller.setProperty(propertyKey, inputValue);
                        }
                    } else {
                        that.#controller.setProperty(propertyKey, inputValue);
                    }
                });
                originalValue = inputValue;
            } else {
                this.value = originalValue;
            }
        });
        return input
    }

    /**
     * TODO: use tooltips instead of alerts
     */
    #keyTextInputIsValid(inputValue) {
        // - I am no longer always converting to lowercase because names are case-sensitive and therefore other properties should be too
        if (TreeFeatureModal.#nonDeletableProperties.includes(inputValue)) {
            alert(`The following properties cannot be added to objects: ${TreeFeatureModal.#nonDeletableProperties}.`);
            return false;
        } else if (inputValue === '') {
            return false;
        } else if (this.#controller.hasProperty(inputValue, 'treeProps')) {
            if (this.#observables.length === 1) {
                alert(`The property "${inputValue}" could not be added because this object already has this property.`);
            } else {
                alert(`The property "${inputValue}" could not be added because one or more objects already has the property.`);
            }
            return false;
        }
        return true;
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
                that.#controller.setProperty(inputValue, '', 'treeProps');
                this.replaceWith(document.createTextNode(inputValue));
                transitionalDeleteButton.replaceWith(that.#getDeletePropertyButton(inputValue));
                valueInputPlaceholder.replaceWith(that.#createValueTextInput(inputValue));
                originalValue = inputValue;
            } else {
                input.value = originalValue;
            }
        });
    }

    /**
     * @returns {HTMLButtonElement}
     */
    #getAddPropertyButton() {
        const btn = document.createElement('button');
        btn.classList.add('add');
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
     * 
     */
    #getDeleteFeatureButton() {
        const btn = this.#getWideButton();
        btn.classList.add('delete');
        btn.appendChild(getTrashCanSvg());
        const span = document.createElement('span');
        span.textContent = 'Delete';
        btn.appendChild(span);
        btn.addEventListener('click', () => {
            this.#controller.deleteObservables();    
        });
        const div = this.#getWideButtonDiv();
        div.appendChild(btn);
        return div;
    }

    /**
     * 
     */
    #getZoomButton() {
        const btn = this.#getWideButton();
        btn.appendChild(getPinSvg());
        const span = document.createElement('span');
        span.textContent = 'Zoom';
        btn.appendChild(span);
        btn.addEventListener('click', () => {
            if (this.#observables.length === 1) {
                const observable = this.#observables[0];
                const layer = Object.values(observable.getObservers().filter(ob => ob instanceof LeafletLayer)[0].layer._layers)[0];
                if (observable.isNode()) {
                    const [lon, lat] = observable.getCoordinates();
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
                }
            } else {
                // - TODO: zoom for multiple features
            }
        });
        const div = this.#getWideButtonDiv();
        div.appendChild(btn);
        return div;
    }

    /**
     * 
     */
    #componentStateIsValid() {
        if (this.#observables.length === 1) {
            const observable = this.#observables[0];
            if (observable.hasProperty('name')) {
                if (!this.#valueTextInputIsValid('name', observable.getProperty('name'))) {
                    return false;
                }
            }
            if (observable.isChild()) {
                if (!this.#valueTextInputIsValid('parent', observable.getProperty('parent'))) {
                    return false;
                }
            }
            if (observable.isLine()) {
                if (!this.#valueTextInputIsValid('from', observable.getProperty('from'))) {
                    return false;
                }
                if (!this.#valueTextInputIsValid('to', observable.getProperty('to'))) {
                    return false;
                }
            }
            return true;
        } else {
            // - TODO;
        }
    }


    /**
     * - Add a configuration object to the data
     */
    #getAddConfigurationObjectButton() {
        const btn = this.#getWideButton();
        btn.classList.add('add');
        btn.appendChild(getCirclePlusSvg());
        const span = document.createElement('span');
        span.textContent = 'Add Config Object';
        btn.appendChild(span);
        btn.addEventListener('click', () => {
            if (this.#componentStateIsValid()) {
                this.#controller.addObservable();
            }
        });
        const div = this.#getWideButtonDiv();
        div.appendChild(btn);
        return div;
    }

    /**
     * - Add a node to the map by clicking on the map
     */
    #getAddNodeWithMapClickButton() {
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
                if (that.#componentStateIsValid()) {
                    that.#controller.addObservable([e.latlng.lat, e.latlng.lng]);
                }
            });
        });
        const div = this.#getWideButtonDiv();
        div.appendChild(btn);
        return div;
    }

    /**
     * - Add a node to the map by inputing coordinates and then clicking this button
     */
    #getAddNodeWithCoordinatesButton() {
        const btn = this.#getWideButton();
        btn.classList.add('add');
        btn.appendChild(getCirclePlusSvg());
        const span = document.createElement('span');
        span.textContent = 'Add with Coordinates';
        btn.appendChild(span);
        btn.addEventListener('click', () => {
            if (this.#componentStateIsValid()) {
                this.#controller.addObservable();
            }
        });
        const div = this.#getWideButtonDiv();
        div.appendChild(btn);
        return div;
    }

    /**
     * - Add a line to the map by inputing "from" and "to" values and then clicking this button
     */
    #getAddLineWithFromToButton() {
        const btn = this.#getWideButton();
        btn.classList.add('add');
        btn.appendChild(getCirclePlusSvg());
        const span = document.createElement('span');
        span.textContent = 'Add Line with from/to';
        btn.appendChild(span);
        btn.addEventListener('click', () => {
            if (this.#componentStateIsValid()) {
                this.#controller.addObservable();
            }
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

function getCirclePlusSvg() {
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('width', '32px');
    svg.setAttribute('height', '32px');
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
    svg.setAttribute('width', '32px');
    svg.setAttribute('height', '32px');
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
    svg.setAttribute('width', '32px');
    svg.setAttribute('height', '32px');
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