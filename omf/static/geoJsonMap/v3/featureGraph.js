export { FeatureGraph, FeatureNotFoundError };
import { Feature } from './feature.js';

class FeatureGraph {
    // - Names are not unique, so I potentially need to map one name to multiple keys
    #nameToKey;     
    // - Graphology graphs allow nodes and lines to have the same key. This is great for representing lines with children, but is annoying when trying
    //   to retrieve a feature by its key
    #keyToFeature;
    // - This points to the actual graph data structure. I'm using the Graphology library
    #graph;

    /**
     * - Create an empty graph that will connect all Feature instances (regular features, components, parent-child lines, etc.) as Observables and
     *   Observers
     * @returns {Object} graph
     */
    constructor() {
        this.#nameToKey = {};
        this.#keyToFeature = {};
        const options = {
            // - Do NOT allow self-loops. Even if a line starts and ends on the same node, the graph models it as three nodes connected by two edges
            allowSelfLoops: false,   
            // - Allow multiple edges between nodes (OMDs have them)
            multi: true,            
            // - Restrict to an undirected graph type
            type: 'undirected'      
        };
        this.#graph = new graphology.Graph(options);
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
        const observableKey = observable.getProperty('treeKey', 'meta');
        this.#graph.setNodeAttribute(observableKey, 'visited', true);
        if (this.#graph.hasNode(observableKey)) {
            // - If a node is deleted, all of its attached lines need to be deleted too
            if (observable.isNode()) {
                this.#graph.edges(observableKey).forEach(edgeKey => {
                    const observerKey = this.#getObserverKey(observableKey, edgeKey);
                    const observer = this.getObservable(observerKey);
                    if (observer.isLine()) {
                        if (this.#graph.getNodeAttribute(observerKey, 'visited') !== true) {
                            observer.deleteObservable();
                        }
                    } else {
                        throw NodeEdgeError(observableKey, observerKey);
                    }
                });
            // - If a line is deleted, any attached lines also need to be deleted
            //  - TODO: only the line(s) that have a "from" or "to" value that matches the name of the line being deleted should also be deleted,
            //    otherwise creating a triangle of lines and deleting the bracing line deletes the other two lines
            } else if (observable.isLine()) {
                this.#graph.edges(observableKey).forEach(edgeKey => {
                    const observerKey = this.#getObserverKey(observableKey, edgeKey);
                    const observer = this.getObservable(observerKey);
                    // - If the observable is a parent-child line, delete the child and any attached lines
                    if (observable.isParentChildLine()) {
                        const childName = observable.getProperty('to');
                        if (observer.getProperty('name') === childName) { 
                            if (this.#graph.getNodeAttribute(observerKey, 'visited') !== true) {
                                observer.deleteObservable();
                            }
                        }
                    // - If the observable is not a parent-child line, just delete any attached lines
                    } else if (observer.isLine()) { 
                        if (this.#graph.getNodeAttribute(observerKey, 'visited') !== true) {
                            observer.deleteObservable();
                        }
                    }
                });
            }
            this.#graph.dropNode(observableKey);
            this.#removeObservableFromNameToKey(observable, observable.getProperty('name'));
            this.#removeObservableFromKeytoFeature(observable);
        } else {
            throw FeatureNotFoundError(key);
        }
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
            throw TypeError('"oldCoordinates" argument must be an array.')
        }
        const observableKey = observable.getProperty('treeKey', 'meta');
        // - Mark this node as visited to prevent infinite recursion
        this.#graph.setNodeAttribute(observableKey, 'visited', true);
        // - Redraw attached lines. That's all I need to do for now
        if (this.#graph.hasNode(observableKey)) {
            this.#graph.edges(observableKey).forEach(edgeKey => {
                const observerKey = this.#getObserverKey(observableKey, edgeKey);                
                const observer = this.getObservable(observerKey);
                if (this.#graph.getNodeAttribute(observerKey, 'visited') !== true) {
                    if (observer.isLine()) {
                        observer.handleUpdatedCoordinates(observable, oldCoordinates);
                    } else if (observable.isNode() && observer.isNode()) {
                        throw NodeEdgeError(observableKey, observerKey);
                    }
                }
            });
        } else {
            throw FeatureNotFoundError(observableKey);
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
        const observableKey = observable.getProperty('treeKey', 'meta');
        this.#graph.setNodeAttribute(observableKey, 'visited', true);
        if (this.#graph.hasNode(observableKey)) {
            // - Deal with property updates that don't affect the connectivity of the graph
            if (propertyKey === 'name') {
                this.#removeObservableFromNameToKey(observable, oldPropertyValue);
                this.#insertObservableIntoNameToKey(observable);
                this.#graph.forEachNode((node, attributes) => {
                    this.getObservable(node).handleUpdatedProperty(observable, propertyKey, oldPropertyValue, namespace);
                });    
            // - Deal with property updates that affect the connectivity of the graph
            } else if (['from', 'to', 'parent'].includes(propertyKey)) {
                for (const edgeKey of this.#graph.edges(observableKey)) {
                    const observer1Key = this.#getObserverKey(observableKey, edgeKey);
                    const observer1 = this.getObservable(observer1Key);
                    // - If true, observable is a line and observer1 is one of the two nodes that is connected to it
                    if (['from', 'to'].includes(propertyKey)) {
                        if (oldPropertyValue === observer1.getProperty('name')) {
                            this.#graph.dropEdge(edgeKey);
                            this.#graph.addEdge(observableKey, this.getKey(observable.getProperty(propertyKey), observableKey));
                            // - For most lines, this break won't do anything since "from" and "to" are not the same so only one observer's name will
                            //   match the oldPropertyValue
                            // - For lines whose "from" and "to" values are the same, this break is necessary because without it, changing either "from"
                            //   or "to" of the looped line will make the graph drop all edges between the line and the node when only one edge should be
                            //   dropped
                            break;
                        }
                    }
                    // - If true, observable is a child node and observer1 is the line that connects the child and the parent
                    if (propertyKey === 'parent') {
                        // - Currently, nodes can only have a single parent, so I don't have to deal with multiple parent-child lines going to one
                        //   (child) node. That means that this entire if-statement below should only execute one time even though the outer for-loop
                        //   continues to run once edges are dropped and added
                        if (observer1.isParentChildLine()) {
                            for (const edgeKey2 of this.#graph.edges(observer1Key)) {
                                const observer2Key = this.#getObserverKey(observer1Key, edgeKey2);
                                const observer2 = this.getObservable(observer2Key);
                                // - If true, observer2 is the old parent node
                                if (oldPropertyValue === observer2.getProperty('name')) {
                                    this.#graph.dropEdge(edgeKey2);
                                    this.#graph.addEdge(observer1Key, this.getKey(observable.getProperty(propertyKey), observer1Key));
                                    // - I need to update the parent-child line to have the correct "from" and "to" treeProps properties 
                                    ['from', 'to'].forEach(prop => {
                                        if (observer1.getProperty(prop) === oldPropertyValue) {
                                            observer1.setProperty(prop, observable.getProperty(propertyKey));
                                        }
                                    });
                                    // - Break in case a node has its own name as a parent and I just changed the "parent" value?
                                    break;
                                }
                            }
                        }
                    }
                }
            }
        } else {
            throw FeatureNotFoundError(observableKey);
        }
    }

    // ********************
    // ** Public methods ** 
    // ********************

    /**
     * - This function accepts an ObservableInterface instance, rather than a basic GeoJSON feature, because I need to rely on the ObservableInterface
     *   API for getting properties. I don't want to assume I'll always be working with true GeoJSON features. All nodes must be inserted before all
     *   lines. If a line is inserted and its nodes don't exist, a ReferencError is thrown.
     * @param {Feature} observable - an ObservableInterface instance
     * @returns {undefined}
     */
    insertObservable(observable) {
        if (!(observable instanceof Feature)) {
            throw TypeError('"observable" argument must be an instance of my Feature class.');
        }
        this.#insertObservableIntoKeyToFeature(observable);
        const observableKey = observable.getProperty('treeKey', 'meta');
        this.#graph.addNode(observableKey);
        // - Insert the feature into the nameToKey map
        // - The following objects sometimes lack the "name" property: recorder, player
        //  - By far, the easiest thing to do is give them a name. I can strip it out on export if needed
        if (!observable.hasProperty('name')) {
            if (observable.hasProperty('object')) {
                const object = observable.getProperty('object');
                if (['recorder', 'player'].includes(object)) {
                    const name = `${object}:${observableKey}:addedName`;
                    observable.setProperty('name', name);
                }
            }
        }
        // - !CMD objects need to be able to have the same command, but the name of the !CMD object is the command. Get around this by creating a new
        //   "command" property whose value replaces the "name" property value on export
        if (observable.hasProperty('object')) {
            const object = observable.getProperty('object');
            if (object === '!CMD') {
                observable.setProperty('CMD_command', observable.getProperty('name'));
                const name = `${object}:${observableKey}:addedName`;
                observable.setProperty('name', name);
            }
        }
        // - Give the feature a pointer to this graph, which effectively makes the feature Observable to all other features and an Observer of all
        //   other features. This needs to be set after recorders and players are given names
        observable._setGraph(this);
        // - Configuration objects aren't pointed to by "to", "from", or "parent", so they don't need names
        this.#insertObservableIntoNameToKey(observable);
        // - Insert the feature into the actual graph
        //  - This logic assumes the following insertion order: (1) all nodes nodes, (2) all lines
        //  - Parent-child lines must be created and inserted with the other lines. They are not automatically created here. Why? Because calling
        //    <ObservableInterface>.registerObserver(<ObserverInterface>) should not create and register another observer as a side-effect
        // - All nodes and all lines are treated as nodes in the graph.
        //  - E.g. a node and two lines are modeled as three nodes, one of which (the actual node) is connected via edges to the other two (line)
        //    nodes
        if (observable.isLine()) {
            const sourceName = observable.getProperty('from');
            const sourceKey = this.getKey(sourceName, observable.getProperty('treeKey', 'meta'));
            // - <Graph>.addEdge() does throw an error for non-existent nodes, which is what I want
            this.#graph.addEdge(sourceKey, observableKey);
            const targetName = observable.getProperty('to');
            const targetKey = this.getKey(targetName, observable.getProperty('treeKey', 'meta')); 
            this.#graph.addEdge(observableKey, targetKey);    
            const sourceObservable = this.getObservable(sourceKey);
            const targetObservable = this.getObservable(targetKey);
            if (sourceObservable.isChild()) {
                if (sourceObservable.getProperty('parent') === targetName) {
                    // - If these conditions are met, this line (which is modeled as a node in this graph) has "from" and "to" mixed up and I need to
                    //   check my parent-child line creation code
                    throw Error(`Parent-child lines should always go from parent (source) to child (target), but the line "${key}" has a source node "${sourceKey}" that is a child.`);
                }
                // - If both conditions are not met, then this line is not a parent-child line, but it is connected to a node that is also a child
                //   node (with a separate parent-child line). This is weird but valid.
            }
            // - I don't need to add a special "isParentChild" attribute to edges anymore. When I inspect the node neighbors of a graph node, all the
            //   information about whether the neighbor node is a another node, a line, a parent-child line, etc. is already present in the
            //   ObservableInterface instance
        }
    }

    /**
     * @param {string} key - the key of the ObservableInterface object that I want
     * @returns {Feature} an instance of my Feature class
     */
    getObservable(key) {
        if (typeof key !== 'string') {
            throw TypeError('"key" argument must be a string.');
        }
        if (!this.#keyToFeature.hasOwnProperty(key)) {
            throw new FeatureNotFoundError(key);
        }
        return this.#keyToFeature[key];
    }
    
    /**
     * @param {Function} func - a function that filters features so that only the desired features are returned. The function should take a single
     * argument (a feature), and should return a boolean depending on whether to include the feature in the array
     * @returns {Array} - an array of instances of my Feature class, where each instance met the filtering criteria
     */
    getObservables(func) {
        if (typeof func !== 'undefined') {
            return Object.values(this.#keyToFeature).filter(f => func(f));
        }
        return Object.values(this.#keyToFeature);
    }

    /**
     * @param {Function} [func=null] - a function that filters features so that only the desired features are returned. The function should take a single
     * argument (a feature), and should return a boolean depending on whether to include the feature in the array
     * @returns {Object} a GeoJSON FeatureCollection object
     */
    getObservablesExportData(func=null) {
        if (func !== null && typeof func !== 'function') {
            throw TypeError('"func" argument must be null or a function');
        }
        if (func === null) {
            func = function(f) {
                if (f.getProperty('treeKey', 'meta') === 'omd') {
                    return true;
                } else {
                    return isNaN(+f.getProperty('treeKey', 'meta')) ? false : true;
                }
            }
        }
        return { 
            'type': 'FeatureCollection',
            'features': this.getObservables(func).map(f => f.getObservableExportData())
        };
    }

    /**
     * @param {string} namespace - the namespace of keys I'm interested in (e.g. "default" for normal keys and "parentChild" for parent-child lines)
     * @returns {number} the current maximum tree key in this FeatureGraph
     */
    getMaxKey(namespace='default') {
        let keys = [];
        for (let k of Object.keys(this.#keyToFeature)) {
            if (namespace === 'default') {
                k = +k;
                if (!isNaN(k)) {
                    keys.push(k);
                }
            } else if (['parentChild'].includes(namespace)) {
                if (k.startsWith(namespace)) {
                    k = +k.split(':')[1];
                    if (!isNaN(k)) {
                        keys.push(k);
                    }
                }
            } else {
                throw ReferenceError(`The key namespace "${namespace}" does not exist in this FeatureGraph. Leave the "namespace" argument empty to use
                    the "default" key namespace.`); 
            }
        }
        // Math.max.apply(null, []) === -Infinity, so I start with 0
        if (keys.length === 0) {
            keys = [0];
        }
        return Math.max.apply(null, keys);
    }

    /**
     * @param {string} name - the name of the feature that I want to retrieve the key for
     * @param {string} featureKey - the key of an instance of my Feature class that is requesting the key
     * @returns {string} The correct tree key of the feature with the given name, depending on which object requested it, else throw an exception if
     *      there is no matching tree key
     */
    getKey(name, featureKey) {
        if (typeof name !== 'string') {
            throw TypeError('"name" argument must be a string.');
        }
        if (typeof featureKey !== 'string') {
            throw TypeError('"feature" argument must be a string.');
        }
        const feature = this.getObservable(featureKey);
        const keys = this.#nameToKey[name];
        if (keys === undefined) {
            throw Error(`This FeatureGraph could not find a key for the object named "${name}", as requested by the feature "${feature.getProperty('name')}". Missing objects are handled on the back-end, not here.`);
        } else if (keys.length === 1) {
            return keys[0];
        }
        // - For recorders, return the first line with the given name. Is this right?
        const objectsWithLineParents = ['recorder'];
        if (objectsWithLineParents.includes(feature.getProperty('object'))) {
            const lineKeys = keys.filter(k => this.getObservable(k).isLine());
            if (lineKeys.length === 1) {
                return lineKeys[0];
            } else {
                throw Error(`This FeatureGraph could not unambiguously find a line for the object named "${feature.getProperty('name')}".`);
            }
        } else {
            const nodeKeys = keys.filter(k => this.getObservable(k).isNode());
            if (nodeKeys.length === 1) {
                return nodeKeys[0];
            } else {
                //throw Error(`This FeatureGraph could not unambiguously find a node for the object named "${feature.getProperty('name')}".`);
                // - HACK (David): How to deal with circuit vs. bus object with same name, or duplicate bus objects with same name?
                //  - Always assume that the line or child wants the "bus" object, not the "circuit" object
                //  - If two buses have identical names, just choose the first bus arbitrarily
                const busKeys = nodeKeys.filter(k => this.getObservable(k).getProperty('object') === 'bus');
                if (busKeys.length > 0) {
                    return busKeys[0];
                } else {
                    // - In really weird situations, such as a case of multiple circuit objects with the same name, just return the first object
                    return nodeKeys[0];
                }
            }
        }
    }

   /**
    * @param {string} name - the name of the feature that I want to retrieve the key for
    * @returns {string} The correct tree key of the feature with the given name. If there are multiple keys, return the first one. Throw an exception
    * if there is no matching tree key.
    */
    getKeyForComponent(name) {
        if (typeof name !== 'string') {
            throw TypeError('"name" argument must be a string.');
        }
        const keys = this.#nameToKey[name];
        if (keys === undefined) {
            throw Error(`This FeatureGraph could not find a key for the object named "${name}". Missing objects are handled on the back-end, not here.`);
        } else {
            return keys[0];
        }
    }

    /**
     * @param {string} sourceKey - the key of an instance of my Feature class that has a line going from it (i.e. the parent)
     * @param {string} targetKey - the key of an instance of my Feature class that has a line going to it (i.e. the child)
     * @returns {Object} An object containing floating-point values for "sourceLat", "sourceLon", "targetLat", "targetLon"
     */
    getLineLatLon(sourceKey, targetKey) {
        let sourceLon, sourceLat, targetLon, targetLat;
        for (let i = 0; i < arguments.length; i++) {
            const observable = this.getObservable(arguments[i]);
            const coordinates = observable.getCoordinates();
            // - TODO: round coordinates?
            let lon, lat;
            if (observable.isLine()) {
                lon = (coordinates[0][0] + coordinates[1][0]) / 2;
                lat = (coordinates[0][1] + coordinates[1][1]) / 2;
            } else if (observable.isNode()) {
                lon = coordinates[0];
                lat = coordinates[1];
            } else {
                throw TypeError(`The feature "${observable.getProperty('name')}" is neither a line nor a node.`);
            }
            if (i === 0) {
                sourceLon = lon;
                sourceLat = lat;
            } else if (i === 1) {
                targetLon = lon;
                targetLat = lat;
            }
        }
        return {
            'sourceLat': sourceLat,
            'sourceLon': sourceLon,
            'targetLat': targetLat,
            'targetLon': targetLon
        }
    }

    /**
     * - Return a new Feature instance that will be used as a parent-child line. This function is a temporary workaround. The controller should just copy
     *   the parent-child line component and insert it. This actually is a special case of the ControllerInterface calling addObservable(). I can think of
     *   the main thread initialization as as special one-time view that should be using the controller to add parent-child line features. The
     *   ControllerInterface should only take an ObservableInterface[], but it needs the graph to be effective. The graph really is an
     *   ObservableInterface[] itself, but I can't put the graph in the UML diagram because then I'm mixing in an implementation. I'll probably just
     *   diagram with the ObservableInterface[], but make the FeatureController actually take a graph. Table view will be created by passing in the entire
     *   graph and an array of keys that the table can look at. "Feature searching" is really just filtering, which is really just calling
     *   <Graph>.getFeatures() 
     * @param {string} parentKey - the key of an instance of my Feature class
     * @param {string} childKey - the key of an instance of my Feature class
     * @returns {Feature} - an instance of my Feature class
     */
    getParentChildLineFeature(parentKey, childKey) {
        const {sourceLat, sourceLon, targetLat, targetLon} = this.getLineLatLon(parentKey, childKey);
        // - This is my custom schema for dealing with parent-child lines
        const maxKey = this.getMaxKey('parentChild');
        const parentChildLineKey = `parentChild:${maxKey + 1}`;
        const parentName = this.getObservable(parentKey).getProperty('name');
        const childName = this.getObservable(childKey).getProperty('name');
        const parentChildLineFeature = new Feature({
            geometry: {
                coordinates: [[sourceLon, sourceLat], [targetLon, targetLat]],
                type: 'LineString'
            },
            properties: {
                treeKey: parentChildLineKey,
                treeProps: {
                    object: 'line',
                    name: parentChildLineKey,
                    phases: 1,
                    type: 'parentChild',
                    from: parentName,
                    to: childName
                }
            },
            type: 'Feature'
        });
        return parentChildLineFeature;
    }

    /**
     * - Mark all nodes as unvisted. The ObservableController instance needs to call this function after calling <Observable>.setCoordinates()
     * @returns {undefined}
     */
    markNodesAsUnvisited() {
        this.#graph.forEachNode((node, attrs) => {
            this.#graph.setNodeAttribute(node, 'visited', false);
        });
    }

    // *********************
    // ** Private methods ** 
    // *********************

    /**
     * - Return the ID of the graph node attached to the edge, as long as the ID != observableKey
     *  - E.g. if I'm examining the edge between a node and a line, and the node was changed, I don't want to be given back the node ID. I want the
     *    line ID
     * @param {string} observableKey - the ID of the ObservableInterface instance that changed in some way
     * @param {string} edgeKey - The edge ID of one edge that is connected to the graph node that represents the ObservableInterface instance
     */
    #getObserverKey(observableKey, edgeKey) {
        const sourceKey = this.#graph.source(edgeKey);
        const targetKey = this.#graph.target(edgeKey);
        if (sourceKey === targetKey) {
            throw SelfLoopError(observableKey);
        }
        if (sourceKey !== observableKey) {
            return sourceKey;
        } else {
            return targetKey;
        }
    }

    /**
     * 
     */
    #insertObservableIntoKeyToFeature(observable) {
        const observableKey = observable.getProperty('treeKey', 'meta');
        if (this.#keyToFeature.hasOwnProperty(observableKey)) {
            throw Error(`The key "${observableKey}" already exists in this.#keyToFeature.`);
        }
        this.#keyToFeature[observableKey] = observable;
    }

    /**
     * 
     */
    #removeObservableFromKeytoFeature(observable) {
        const observableKey = observable.getProperty('treeKey', 'meta');
        if (this.#keyToFeature.hasOwnProperty(observableKey)) {
            delete this.#keyToFeature[observableKey];
        } else {
            throw Error(`The key "${observableKey}" does not exist in this.#keyToFeature.`);
        }
    }
    
    /**
     * - Insert an ObservableInterface instance into the nameToKey map
     * @param {Feature} observable - an ObservableInterface instance
     * @returns {undefined}
     */
    #insertObservableIntoNameToKey(observable) {
        const key = observable.getProperty('treeKey', 'meta');
        if (observable.hasProperty('name')) {
            const name = observable.getProperty('name');
            if (!this.#nameToKey.hasOwnProperty(name)) {
                this.#nameToKey[name] = [key];
            } else {
                if (this.#nameToKey[name].includes(key)) {
                    throw Error(`The key "${key}" is already mapped to the name "${name}".`);
                }
                this.#nameToKey[name].push(key);
            }
        }
    }

    /**
     * - Remove an ObservableInterface instance from the nameToKey map
     * @param {Feature} observable - an ObservableInterface instance
     * @param {string} oldName - the previous name of the ObservableInterface instance
     * @returns {undefined}
     */
    #removeObservableFromNameToKey(observable, oldName) {
        if (!(observable instanceof Feature)) {
            throw TypeError('"observable" argument must be an instanceof Feature');
        }
        if (typeof oldName !== 'string') {
            throw TypeError('"oldName" argument must be a string.');
        }
        const key = observable.getProperty('treeKey', 'meta');
        // - The "name" property cannot be deleted from ObservableInterface instances, so I shouldn't have to deal with a situation where an
        //   observable no longer has a name but its old name is still in this.#nameToKey
        if (observable.hasProperty('name')) {
            if (!this.#nameToKey.hasOwnProperty(oldName)) { 
                // - This function should throw an exception if the ObservableInterface instance's name never existed in this.#nameToKey because that
                //   would only happen if an object that never had a name has been given a name, which isn't allowed (actually recorders and players
                //   are given names
                throw Error(`The name "${oldName}" does not exist in the this.#nameToKey.`);
            }
            if (this.#nameToKey[oldName].includes(key)) {
                this.#nameToKey[oldName] = this.#nameToKey[oldName].filter(k => k !== key);
                if (this.#nameToKey[oldName].length === 0) {
                    delete this.#nameToKey[oldName];
                }
            } else {
                throw Error(`The name "${oldName}" exists in this.#nameToKey, but the key "${key}" does not exist in the array for that name.`);
            }
        }
    }
}

class FeatureNotFoundError extends Error {

    constructor(key) {
        // - After this call to the Error constructor, "message" is undefined but that's okay because I set it immediately after
        super();
        this.message = `This FeatureGraph instance does not have a node with the key "${key}".`;
        this.name = 'FeatureNotFoundError';
    }
}

class SelfLoopError extends Error {
    
    constructor(key) {
        super();
        this.message = `This FeatureGraph instance does not allow self-loops, but one exists on node "${key}".`;
        this.name = 'SelfLoopError';
    }
}

class NodeEdgeError extends Error {
    
    constructor(node1Key, node2Key) {
        super();
        this.message = `This FeatureGraph instance does not currently support edges between nodes, but an edge exists between nodes "${node1Key}" and "${node2Key}".`;
        this.name = 'NodeEdgeError';
    }
}