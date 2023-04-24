export { Feature };
import { FeatureController } from './featureController.js';
import { FeatureGraph } from './featureGraph.js';
'use strict';

class Feature {
    // - This class is designed around the Observer Pattern and the Model View Controller Pattern
    //  - Every Feature instance is both an Observable and an Observer
    //  - This class represents the model in the MVC Pattern
    // - This class implements two interfaces, the "ObservableInterface" and the "ObserverInterface"
    //  - This class implements the "ObservableInterface" interface. Some public methods of this class correspond to methods that are defined in the
    //    ObservableInterface interface. If the data model ever changes, simply replace this class with another class (e.g. a class called
    //    "OMDObject") that implements the same set of public methods
    //  - This class implements the "ObserverInterface" interface. Some public methods of this class correspond to methods that are defined in the
    //    ObserverInterface. If the data model ever changes, simply replace this class with another class (e.g. a class called "OMDObject") that
    //    implements the same set of public methods

    #observers;
    #feature;
    #graph;

    /**
     * @param {Object} feature - a standard GeoJSON feature
     * @param {FeatureGraph} graph - an already-constructed graph that is used to optimize observable-observer notifications. It isn't required, but
     *  is very helpful
     * @returns {undefined}
     */
    constructor(feature) {
        this.#feature = feature;
        this.#observers = [];
        this.#graph = null
    }
    
    // *********************************
    // ** ObservableInterface methods ** 
    // *********************************

    /**
     * - Get the ObserverInterface instances that are observing this ObservableInterface instance
     *  - This is needed to get the LeafletMap for the Zoom button in the TreeFeatureModal class
     */
    getObservers() {
        return this.#observers;
    }

