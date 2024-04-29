export { TestModal };
    import { FeatureController } from '../featureController.js';
    import { Modal } from '../modal.js';

class TestModal {
    #controller;    // - ControllerInterface instance
    #modal;         // - A single Modal instance
    #observables;   // - An array of ObservableInterface instances

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
        this.#modal = null;
        this.#observables = observables;
        this.renderContent();
    }

    /**
     * - A render a static, read-only table for arbitrary GeoJSON objects. Does not support editing data in any way. See featureEditModal.js for
     *   examples of how to edit data in a table
     */
    renderContent() {
        const modal = new Modal();
        modal.addStyleClasses(['featureEditModal'], 'divElement');
        let count = 0;
        for (const [key, val] of Object.entries(this.#observables[0].getProperties('meta'))) {
            const keySpan = document.createElement('span');
            keySpan.textContent = key;
            keySpan.dataset.propertyKey = key;
            keySpan.dataset.propertyNamespace = 'meta';
            const valueSpan = document.createElement('span');

            // check for fema secific columns    
        
            if(keySpan.textContent === 'TRACT'){
                keySpan.textContent = 'Census Tract';
                keySpan.dataset.propertyKey = 'tract';
                keySpan.dataset.propertyNamespace = 'treeProps';

                modal.insertTHeadRow([null, 'Census Tract', val.toString()], 'prepend');
                continue;
            }
            if (keySpan.textContent === 'SOVI_SCORE') {
                keySpan.textContent = 'Social Vulnerability Score'
            }
            if (keySpan.textContent === 'SOVI_RATNG') {
                keySpan.textContent = 'Social Vulnerability Rating'
            }
            valueSpan.textContent = val;
            modal.insertTBodyRow([null, keySpan, valueSpan]);
        }
        modal.addStyleClasses(['centeredTable', 'plainTable'], 'tableElement');
        


        // - Add buttons for regular features
            if (!this.#observables.some(ob => ob.isConfigurationObject())) {
                modal.insertElement(this.#getZoomDiv(), 'prepend'); 
            }



        modal.addStyleClasses(['verticalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex'], 'containerElement');
        if (this.#modal === null){
            this.#modal = modal;
        }
        if (document.body.contains(this.#modal.divElement)) {
            this.#modal.divElement.replaceWith(modal.divElement);
            this.#modal = modal;
        }
        // - Example of how to get to underlying data
        
    }


    // ****************************
    // ** ModalInterface methods **
    // ****************************

    getDOMElement() {
        return this.#modal.divElement;
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
     * @returns {HTMLDivElement}
     */
    #getZoomDiv(){
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
}

function getPinSvg() {
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('width', '22px');
    svg.setAttribute('height', '22px');
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
            // - The max zoom level without losing the map is 19
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
