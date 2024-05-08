export { FeatureController };
import { Feature } from './feature.js';
import { FeatureGraph } from './featureGraph.js';
import { LeafletLayer } from './leafletLayer.js';
import { hideModalInsert } from './main.js';
import { Modal } from './modal.js';

class FeatureController { // implements ControllerInterface
    observableGraph; // - A FeatureGraph instance. It must be public so that views can query all of the data if they need to

    /**
     * @param {FeatureGraph} observableGraph - a FeatureGraph instance that contains all of the actual data
     */
    constructor(observableGraph) {
        if (!(observableGraph instanceof FeatureGraph)) {
            throw TypeError('"observableGraph" argument must be instanceof FeatureGraph.')
        }
        this.observableGraph = observableGraph;
    }

    // *********************************
    // ** ControllerInterface methods **
    // *********************************

    /**
     * @param {Array} observables - an array of ObservableInterface instances that should be added to the graph
     * @returns {undefined}
     */
    addObservables(observables) {
        observables.forEach(ob => {
            const key = (this.observableGraph.getMaxKey() + 1).toString();
            ob.setProperty('treeKey', key, 'meta');
            this.observableGraph.insertObservable(ob);
            if (!ob.isConfigurationObject()) {
                LeafletLayer.createAndGroupLayer(ob, this);
            }
            if (ob.isLine()) {
                ob.getObservers().filter(ob => ob instanceof LeafletLayer)[0].getLayer().bringToBack();
            }
            if (ob.isChild()) {
                const parentKey = this.observableGraph.getKey(ob.getProperty('parent'), ob.getProperty('treeKey', 'meta'));
                const parentChildLineFeature = this.observableGraph.getParentChildLineFeature(parentKey, key);
                this.observableGraph.insertObservable(parentChildLineFeature);
                LeafletLayer.createAndGroupLayer(parentChildLineFeature, this);
                parentChildLineFeature.getObservers().filter(ob => ob instanceof LeafletLayer)[0].getLayer().bringToBack();
            }
        });
    }