    /**
     * - Mark this ObservableInterface instance as being no longer observable to any observers (i.e. "delete" it)
     *  - Make all of its observers ignore it
     *  - Kick it out of the ObservableGraph interface instance
     * - In all update calls, FeatureControllers must always be updated before other observers because other observers, which are views, ask their
     *   FeatureController for the current subset of observables that they should be displaying
     */
    deleteObservable() {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        this.#observers.filter(ob => ob instanceof FeatureController).forEach(ob => {
            ob.handleDeletedObservable(this);
        });
        this.#observers.filter(ob => !(ob instanceof FeatureController)).forEach(ob => {
            ob.handleDeletedObservable(this);
        });
        if (this.#graph !== null) {
            this.#graph.handleDeletedObservable(this);
        }
    }

    /**
     * @param {Object} observer - an instance of ObserverInterface that wants to observer this ObservableInterface instance
     *  - E.g. this feature is a node and a line feature wants to observe it
     *  - E.g. this feature is a node and a LeafletLayer instance wants to observe it
     */
    registerObserver(observer) {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        if (observer instanceof Feature) {
            throw ObserverError(observer.getProperty('treeKey', 'meta'));
        }
        this.#observers.push(observer);
    }

    /**
     * @param {Object} observer - an instance of ObserverInterface that no longer should observe this ObservableInterface instance
     *  - E.g. a FeatureTable instance shouldn't to observe this ObservableInterface instance anymore
     */
    removeObserver(observer) {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        if (observer instanceof Feature) {
            throw ObserverError(observer.getProperty('treeKey', 'meta'));
        }
        this.#observers = this.#observers.filter(ob => ob !== observer);
    }

    // ** Coordinate-related methods **

    /**
     * - This method is intended to provide a way for this ObservableInterface instance to query its Observers to see if some coordinates are valid.
     *   For example, perhaps it is decided that no two nodes can be stacked directly on top of each other. This method is not intended to validate
     *   whether the coordinates are in a valid format
     * 
     * @returns {boolean} whether the coordinates are valid
     */
    coordinatesAreValid(coordinates) {
        return true;
    }
    
    deleteCoordinates() {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
    }

    /**
     * @returns {Array} the coordinates of the ObservableInterface instance in [<lon>, <lat>] format
     *  - E.g. [<lon>, <lat>] for points and [[<lon_1>, <lat_1>], [<lon_2>, <lat_2>]] for lines
     */
    getCoordinates() {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        return structuredClone(this.#feature.geometry.coordinates);
    }
    
    getOriginalCoordinates() {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
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
        coordinates = structuredClone(coordinates);
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
     * - Don't pass arbitrary messages between Observables and Observers. If I want to do crazy things like use one node as a pivot point to rotate
     *   all of the other nodes, all of the rotating nodes should have a "pivot" property in the meta namespace that matches this Observable or
     *   something, and they should check that property when coordinates are updated and respond appropriately
     * @param {Array} oldCoordinates - the previous coordinates of this ObservableInterface instance prior to the new, current coordinates
     * @returns {undefined}
     */
    updateCoordinatesOfObservers(oldCoordinates) {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        this.#observers.filter(ob => ob instanceof FeatureController).forEach(ob => {
            ob.handleUpdatedCoordinates(this, oldCoordinates);
        });
        this.#observers.filter(ob => !(ob instanceof FeatureController)).forEach(ob => {
            ob.handleUpdatedCoordinates(this, oldCoordinates);
        });
        if (this.#graph !== null) {
            this.#graph.handleUpdatedCoordinates(this, oldCoordinates);
        }
    }

    // ** Property-related methods **

    /**
     * - Delete the property with the matching namespace and property key in this ObservableInstance (i.e. "this") if it exists, otherwise throw a
     *   ReferenceError
     * @param {string} propertyKey - the property key of the property that is in the observable
     * @param {string} [namespace='treeProps'] - the namespace of the property that is in the observable 
     *  - E.g. for Feature instances, this defaults to "treeProps" which corresponds to properties in the "treeProps" object
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
                    throw ReferenceError(`The property "${propertyKey}" could not be found in the namespace "${namespace}" in the Feature instance
                        "${this.getProperty('treeKey', 'meta')}."`);
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
                throw ReferenceError(`The property "${propertyKey}" could not be found in the namespace "${namespace}" in the Feature instance
                    "${this.getProperty('treeKey', 'meta')}."`);
            }
        } else {
            throw ReferenceError(`The namespace "${namespace}" does not exist in this Feature. Leave the "namespace" argument empty to use the
                "treeProps" namespace.`);
        }
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
                    // - I'm not comfortable returning a structuredClone of HTML Nodes with attached event listeners
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

    getOriginalProperties() {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
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
        throw ReferenceError(`The namespace "${namespace}" does not exist in this Feature. Leave the "namespace" argument empty to use the
            "treeProps" namespace.`);
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
    * @param {string} propertyKey - the property key of the property that is being created/changed/deleted in this ObservableInterface instance
    * @param {(string|Object)} oldPropertyValue - the previous property value of the property that was created/changed/deleted in this observable. I
    *  don't like to store Objects, Arrays, etc. as property values, but it's required for certain observables like those that represent form objects
    * @param {string} [namespace='treeProps'] - the namespace of the property key in this observable. Whether a new namespace is created if a
    *  non-existent namespace is passed is implementation dependent. I throw a ReferenceError because I don't want new namespaces
    * @returns {undefined}
    */
    updatePropertyOfObservers(propertyKey, oldPropertyValue, namespace='treeProps') {
        // - The function signature above is part of the ObservableInterface API. The implementation below is not
        this.#observers.filter(ob => ob instanceof FeatureController).forEach(ob => {
            ob.handleUpdatedProperty(this, propertyKey, oldPropertyValue, namespace);
        });
        this.#observers.filter(ob => !(ob instanceof FeatureController)).forEach(ob => {
            ob.handleUpdatedProperty(this, propertyKey, oldPropertyValue, namespace);
        });
        if (this.#graph !== null) {
            this.#graph.handleUpdatedProperty(this, propertyKey, oldPropertyValue, namespace);
        }
    }

    // *******************************
    // ** ObserverInterface methods **
    // *******************************

    /**
     * - Remove this ObserverInterface instance (i.e. "this") from the ObservableInterface instance (i.e. "observable") that has been deleted, and
     *   perform other actions as needed
     *  - E.g. if a node ObservableInterface instance is being deleted, then this line ObserverInterface instance needs to remove itself as an
     *    Observer from the deleted node and also remove itself as an Observer from its other node and then also delete itself
     * @param {Object} observable - an instance of ObservableInterface that this Observer is observing
     * @returns {undefined}
     */
    handleDeletedObservable(observable) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        observable.removeObserver(this);
        if (observable instanceof Feature) {
            throw ObserverError(observable.getProperty('treeKey', 'meta'));
        }
        // - Do nothing. A Feature instance shouldn't be directly observing anything
        throw Error('Feature instances shouldn\'t directly observe anything.');
    }

    /**
     * - Update this ObserverInterface instance (i.e. "this") based on the coordinates of the ObservableInterface instance (i.e. "observable") that
     *   have just changed and perform other actions as needed
     *  - The ObservableGraphInterface instance is an optimization that determines which other ObservableInterface instances have
     *    handleUpdatedCoordinates() invoked. The optimization means I don't need to invoke handleUpdatedCoordinates() on all ObservableInterface
     *    instances everytime any one ObservableInterface instance changes
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
     * - Set the "graph" property of this Feature instance to optimize communication between Feature observables and Feature observers. All Feature
     *   instances are part of the same graph. I can use a graph because all Features have a unique ID, but the overall Observer Pattern doesn't
     *   assume that Observables have unique IDs or that a graph exists at all
     * - Calling this method essentially makes this Feature observable to all other features and makes it an observer of all other features
     * - This method is only supposed to be invoked by an instance of the FeatureGraph class
     * @param {FeatureGraph} graph - an instance of my FeatureGraph class that has already been built
     * @returns {undefined}
     */
    _setGraph(graph) {
        if (!(graph instanceof FeatureGraph)) {
            throw TypeError('"graph" argument must be an instanceof FeatureGraph');
        }
        this.#graph = graph;
    }

    /**
     * @returns {Object} a copy of the underlying data of this ObservableInterface instance
     *  - E.g. a vanilla JavaSCript GeoJSON feature object
     */
    getObservableExportData() {
        // - Recorders and players cannot have a "name" property when being saved, but they need to maintain that property in the interface
        const clone = structuredClone(this.#feature);
        if (clone.properties.hasOwnProperty('treeProps')) {
            if (clone.properties.treeProps.hasOwnProperty('object')) {
                if (['recorder', 'player'].includes(clone.properties.treeProps.object)) {
                    if (clone.properties.treeProps.hasOwnProperty('name')) {
                        const name = clone.properties.treeProps.name;
                        const nameComponents = name.split(':');
                        if (nameComponents.length === 3 && nameComponents[2] === 'addedName') {
                            delete clone.properties.treeProps.name;
                        }
                    }
                }
            }
        }
        return clone;
    }

    /**
     * @returns {boolean} whether this ObservableInterface instance (i.e. a node) is a child of another node or line
     */
    isChild() {
        return this.hasProperty('parent');
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
     * @returns {boolean} whether this ObservableInterface instance is a parent-child line
     */
    isParentChildLine() {
        return this.isLine() && this.hasProperty('type') && this.getProperty('type') === 'parentChild';
    }

    /**
     * @returns {boolean} whether this ObservableInterface instance is a node
     */
    isNode() {
        return !this.isLine() && !this.isConfigurationObject();
    }

    /**
     * @returns {boolean} whether this ObservableInterface instance is a component feature, which is a non-displayed ObservableInterface instance that
     * is used to create displayed ObservableInterface instances. Non-configuration-object components DO have real coordinates.
     */
    isComponentFeature() {
        return this.getProperty('treeKey', 'meta').startsWith('component:');
    }

    /**
     * @returns {boolean} whether this ObservableInterface instance is a modal feature, which is a non-displayed ObservableInterface instance that is
     * used to create a modal.
     */
    isModalFeature() {
        return this.getProperty('treeKey', 'meta').startsWith('modal');
    }

    isPolygon() {
        return this.#feature.geometry.type === 'Polygon';
    }
}

class ObserverError extends Error {
    
    constructor(key) {
        super();
        this.message = `Feature instances must observe other Feature instances through a FeatureGraph, not as direct observers, but the Feature with treeKey "${key}" tried to directly observe another Feature.`;
        this.name = 'ObserverError';
    }
}