export { Feature, UnsupportedOperationError, ObserverError };
import { FeatureGraph } from './featureGraph.js';

class Feature {
    #feature;
    #graph;
    #observers;
    #originalFeature;

    /**
     * @param {Object} feature - a standard GeoJSON feature
     * @param {FeatureGraph} graph - an already-constructed graph that is used to optimize observable-observer notifications
     * @returns {undefined}
     */
    constructor(feature) {
        this.#feature = feature;
        this.#graph = null
        this.#observers = [];
        this.#originalFeature = structuredClone(feature);
    }
    
    // *********************************
    // ** ObservableInterface methods **
    // *********************************

    /**
     * - Delete the property with the matching namespace and property key in this ObservableInstance (i.e. "this") if it exists, otherwise throw a
     *   ReferenceError
     * @param {string} propertyKey - the property key of the property that is in the observable
     * @param {string} [namespace='treeProps'] - the namespace of the property that is in the observable 
     *  - E.g. for Feature instances, this defaults to "treeProps" which corresponds to properties in the "treeProps" object
     * @returns {undefined}
     */
    deleteProperty(propertyKey, namespace='treeProps') {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be a string.');
        }
        if (typeof namespace !== 'string') {
            throw TypeError('"namespace" argument must be a string.');
        }
        if (['treeProps', 'formProps', 'urlProps'].includes(namespace)) {
            if (this.#feature.properties.hasOwnProperty(namespace)) {
                if (this.#feature.properties[namespace].hasOwnProperty(propertyKey)) {
                    const oldPropertyValue = this.getProperty(propertyKey, namespace);
                    delete this.#feature.properties[namespace][propertyKey];
                    this.updatePropertyOfObservers(propertyKey, oldPropertyValue, namespace);
                } else {
                    throw ReferenceError(`The property "${propertyKey}" could not be found in the namespace "${namespace}" in the Feature instance "${this.getProperty('treeKey', 'meta')}."`);
                }
            } else {
                throw ReferenceError(`This feature does not have the namespace "${namespace}".`);
            }
        } else if (namespace === 'meta') {
            if (this.#feature.properties.hasOwnProperty(propertyKey)) {
                const oldPropertyValue = this.getProperty(propertyKey, namespace);
                delete this.#feature.properties[propertyKey];
                this.updatePropertyOfObservers(propertyKey, oldPropertyValue, namespace);
            } else {
                throw ReferenceError(`The property "${propertyKey}" could not be found in the namespace "${namespace}" in the Feature instance "${this.getProperty('treeKey', 'meta')}."`);
            }
        } else {
            throw ReferenceError(`The namespace "${namespace}" does not exist in this Feature. Leave the "namespace" argument empty to use the "treeProps" namespace.`);
        }
    }

    /**
     * - Mark this ObservableInterface instance as being no longer observable to any observers (i.e. "delete" it)
     *  - Make all of its observers ignore it
     *  - Remove it from the ObservableGraph interface instance
     * @returns {undefined}
     */
    deleteObservable() {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        // - I need to clone the array because if I iterate over this.#observers while I'm removing elements from it, everything gets messed up
        const observers = [...this.#observers];
        observers.forEach(ob => {
            ob.handleDeletedObservable(this);
        });
        if (this.#graph instanceof FeatureGraph) {
            this.#graph.handleDeletedObservable(this);
        }
    }

    /**
     * @returns {Array} the coordinates of the ObservableInterface instance in [<lon>, <lat>] format
     *  - E.g. [<lon>, <lat>] for points and [[<lon_1>, <lat_1>], [<lon_2>, <lat_2>]] for lines
     */
    getCoordinates() {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        return this.#feature.geometry.coordinates;
    }

    getObservable() {
        throw new UnsupportedOperationError();
    }

    /**
     * @returns {Object} a copy of the underlying data of this ObservableInterface instance
     *  - E.g. a vanilla JavaSCript GeoJSON feature object
     */
    getObservableExportData() {
        const clone = structuredClone(this.#feature);
        if (clone.properties.hasOwnProperty('treeProps')) {
            if (clone.properties.treeProps.hasOwnProperty('object')) {
                // - Recorders and players cannot have a "name" property when being saved, but they need to maintain that property in the interface
                if (['recorder', 'player'].includes(clone.properties.treeProps.object)) {
                    if (clone.properties.treeProps.hasOwnProperty('name')) {
                        const nameComponents = clone.properties.treeProps.name.split(':');
                        if (nameComponents.length === 3 && nameComponents[2] === 'addedName') {
                            delete clone.properties.treeProps.name;
                        }
                    }
                }
                // - !CMD objects have their "name" property moved to the "command" property in the interface so that they have unique names. The
                //   "name" property value must be set to the value of the "command" property on export
                if (clone.properties.treeProps.object === '!CMD') {
                    clone.properties.treeProps.name = clone.properties.treeProps.CMD_command;
                    delete clone.properties.treeProps.CMD_command;
                }
            }
        }
        return clone;
    }

    getObservables(func) {
        throw new UnsupportedOperationError();
    }

    /**
     * - Get the ObserverInterface instances that are observing this ObservableInterface instance
     *  - This is needed to get the LeafletMap for the Zoom button in the TreeFeatureModal class
     * @returns {Array}
     */
    getObservers() {
        return this.#observers;
    }

    /**
     * - Return the properties in the specified namespace in this ObservableInstance (i.e. "this") if it exists, otherwise throw a ReferenceError
     * @param {string} namespace - the namespace of some properties in this observable
     * @returns {Object}
     */
    getProperties(namespace) {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        if (typeof namespace !== 'string') {
            throw TypeError('"namespace" argument must be a string');
        }
        if (['treeProps', 'formProps', 'urlProps'].includes(namespace)) {
            if (this.#feature.properties.hasOwnProperty(namespace)) {
                // - I need to be consistent
                return this.#feature.properties[namespace];
            }
            throw ReferenceError(`This feature does not have the namespace "${namespace}".`);
        } else if (namespace === 'meta') {
            // - I need to be consistent
            return this.#feature.properties;
        }
        throw ReferenceError(`The namespace "${namespace}" does not exist in this Feature. Leave the "namespace" argument empty to get all properties.`);
    }

    /**
     * - Return the property value of the property with the matching namespace and property key in this ObservableInstance (i.e. "this") if it exists,
     *   otherwise throw a ReferenceError
     * @param {string} propertyKey - the property key of the property that is in the observable
     * @param {string} [namespace='treeProps'] - the namespace of the property that is in the observable 
     *  - E.g. for Feature instances, this defaults to "treeProps" which corresponds to properties in the "treeProps" object
     * @returns {(string|Object)} propertyValue 
     */
    getProperty(propertyKey, namespace='treeProps') {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be a string.');
        }
        if (typeof namespace !== 'string') {
            throw TypeError('"namespace" argument must be a string.');
        }
        if (['treeProps', 'formProps', 'urlProps'].includes(namespace)) {
            if (this.#feature.properties.hasOwnProperty(namespace)) {
                if (this.#feature.properties[namespace].hasOwnProperty(propertyKey)) {
                    // - At this point, I don't want to return a structuredClone becuase I use this method everywhere
                    return this.#feature.properties[namespace][propertyKey];
                }
                throw ReferenceError(`The property "${propertyKey}" could not be found in the namespace "${namespace}" in the Feature instance "${this.getProperty('treeKey', 'meta')}."`);
            }
            throw ReferenceError(`This feature does not have the namespace "${namespace}".`);
        } else if (namespace === 'meta') {
            if (this.#feature.properties.hasOwnProperty(propertyKey)) {
                // - I need to be consistent
                return this.#feature.properties[propertyKey];
            }
            throw ReferenceError(`The property "${propertyKey}" could not be found in the namespace "${namespace}" in the Feature instance "${this.getProperty('treeKey', 'meta')}."`);
        }
        throw ReferenceError(`The namespace "${namespace}" does not exist in this Feature. Leave the "namespace" argument empty to use the "treeProps" namespace.`);
    }

    /**
     * @returns {boolean} whether this ObservableInterface instance has coordinates
     */
    hasCoordinates() {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        if (this.#feature.geometry.type === 'Point') {
            return !this.#feature.geometry.coordinates.some(c => typeof c !== 'number');
        } else if (this.#feature.geometry.type === 'LineString') {
            return !this.#feature.geometry.coordinates[0].some(c => typeof c !== 'number') && !this.#feature.geometry.coordinates[1].some(c =>
                typeof c !== 'number');
        }
    }

    /**
     * @returns {boolean} whether this ObservableInterface instance has this.#graph set to some FeatureGraph
     */
    hasGraph() {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        return (this.#graph instanceof FeatureGraph);
    }

    /**
     * @param {string} propertyKey - the property key of the property that may or may not be in this observable's namespace 
     * @param {string} [namespace='treeProps'] - the namespace of the property key that may or may not be in this observable
     * @returns {boolean}
     */
    hasProperty(propertyKey, namespace='treeProps') {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be a string.');
        }
        if (typeof namespace !== 'string') {
            throw TypeError('"namespace" argument must be a string.');
        }
        if (['treeProps', 'formProps', 'urlProps'].includes(namespace)) {
            if (this.#feature.properties.hasOwnProperty(namespace)) {
                return this.#feature.properties[namespace].hasOwnProperty(propertyKey);
            }
            return false;
        } else if (namespace === 'meta') {
            return this.#feature.properties.hasOwnProperty(propertyKey);
        }
        throw ReferenceError(`The namespace "${namespace}" does not exist in this Feature. Leave the "namespace" argument empty to use the "treeProps" namespace.`);
    }

    /**
     * @returns {undefined}
     */
    notifyObserversOfNewObservable() {
        throw new UnsupportedOperationError();
    }

    /**
     * @param {Object} observer - an instance of ObserverInterface that wants to observer this ObservableInterface instance
     *  - E.g. this feature is a node and a LeafletLayer instance wants to observe it
     * @returns {undefined}
     */
    registerObserver(observer) {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        if (observer instanceof Feature) {
            throw new ObserverError();
        }
        this.#observers.push(observer);
    }

    /**
     * @param {Object} observer - an instance of ObserverInterface that no longer should observe this ObservableInterface instance
     *  - E.g. a TreeFeatureModal instance shouldn't observe this ObservableInterface instance anymore
     * @returns {undefined}
     */
    removeObserver(observer) {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        if (observer instanceof Feature) {
            throw new ObserverError();
        }
        const index = this.#observers.indexOf(observer);
        if (index > -1) {
            this.#observers.splice(index, 1);
        } else {
            // - Unfortunately, <Leaflet layer>.remove() also removes the FeatureEditModal in the pop-up from this.#observers for some reason before
            //   the FeatureEditModal is removed. I can't control the behavior of Leaflet, so I can't throw an error here
            //console.log('The observer was not found in this.#observers');
            //throw Error('The observer was not found in this.#observers');
        }
    }

    /**
     * @param {Array} coordinates - an array of coordinates for this ObservableInterface instance
     *  - E.g. for Feature instances this should be in [<lon>, <lat>] format
     * @returns {undefined}
     */
    setCoordinates(coordinates) {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        if (!(coordinates instanceof Array)) {
            throw TypeError('"coordinates" argument must be an array.');
        }
        // - Check that all coordinate values are valid numbers
        for (let i = 0; i < coordinates.length; i++) {
            if (coordinates[i] instanceof Array) {
                for (let j = 0; j < coordinates[i].length; j++) {
                    if (typeof coordinates[i][j] !== 'string' && typeof coordinates[i][j] !== 'number') {
                        throw TypeError(`"coordinates[${i}][${j}]" must be a number or valid number-string`);
                    }
                    coordinates[i][j] = +coordinates[i][j];
                    if (isNaN(coordinates[i][j])) {
                        throw TypeError(`"coordinates[${i}][${j}]" must be a number or valid number-string`);
                    }
                }
            } else {
                if (typeof coordinates[i] !== 'string' && typeof coordinates[i] !== 'number') {
                    throw TypeError(`"coordinates[${i}]" must be a number or valid number-string`);
                }
                coordinates[i] = +coordinates[i];
                if (isNaN(coordinates[i])) {
                    throw TypeError(`"coordinates[${i}]" must be a number or valid number-string`);
                }
            }
        }
        // - Check that the right number of coordinates were passed
        if (this.isNode()) {
            if (coordinates.length !== 2 || typeof coordinates[0] !== 'number' || typeof coordinates[1] !== 'number') {
                throw TypeError('"coordinates" argument must be an array of two numbers for node features');
            }
        }
        if (this.isLine()) {
            if (coordinates.length !== 2 || coordinates[0].length !== 2 || coordinates[1].length !== 2) {
                throw TypeError('"coordinates" argument must be an array of two arrays of two numbers for line features.');
            }
        }
        const oldCoordinates = this.getCoordinates();
        this.#feature.geometry.coordinates = coordinates;
        this.updateCoordinatesOfObservers(oldCoordinates);
    }

    /**
     * - Set the "graph" property of this Feature instance to optimize communication between Feature observables and Feature observers. All
     *   non-component Feature instances are part of the same graph. I can use a graph because all Features have a unique ID, but the overall Observer
     *   Pattern doesn't assume that Observables have unique IDs or that a graph exists at all
     * - Calling this method essentially makes this Feature observable to all other features and makes it an observer of all other features
     * - This method is only supposed to be invoked by an instance of the FeatureGraph class
     * @param {FeatureGraph} graph - an instance of my FeatureGraph class that has already been built
     * @returns {undefined}
     */
    setGraph(graph) {
        if (!(graph instanceof FeatureGraph)) {
            throw TypeError('"graph" argument must be an instanceof FeatureGraph.');
        }
        if (this.#graph instanceof FeatureGraph) {
            throw Error(`The feature "${this.getProperty('treeKey', 'meta')}" is already in a FeatureGraph.`);
        }
        this.#graph = graph;
    }

    /**
     * @param {string} propertyKey - the property key of the property that is being changed or created in this ObservableInterface instance
     * @param {(string|Object)} propertyValue - the property value of the property that is being changed or created in this observable. I don't like
     *  to store Objects, Arrays, etc. as property values, but it's required for certain observables like those that represent form objects
     * @param {string} [namespace='treeProps'] - the namespace of the property key in this observable. Whether a new namespace is created if a
     *  non-existent namespace is passed is implementation dependent. I throw a ReferenceError because I don't want new namespaces
     * @returns {undefined}
     */
    setProperty(propertyKey, propertyValue, namespace='treeProps') {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be a string.');
        }
        if (typeof namespace !== 'string') {
            throw TypeError('"namespace" argument must be a string.');
        }
        if (['treeProps', 'formProps', 'urlProps'].includes(namespace)) {
            if (this.#feature.properties.hasOwnProperty(namespace)) {
                let oldPropertyValue = propertyValue;
                if (this.hasProperty(propertyKey, namespace)) {
                    oldPropertyValue = this.getProperty(propertyKey, namespace);
                }
                this.#feature.properties[namespace][propertyKey] = propertyValue;
                this.updatePropertyOfObservers(propertyKey, oldPropertyValue, namespace);
                return;
            } 
            throw ReferenceError(`This feature does not have the namespace "${namespace}".`);
        } else if (namespace === 'meta') {
            let oldPropertyValue = propertyValue;            
            if (this.hasProperty(propertyKey, namespace)) {
                oldPropertyValue = this.getProperty(propertyKey, namespace);
            }
            this.#feature.properties[propertyKey] = propertyValue;
            this.updatePropertyOfObservers(propertyKey, oldPropertyValue, namespace);
            return;
        }
        throw ReferenceError(`The namespace "${namespace}" does not exist in this Feature. Leave the "namespace" argument empty to use the "treeProps" namespace.`);
    }

    /**
     * - Don't pass arbitrary messages between Observables and Observers. If I want to do crazy things like use one node as a pivot point to rotate
     *   all of the other nodes, all of the rotating nodes should have a "pivot" property in the meta namespace that matches this Observable or
     *   something, and they should check that property when coordinates are updated and respond appropriately
     * @param {Array} oldCoordinates - the previous coordinates of this ObservableInterface instance prior to the new, current coordinates
     * @returns {undefined}
     */
    updateCoordinatesOfObservers(oldCoordinates) {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        this.#observers.forEach(ob => ob.handleUpdatedCoordinates(this, oldCoordinates));
        if (this.#graph instanceof FeatureGraph) {
            this.#graph.handleUpdatedCoordinates(this, oldCoordinates);
        }
    }

    /**
     * @param {string} propertyKey - the property key of the property that is being created/changed/deleted in this ObservableInterface instance
     * @param {(string|Object)} oldPropertyValue - the previous property value of the property that was created/changed/deleted in this observable. I
     *  don't like to store Objects, Arrays, etc. as property values, but it's required for certain observables like those that represent form objects
     * @param {string} [namespace='treeProps'] - the namespace of the property key in this observable. Whether a new namespace is created if a
     *  non-existent namespace is passed is implementation dependent. I throw a ReferenceError because I don't want new namespaces
     * @returns {undefined}
     */
    updatePropertyOfObservers(propertyKey, oldPropertyValue, namespace='treeProps') {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        this.#observers.forEach(ob => ob.handleUpdatedProperty(this, propertyKey, oldPropertyValue, namespace));
        if (this.#graph instanceof FeatureGraph) {
            this.#graph.handleUpdatedProperty(this, propertyKey, oldPropertyValue, namespace);
        }
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
        throw new UnsupportedOperationError();
    }

    handleNewObservable(observable) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        throw new UnsupportedOperationError();
    }

    /**
     * - Update this ObserverInterface instance (i.e. "this") based on the coordinates of the ObservableInterface instance (i.e. "observable") that
     *   have just changed and perform other actions as needed
     *  - E.g. update the line observer's coordinates to match the node observable's coordinates if the line was connected to the node
     * @param {Object} observable - an instance of ObservableInterface that this Observer is observing
     * @param {Array} oldCoordinates - the old coordinates of the observable prior to the change in coordinates
     * @returns {undefined}
     */
    handleUpdatedCoordinates(observable, oldCoordinates) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!(oldCoordinates instanceof Array)) {
            throw TypeError('"oldCoordinates" argument must be an array.');
        }
        const observableName = observable.getProperty('name');
        const thisName = this.getProperty('name');
        const thisKey = this.getProperty('treeKey', 'meta');
        if (this.isLine()) {
            const fromName = this.getProperty('from');
            const toName = this.getProperty('to');
            if (![fromName, toName].includes(observableName)) {
                if (observable.isLine()) {
                    // - This isn't an error. It means a child line is connected to this line and the child line was updated. Since parents observe
                    //   children, this line gets a call to update even though it doesn't need to do anything
                } else {
                    throw Error(`The Feature instance "${observableName}" is not connected to the line Feature instance "${thisName}."`);
                }
            }
            const fromKey = this.#graph.getKey(fromName, thisKey);
            const toKey = this.#graph.getKey(toName, thisKey);
            const { sourceLat, sourceLon, targetLat, targetLon } = this.#graph.getLineLatLon(fromKey, toKey);
            this.setCoordinates([[sourceLon, sourceLat], [targetLon, targetLat]]);
        } else {
            throw Error(`The Feature instance "${observableName}" tried to update the Feature instance "${thisName}", but there is no relationship between the features.`);
        }
    }

    /**
     * - Update this ObserverInstance (i.e. "this") based on the property of the ObservableInterface instance (i.e. "observable") that has just
     *   changed and perform other actions as needed
     *  - E.g. update this line's "to" and/or "from" property to match the "name" property of the node that was just changed
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
        if (propertyKey === 'name') {
            ['from', 'to', 'parent'].forEach(k => {
                if (this.hasProperty(k) && this.getProperty(k) === oldPropertyValue) {
                    this.setProperty(k, observable.getProperty('name'));
                }
            });
        }
    }

    // ********************
    // ** Public methods **
    // ********************

    /**
     * @returns {boolean} whether this ObservableInterface instance (i.e. a node) is a child of another node or line
     */
    isChild() {
        return this.hasProperty('parent');
    }

    /**
     * @returns {boolean} whether this ObservableInterface instance is a component feature, which is a non-displayed ObservableInterface instance that
     * is used to create displayed ObservableInterface instances. Non-configuration-object components DO have real coordinates.
     */
    isComponentFeature() {
        return this.getProperty('treeKey', 'meta').startsWith('component:');
    }

    /**
     * @returns {boolean} whether this ObservableInterface instance is displayed in the map visualization
     */
    isConfigurationObject() {
        return !this.hasCoordinates();
    }

    /**
     * @returns {boolean} whether this ObservableInterface instance is a line
     */
    isLine() {
        return this.hasProperty('to') && this.hasProperty('from') && !this.isConfigurationObject();
    }

    /**
     * @returns {boolean} whether this ObservableInterface instance is a modal feature, which is a non-displayed ObservableInterface instance that is
     * used to create a modal.
     */
    isModalFeature() {
        return this.getProperty('treeKey', 'meta').startsWith('modal');
    }


    /**
     * @returns {boolean} whether this ObservableInterface instance is a node
     */
    isNode() {
        return !this.isLine() && !this.isConfigurationObject();
    }

    /**
     * @returns {boolean} whether this ObservableInterface instance is a parent-child line
     */
    isParentChildLine() {
        return this.getProperty('treeKey', 'meta').startsWith('parentChild:');
    }

    isPolygon() {
        return this.#feature.geometry.type === 'Polygon';
    }

    /**
     * - Reset this Feature's coordinates and properties to how they were when the page was loaded
     * @returns {undefined}
     */
    resetState() {
        this.setCoordinates(structuredClone(this.#originalFeature.geometry.coordinates));
        for (const [key, val] of Object.entries(this.#feature.properties)) {
            if (!this.#originalFeature.properties.hasOwnProperty(key)) {
                this.deleteProperty(key, 'meta');
            } else {
                this.setProperty(key, this.#originalFeature.properties[key], 'meta');
            }
            if (key === 'treeProps') {
                for (const [tKey, tVal] of Object.entries(this.#feature.properties.treeProps)) {
                    if (!this.#originalFeature.properties.treeProps.hasOwnProperty(tKey)) {
                        this.deleteProperty(tKey);
                    } else {
                        this.setProperty(tKey, this.#originalFeature.properties.treeProps[tKey]);
                    }
                }
            }
            // - Modal features can't be edited by the user, so I don't need to deal with formProps or urlProps
        }
    }
}

class UnsupportedOperationError extends Error {

    constructor() {
        super();
        this.message = `An interface defines this method, but the method is not implemented in this class.`;
        this.name = 'UnsupportedOperationError';
    }
}

class ObserverError extends Error {
    
    constructor() {
        super();
        this.message = `This type of ObserverInterface instance is not allowed to observe this ObservableInterface instance`;
        this.name = 'ObserverError';
    }
}