    /**
     * - Delete the property with the matching namespace and property key from all of the ObservableInterface instances
     * @param {Array} observables - an array of ObservableInterface instances from which the property should be deleted
     * @param {string} propertyKey - the property key of the property that is in the observables
     * @param {string} [namespace='treeProps'] - the namespace of the property that is in the observables
     * @returns {undefined}
     */
    deleteProperty(observables, propertyKey, namespace='treeProps') {
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
        const observablesCopy = [...observables];
        for (const ob of observablesCopy) {
            ob.deleteObservable();
        }
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
                if (ob.isComponentFeature()) {
                    // - Do nothing. There's no need to set the coordinates of a component line that hasn't been inserted yet
                } else {
                    const fromKey = this.observableGraph.getKey(ob.getProperty('from'), obKey);
                    const toKey = this.observableGraph.getKey(ob.getProperty('to'), obKey);
                    const { sourceLat, sourceLon, targetLat, targetLon } = this.observableGraph.getLineLatLon(fromKey, toKey);
                    ob.setCoordinates([[sourceLon, sourceLat], [targetLon, targetLat]]);
                }
            } 
            if (propertyKey === 'parent') {
                if (ob.isComponentFeature()) {
                    // - Do nothing. Child components don't yet have a parent-child line
                } else {
                    const fromKey = this.observableGraph.getKey(ob.getProperty('parent'), obKey);
                    const toKey = obKey;
                    const { sourceLat, sourceLon, targetLat, targetLon } = this.observableGraph.getLineLatLon(fromKey, toKey);
                    const parentChildLine = this.observableGraph.getParentChildLine(obKey);
                    parentChildLine.setCoordinates([[sourceLon, sourceLat], [targetLon, targetLat]]);
                }
            } 
        });
        // - <FeatureGraph>.handleUpdatedProperty() no longer marks nodes as visited, so I don't need to undo that here
        //this.observableGraph.markNodesAsUnvisited();
    }
    
    // ********************
    // ** Public methods **
    // ********************

    /**
     * - Send an AJAX request to the server
     * @param {Feature} observable - the ObservableInterface instance to submit
     * @param {ModalFeatureModal} modal
     * @param {HTMLButtonElement} submitButton - a button to enable/disable depending on the state of the operation
     * @param {boolean} reload - whether or not to reload the page. This is necessary when chaining multiple operations together (e.g. every rename
     * operation must be preceeded by a save operation)
     * @returns {undefined}
     */
    async submitFeature(observable, modal, submitButton=null, reload=true) {
        if (!(observable instanceof Feature)) {
            throw TypeError('"observable" argument must be instanceof Feature.');
        }
        if (!(modal instanceof Modal)) {
            throw TypeError('"modal" argument must be instanceof Modal.');
        }
        if (!(submitButton instanceof HTMLButtonElement) && !(submitButton === null)) {
            throw TypeError('"submitButton" argument must be instanceof HTMLButtonElement or null');
        }
        if (typeof reload !== 'boolean') {
            throw TypeError('"reload" argument must be a boolean.');
        }
        if (submitButton !== null) {
            submitButton.disabled = true;
        }
        const modalInsert = document.getElementById('modalInsert');
        let data;
        if (observable.hasProperty('fileExistsUrl', 'urlProps')) {
            try {
                data = await $.ajax({
                    type: observable.getProperty('fileExistsUrl', 'urlProps').method,
                    url: observable.getProperty('fileExistsUrl', 'urlProps').url
                });
                switch (observable.getProperty('treeKey', 'meta')) {
                    case 'modal:rename':
                    case 'modal:opendss':
                    case 'modal:windmil':
                    case 'modal:cymdist':
                    case 'modal:gridlabd':
                        if (data.exists === true) {
                            modal.showProgress(false, 'You already have a feeder with that name. Please choose a different name', ['caution']);
                            if (submitButton !== null) {
                                submitButton.disabled = false;
                            }
                            modalInsert.addEventListener('click', hideModalInsert);
                            return;
                        }
                        break;
                    case 'modal:loadFeeder':
                        // - I do this to assert that data.exists is equal to true, not that it is truthy. There's an important difference
                        if (data.exists === true) {
                            modal.showProgress(true, 'Loading feeder from the server...', ['caution']);
                            break;
                        }
                    default:
                        if (data.exists !== true) {
                            modal.showProgress(false, 'This feeder no longer exists on the server, so the operation failed. Please save and try again.', ['caution']);
                            if (submitButton !== null) {
                                submitButton.disabled = false;
                            }
                            modalInsert.addEventListener('click', hideModalInsert);
                        }
                }
            } catch {
                modal.showProgress(false, 'The server raised an internal exception during the operation. Please save before trying again.', ['caution']); 
                if (submitButton !== null) {
                    submitButton.disabled = false;
                }
                modalInsert.addEventListener('click', hideModalInsert);
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
            modal.showProgress(false, 'The server raised an internal exception during the operation. Please save before trying again.', ['caution']); 
            if (submitButton !== null) {
                submitButton.disabled = false;
            }
            modalInsert.addEventListener('click', hideModalInsert);
            return;
        }
        const that = this;
        // - We don't want to poll the server. Just reload the page.
        if (!observable.hasProperty('pollUrl', 'urlProps')) {
            if (data === 'Failure') {
                modal.showProgress(false, 'The server operation failed.', ['caution']);
                if (submitButton !== null) {
                    submitButton.disabled = false;
                }
                modalInsert.addEventListener('click', hideModalInsert);
            } else {
                if (reload) {
                    that.#reloadPage();
                } else {
                    document.getElementById('modalInsert').classList.remove('visible');
                    if (submitButton !== null) {
                        submitButton.disabled = false;
                    }
                    modalInsert.addEventListener('click', hideModalInsert);
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
                            if (submitButton !== null) {
                                submitButton.disabled = false;
                            }
                            modalInsert.addEventListener('click', hideModalInsert);
                        }
                    } else if (data.exists === undefined) {
                        clearInterval(intervalId);
                        if (submitButton !== null) {
                            submitButton.disabled = false;
                        }
                        modalInsert.addEventListener('click', hideModalInsert);
                        if (data === 'milError') {
                            modal.showProgress(false, 'The .std and .seq files used were incorrectly formatted. Please save before trying again.', ['caution']);
                        } else if (data === 'dssError') {
                            modal.showProgress(false, 'The .dss file used was incorrectly formatted. Please save before trying again.', ['caution']);
                        } else if (data === 'cymeError') {
                            modal.showProgress(false, 'The .mdb file used was incorrectly formatted. Please save before trying again.', ['caution']);
                        } else if (data === 'glmError') {
                            modal.showProgress(false, 'The .glm file used was incorrectly formatted. Please save before trying again.', ['caution']);
                        } else if (data === 'amiError') {
                            modal.showProgress(false, 'The AMI file used was incorrectly formatted. Please save before trying again.', ['caution']);
                        } else if (data === 'anonymizeError') {
                            modal.showProgress(false, 'The anonymization process failed. Please save before trying again.', ['caution']);
                        } else {
                            if (!data.endsWith('.')) {
                                data += '.';
                            }
                            data += ' Please save before trying again.';
                            modal.showProgress(false, data, ['caution']);
                        }
                    // - The server process is ongoing, so let setInterval keep going
                    } else if (data.exists === true) {
                        // - Do nothing
                    } else {
                        if (submitButton !== null) {
                            submitButton.disabled = false;
                        }
                        modalInsert.addEventListener('click', hideModalInsert);
                        throw Error('Undefined value returned by server during the polling process.');
                    }
                } catch {
                    clearInterval(intervalId);
                    modal.showProgress(false, 'The server raised an internal exception during the operation. Please save before trying again.', ['caution']);
                    if (submitButton !== null) {
                        submitButton.disabled = false;
                    }
                    modalInsert.addEventListener('click', hideModalInsert);
                    return;
                }
            }, 10000);
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