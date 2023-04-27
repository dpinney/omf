export { FeatureController };
import { Feature } from './feature.js';
import { FeatureGraph } from './featureGraph.js';
import { LeafletLayer } from './leafletLayer.js';
import { Modal } from './modal.js';

class FeatureController { // implements ControllerInterface
    #observableGraph; // - A FeatureGraph instance

    /**
     * @param {FeatureGraph} observableGraph - a FeatureGraph instance that contains all of the actual data
     */
    constructor(observableGraph) {
        if (!(observableGraph instanceof FeatureGraph)) {
            throw TypeError('"observableGraph" argument must be instanceof FeatureGraph.')
        }
        this.#observableGraph = observableGraph;
    }

    // *********************************
    // ** ControllerInterface methods **
    // *********************************

    /**
     * @param {Array} observables - an array of ObservableInterface instances that should be added to the graph
     * @returns {undefined}
     */
    addObservables(observables) {

    }

    /**
     * - Delete the property with the matching namespace and property key from all of the ObservableInterface instances
     * @param {Array} observables - an array of ObservableInterface instances from which the property should be deleted
     * @param {string} propertyKey - the property key of the property that is in the observables
     * @param {string} namespace - the namespace of the property that is in the observables 
     * @returns {undefined}
     */
    deleteProperty(observables, propertyKey, namespace) {
        if (!(observables instanceof Array)) {
            throw TypeError('"observables" argument must be instanceof Array.');
        }
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be a string.');
        }
        if (typeof namespace !== 'string') {
            throw TypeError('"namespace" argument must be a string.');
        }
        observables.forEach(ob => {
            if (ob.hasProperty(propertyKey, namespace)) {
                ob.deleteProperty(propertyKey, namespace);
            }
        });
        // - Currently, this function is a convenience function that views could do themselves because nothing else needs to be done besides calling
        //   deleteProperty() on the ObservableInterface instances
    }

    /**
     * - Tell the ObservableInterface instances to delete themselves
     * @param {Array} observables - an array of ObservableInterface instances from which the property should be deleted
     * @returns {undefined}
     */
    deleteObservables(observables) {
        if (!(observables instanceof Array)) {
            throw TypeError('"observables" argument must be instanceof Array.');
        }
        observables.forEach(ob => {
            ob.deleteObservable();
        });
        // - I shouldn't have to do this because all visited nodes are deleted
        //this.observableGraph.markNodesAsUnvisited();
        // - Currently, this function is a convenience function that views could do themselves because nothing else needs to be done besides calling
        //   deleteObservable() on the ObservableInterface instances
    }

    /**
     * @param {Array} observables - an array of ObservableInterface instances whose coordinates should be set
     * @param {Array} coordinates - an array of coordinates for this ObservableInterface instance
     *  - E.g. for node Feature instances this should be in [<lon>, <lat>] format
     * @returns {undefined}
     */
    setCoordinates(observables, coordinates) {
        if (!(observables instanceof Array)) {
            throw TypeError('"observables" argument must be instanceof Array.');
        }
        if (!(coordinates instanceof Array)) {
            throw TypeError('"coordinates" argument must be instanceof Array.');
        }
        observables.forEach(ob => {
            ob.setCoordinates(coordinates);
        });
        // - I have to mark all the nodes as unvisted here because I can't do it in any of the other coordinate-related functions since they all call
        //   each other
        this.observableGraph.markNodesAsUnvisited();        
    }

    /**
     * @param {Array} observables - an array of ObservableInterface instances whose property should be set
     * @param {string} propertyKey - the property key of the property that is being created/changed in the ObservableInterface instances
     * @param {(string|Object)} propertyValue - the property value of the property that is being created/changed in the ObservableInterface instances.
     *  I don't like to store Objects, Arrays, etc. as property values, but it's required for certain observables like those that represent form
     *  objects
     * @param {string} [namespace='treeProps'] - the namespace of the property key in this observable. Whether a new namespace is created if a
     *  non-existent namespace is passed is implementation dependent. I throw a ReferenceError because I don't want new namespaces
     * @returns {undefined}
     */
    setProperty(observables, propertyKey, propertyValue, namespace='treeProps') {
        if (!(observables instanceof Array)) {
            throw TypeError('"observables" argument must be instanceof Array.');
        }
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be a string.');
        }
        if (typeof namespace !== 'string') {
            throw TypeError('"namespace" argument must be a string.');
        }
        observables.forEach(ob => {
            ob.setProperty(propertyKey, propertyValue, namespace); 
            const obKey = ob.getProperty('treeKey', 'meta');
            if (['from', 'to'].includes(propertyKey)) {
                const fromKey = this.#observableGraph.getKey(ob.getProperty('from'), obKey);
                const toKey = this.#observableGraph.getKey(ob.getProperty('to'), obKey);
                const { sourceLat, sourceLon, targetLat, targetLon } = this.#observableGraph.getLineLatLon(fromKey, toKey);
                ob.setCoordinates([[sourceLon, sourceLat], [targetLon, targetLat]]);
            } 
            if (propertyKey === 'parent') {
                const fromKey = this.#observableGraph.getKey(ob.getProperty('parent'), obKey);
                const toKey = obKey;
                const { sourceLat, sourceLon, targetLat, targetLon } = this.#observableGraph.getLineLatLon(fromKey, toKey);
                const parentChildLine = this.#observableGraph.getParentChildLine(obKey);
                parentChildLine.setCoordinates([[sourceLon, sourceLat], [targetLon, targetLat]]);
            } 
        });
        // - ob.setProperty() eventually calls <FeatureGraph>.handleUpdatedProperty(), so I must mark nodes as unvisited here
        this.#observableGraph.markNodesAsUnvisited();
    }
    

    // *******************************
    // ** ObserverInterface methods **
    // *******************************

    /**
     * - Remove this ObserverInterface instance (i.e. "this") from the ObservableInterface instance (i.e. "observable") that has been deleted, and
     *   perform other actions as needed
     * - A FeatureController instance needs to implement the ObserverInterface because that's the only way it can can updated when an
     *   ObservableInterface instance is deleted
     * @param {Object} observable - an instance of ObservableInterface that this Observer is observing
     * @returns {undefined}
     */
    handleDeletedObservable(observable) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!this.#removed) {
            observable.removeObserver(this);
            this.#ids = this.#ids.filter(id => id !== observable.getProperty('treeKey', 'meta'));
            if (this.#ids.length === 0) {
                this.remove();
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
        // - Do nothing. A FeatureController doesn't care if coordinates change
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
        // - Do nothing. A FeatureController doesn't care if a property is added/changed/deleted
    }

    // ********************
    // ** Public methods **
    // ********************

    /**
     * - Set the IDs to determine the subset of ObservableInterface instances in the ObservableGraphInterface that this FeatureController can control
     *   and observe
     * @param {Array} ids
     * @returns {undefined}
     */
    setIDs(ids) {
        if (!(ids instanceof Array)) {
            throw TypeError('"ids" argument must be an array');    
        }
        if (ids.length < 1) {
            throw Error('"ids" argument must have at least one element');
        }
        if (ids.some(id => typeof id !== 'string')) {
            throw TypeError('"ids" argument must be an array of strings that correspond to the "treeKey" property of Features');
        }
        if (this.#ids !== null) {
            if (this.isComponentManager) {
                // - A ControllerInterface MUST observe its components because that's the only way views (e.g. TreeFeatureModal) can render updates
                //   correctly
                this.#ids.forEach(id => this.#componentMap[id].removeObserver(this));
            } else {
                this.#ids.forEach(id => this.observableGraph.getObservable(id).removeObserver(this));
            }
        }
        if (this.isComponentManager) {
            // - A ControllerInterface MUST observe its components because that's the only way views (e.g. TreeFeatureModal) can render updates
            //   correctly
            ids.forEach(id => this.#componentMap[id].registerObserver(this));
        } else {
            ids.forEach(id => this.observableGraph.getObservable(id).registerObserver(this));
        }
        this.#ids = ids;
        // - Add validation logic here so that other classes don't need to worry about it. Actually, I can't do that. Some controllers manage all of
        //   the ObservableInterface instances (e.g. configuration and non-configuration objects) while other controllers only manage a single
        //   ObservableInterface instance. What constitutes an invalid controller depends on the context
    }

    /**
     * - Remove this FeatureController
     *  - A FeatureController doesn't have a visual appearance, so the DOM won't change. However, sometimes a view needs to remove itself, so the
     *    controller that's managing the view should also have the ability to remove itself
     *  - Be careful not to remove a controller that managing multiple views if one the views still exists!
     * @returns {undefined}
     */
    remove() {
        if (!this.#removed) {
            if (this.isComponentManager) {
                this.#ids.forEach(id => this.#componentMap[id].removeObserver(this));
            } else {
                this.#ids.forEach(id => this.observableGraph.getObservable(id).removeObserver(this)); 
            }
            this.#ids = null;
            this.observableGraph = null;
            this.#removed = true;
        }
    }


    /**
     * @returns {Array} an array of the ObservableInterface instances (i.e. the model(s) in the MVC pattern) that this ControllerInterface is
     *  managing. This method is needed by ObserverInterface instances (i.e. views in the MVC pattern) that need to register themselves on the
     *  ObservableInterface instances
     */
    getObservables() {
        if (this.isComponentManager) {
            return this.#ids.map(id => this.#componentMap[id]);
        } else {
            return this.#ids.map(id => this.observableGraph.getObservable(id));
        }
    }





    /**
     * @param {string} propertyKey - the property key of the property that may or may not be in the observable(s) namespace 
     * @param {string} [namespace='treeProps'] - the namespace of the property key that may or may not be in observable(s)
     * @returns {boolean} true if any one of the observable(s) have the property, else false
     */
    hasProperty(propertyKey, namespace='treeProps') {
        if (this.isComponentManager) {
            return this.#ids.some(id => this.#componentMap[id].hasProperty(propertyKey, namespace));
        } else {
            return this.#ids.some(id => this.observableGraph.getObservable(id).hasProperty(propertyKey, namespace));
        }
    }



    /**
     * @returns {boolean} true if any of the observables is a configuration object
     */
    hasConfigurationObjects() {
        if (this.isComponentManager) {
            return this.#ids.some(id => this.#componentMap[id].isConfigurationObject());
        } else {
            return this.#ids.some(id => this.observableGraph.getObservable(id).isConfigurationObject());
        }
    }

    /**
     * @returns {boolean} true if any of the observables is a component object
     */
    hasComponents() {
        if (this.isComponentManager) {
            return true;
        } else {
            if (this.#ids.some(id => this.observableGraph.getObservable(id).isComponentFeature())) {
                throw Error('This FeatureController references at least one component, but it is not a component manager.');
            }
            return false;
        }
    }

    /**
     * @returns {boolean} true if any of the observables is a line object
     */
    hasLines() {
        if (this.isComponentManager) {
            return this.#ids.some(id => this.#componentMap[id].isLine());
        } else {
            return this.#ids.some(id => this.observableGraph.getObservable(id).isLine());
        }
    }
    
    /**
     * @returns {boolean} true if any of the observables is a node object
     */
    hasNodes() {
        if (this.isComponentManager) {
            return this.#ids.some(id => this.#componentMap[id].isNode());
        } else {
            return this.#ids.some(id => this.observableGraph.getObservable(id).isNode());
        }
    }

    /**
     * - ?
     */
    massAddFeature() {

    }

    /**
     * @param {Array} [clickCoordinates=null] - An array of coordinates that the ObservableInterface instance should use, or null. 
     *      E.g. for nodes use [<lat>, <lng>] format
     * @returns {undefined}
     */
    addObservable(clickCoordinates=null) {
        if (!this.isComponentManager) {
            throw Error('For now, only FeatureController instances that are also component managers can add features.');
        }
        if (this.#ids.length !== 1) {
            throw Error('This FeatureController instance can only add one Feature instance at a time');
        }
        if (!(clickCoordinates instanceof Array) && clickCoordinates !== null) {
            throw TypeError('"clickCoordinates" argument should be an array or null.');
        }
        const geometry = {
            type: 'Point'
        };;
        const observable = new Feature({
            geometry: geometry,
            properties: {
                treeKey: (this.observableGraph.getMaxKey() + 1).toString(),
                treeProps: structuredClone(this.#componentMap[this.#ids[0]].getProperties('treeProps'))
            },
            type: 'Feature'
        });
        let coordinates = structuredClone(this.#componentMap[this.#ids[0]].getCoordinates());
        if (clickCoordinates !== null) {
            coordinates = [clickCoordinates[1], clickCoordinates[0]];
        }
        if (coordinates[0] instanceof Array) {
            const fromKey = this.observableGraph.getKeyForComponent(observable.getProperty('from'));
            const toKey = this.observableGraph.getKeyForComponent(observable.getProperty('to'));
            const { sourceLat, sourceLon, targetLat, targetLon } = this.observableGraph.getLineLatLon(fromKey, toKey);
            coordinates = [[sourceLon, sourceLat], [targetLon, targetLat]];
            geometry.type = 'LineString'
        }
        geometry.coordinates = coordinates;
        this.observableGraph.insertObservable(observable);
        if (!observable.isConfigurationObject()) {
            const controller = new FeatureController(this.observableGraph, [observable.getProperty('treeKey', 'meta')]);
            new LeafletLayer(controller);
        }
        if (observable.isChild()) {
            const parentKey = this.observableGraph.getKey(observable.getProperty('parent'), observable.getProperty('treeKey', 'meta'));
            const childKey = observable.getProperty('treeKey', 'meta');
            const parentChildLineFeature = this.observableGraph.getParentChildLineFeature(parentKey, childKey);
            this.observableGraph.insertObservable(parentChildLineFeature);
            const controller = new FeatureController(this.observableGraph, [parentChildLineFeature.getProperty('treeKey', 'meta')]);
            new LeafletLayer(controller);
        }
    }

    /**
     * - Send an AJAX request to the server
     * @param {ModalFeatureModal} modal
     * @param {boolean} reload - whether or not to reload the page. This is necessary when chaining multiple operations together (e.g. every rename
     * operation must be preceeded by a save operation)
     * @returns {undefined}
     */
    async submitFeature(modal, reload=true) {
        if (this.isComponentManager) {
            throw Error('A FeatureController should not manage modal features and be a component manager');
        }
        if (this.#ids.length !== 1) {
            throw Error('A FeatureController that is responsible for submitting AJAX requests to the server should only track one Feature at a time.');
        }
        if (!this.observableGraph.getObservable(this.#ids[0]).getProperty('treeKey', 'meta').startsWith('modal:')) {
            throw Error('A FeatureController that is responsible for submitting AJAX requests to the server should only manage a modal feature');
        }
        if (!(modal instanceof Modal)) {
            throw TypeError('"modal" argument must be instanceof Modal');
        }
        const observable = this.observableGraph.getObservable(this.#ids[0]);
        let data;
        if (observable.hasProperty('fileExistsUrl', 'urlProps')) {
            try {
                data = await $.ajax({
                    type: observable.getProperty('fileExistsUrl', 'urlProps').method,
                    url: observable.getProperty('fileExistsUrl', 'urlProps').url
                });
                switch (this.#ids[0]) {
                    case 'modal:rename':
                    case 'modal:opendss':
                    case 'modal:windmil':
                    case 'modal:cymdist':
                    case 'modal:gridlabd':
                        if (data.exists === true) {
                            modal.showProgress(false, 'You already have a feeder with that name. Please choose a different name', 'caution');
                            return;
                        }
                        break;
                    case 'modal:loadFeeder':
                        // - I do this to assert that data.exists is equal to true, not that it is truthy. There's an important difference
                        if (data.exists === true) {
                            modal.showProgress(true, 'Loading feeder from the server...', 'caution');
                            break;
                        }
                    default:
                        if (data.exists !== true) {
                            modal.showProgress(false, 'This feeder no longer exists on the server, so the operation failed. Please save and try again.', 'caution');
                        }
                }
            } catch {
                modal.showProgress(false, 'The server raised an internal exception during the operation. Please save before trying again.', 'caution'); 
                return;
            }
        }
        const formData = new FormData(); 
        if (observable.hasProperty('formProps', 'meta')) {
            for (const [key, val] of Object.entries(observable.getProperties('formProps'))) {
                formData.set(key, val);
            };
        }
        try {
            data = await $.ajax({
                type: observable.getProperty('submitUrl', 'urlProps').method,
                url: observable.getProperty('submitUrl', 'urlProps').url,
                data: formData,
                processData: false,
                contentType: false,
            });
        } catch {
            modal.showProgress(false, 'The server raised an internal exception during the operation. Please save before trying again.', 'caution'); 
            return;
        }
        const that = this;
        // - We don't want to poll the server. Just reload the page.
        if (!observable.hasProperty('pollUrl', 'urlProps')) {
            if (data === 'Failure') {
                modal.showProgress(false, 'The server operation failed.', 'caution');
            } else {
                if (reload) {
                    that.#reloadPage();
                } else {
                    document.getElementById('modalInsert').classList.remove('visible');
                }
            }
        } else {
            const intervalId = setInterval(async function() {
                try {
                    data = await $.ajax({
                        type: observable.getProperty('pollUrl', 'urlProps').method,
                        url: observable.getProperty('pollUrl', 'urlProps').url
                    });
                    // - The server process ID file no longer exists, so the server operation completed successfully
                    if (data.exists === false) {
                        clearInterval(intervalId);
                        if (reload) {
                            that.#reloadPage();
                        } else {
                            document.getElementById('modalInsert').classList.remove('visible');
                        }
                    } else if (data.exists === undefined) {
                        clearInterval(intervalId);
                        if (data === 'milError') {
                            modal.showProgress(false, 'The .std and .seq files used were incorrectly formatted. Please save before trying again.', 'caution');
                        } else if (data === 'dssError') {
                            modal.showProgress(false, 'The .dss file used was incorrectly formatted. Please save before trying again.', 'caution');
                        } else if (data === 'cymeError') {
                            modal.showProgress(false, 'The .mdb file used was incorrectly formatted. Please save before trying again.', 'caution');
                        } else if (data === 'glmError') {
                            modal.showProgress(false, 'The .glm file used was incorrectly formatted. Please save before trying again.', 'caution');
                        } else if (data === 'amiError') {
                            modal.showProgress(false, 'The AMI file used was incorrectly formatted. Please save before trying again.', 'caution');
                        } else if (data === 'anonymizeError') {
                            modal.showProgress(false, 'The anonymization process failed. Please save before trying again.', 'caution');
                        } else {
                            if (!data.endsWith('.')) {
                                data += '.';
                            }
                            data += ' Please save before trying again.';
                            clearInterval(intervalId);
                            modal.showProgress(false, data, 'caution');
                        }
                    // - The server process is ongoing, so let setInterval keep going
                    } else if (data.exists === true) {
                        // - Do nothing
                    } else {
                        throw Error('Undefined value returned by server during the polling process.');
                    }
                } catch {
                    clearInterval(intervalId);
                    modal.showProgress(false, 'The server raised an internal exception during the operation. Please save before trying again.', 'caution');
                    return;
                }
            }, 5000);
        }
    }

    // *********************
    // ** Private methods ** 
    // *********************

    /**
     * - Force the client to always request new files from the server without using the browser cache.
     */
    #reloadPage() {
        window.location.reload(true);
        //console.log('Reloaded page');
    }
}