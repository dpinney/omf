export { GeojsonModal };
import { Feature, UnsupportedOperationError } from './feature.js';
import { FeatureController } from './featureController.js';
import { LeafletLayer } from './leafletLayer.js';
import { Modal } from './modal.js';

class GeojsonModal { // implements ModalInterface, ObserverInterface
    #controller;            // - ControllerInterface instance
    #filenameToLayerGroup;  // - Container for LayerGroups
    #modal;                 // - Modal instance
    #observables;           // - An array of ObservableInterface instances
    #removed;               // - Whether this ColorModal instance has already been deleted

    /**
     * @param {Array} observables - an array of ObservableInterface instances 
     * @param {FeatureController} controller - a ControllerInterface instance
     */
    constructor(observables, controller) {
        if (!(observables instanceof Array)) {
            throw TypeError('"observables" argumnet must be an Array.');
        }
        if (!(controller instanceof FeatureController)) {
            throw Error('"controller" argument must be instanceof FeatureController.');
        }
        this.#controller = controller;
        this.#filenameToLayerGroup = {};
        this.#modal = null;
        this.#observables = observables;
        this.#observables.forEach(ob => ob.registerObserver(this));
        this.#removed = false;
        this.renderContent();
        this.refreshContent();
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
                this.#updateLayerGroups();
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
        this.#updateLayerGroups();
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
        this.#updateLayerGroups();
        this.refreshContent();
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

    // - Go through the attachments object and display existing GeoJSON files

    /**
     * @returns {undefined}
     */
    refreshContent() {
        const fileListModal = new Modal();
        fileListModal.addStyleClasses(['colorModal'], 'divElement');
        if (Object.values(this.#filenameToLayerGroup).length > 0) {
            fileListModal.insertTHeadRow(['Filename', 'Show GeoJSON on Page Load']);
            fileListModal.addStyleClasses(['centeredTable'], 'tableElement');
        }
        const that = this;
        const attachments = this.#controller.observableGraph.getObservable('omd').getProperty('attachments', 'meta');
        for (const filename of Object.keys(this.#filenameToLayerGroup)) {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'displayOnLoad';
            checkbox.addEventListener('change', function() {
                for (const [fname, obj] of Object.entries(attachments.geojsonFiles)) {
                    if (fname === filename) {
                        if (this.checked) {
                            obj.displayOnLoad = true;
                        } else {
                            delete obj.displayOnLoad
                        }
                    } else {
                        // - Do nothing
                    }
                }
            });
            if (attachments.geojsonFiles[filename].displayOnLoad) {
                checkbox.checked = true;
            }
            const removeButton = document.createElement('button');
            removeButton.classList.add('horizontalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex', 'fullWidth', 'delete');
            const span = document.createElement('span');
            span.textContent = 'Remove';
            removeButton.appendChild(span);
            removeButton.addEventListener('click', function() {
                if (attachments.hasOwnProperty('geojsonFiles')) {
                    delete attachments.geojsonFiles[filename];
                    that.#filenameToLayerGroup[filename].layerGroup.remove();
                    that.#filenameToLayerGroup[filename].layerControl.remove();
                    delete that.#filenameToLayerGroup[filename];
                    if (Object.keys(attachments.geojsonFiles).length === 0) {
                        delete attachments.geojsonFiles;
                    }
                    that.refreshContent();
                }
            });
            fileListModal.insertTBodyRow([filename, checkbox, removeButton]);
        }
        const containerElement = this.#modal.divElement.getElementsByClassName('div--modalElementContainer')[0];
        const oldModal = containerElement.getElementsByClassName('js-div--modal');
        if (oldModal.length === 0) {
            containerElement.prepend(fileListModal.divElement);
        } else {
            oldModal[0].replaceWith(fileListModal.divElement);
        }
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
        modal.addStyleClasses(['outerModal', 'fitContent'], 'divElement');
        modal.setTitle('Add GeoJSON');
        modal.addStyleClasses(['horizontalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex'], 'titleElement');
        const geojsonInput = document.createElement('input');
        geojsonInput.type = 'file';
        geojsonInput.accept = '.geojson';
        geojsonInput.required = true;
        geojsonInput.id = 'geojsonInput';
        const that = this;
        const attachments = this.#controller.observableGraph.getObservable('omd').getProperty('attachments', 'meta');
        geojsonInput.addEventListener('change', async function() {
            const file = this.files[0];
            const text = await file.text();
            let featureCollection;
            try {
                featureCollection = JSON.parse(text);
                that.#modal.setBanner('', ['hidden']);
                if (!attachments.hasOwnProperty('geojsonFiles')) {
                    attachments.geojsonFiles = {};
                }
                attachments.geojsonFiles[file.name] = {
                    json: JSON.stringify(featureCollection)
                }
                that.#updateLayerGroups();
                that.refreshContent();
            } catch (e) {
                that.#modal.showProgress(false, `There was an error "${e.message}" when parsing the JSON file "${file.name}". Please double-check the JSON formatting.`, ['caution']);
            }
        });
        const geojsonLabel = document.createElement('label');
        geojsonLabel.htmlFor = 'geojsonInput';
        geojsonLabel.innerHTML = 'Add a file containing a GeoJSON feature collection (.geojson)';
        modal.insertTBodyRow([geojsonLabel, geojsonInput]);
        modal.addStyleClasses(['centeredTable'], 'tableElement');
        // - Append an empty div so the containerElement isn't null
        const submitDiv = document.createElement('div');
        modal.insertElement(submitDiv);
        if (this.#modal === null) {
            this.#modal = modal;
        }
        if (document.body.contains(this.#modal.divElement)) {
            this.#modal.divElement.replaceWith(modal.divElement);
            this.#modal = modal;
        }
        this.#updateLayerGroups(true);
    }

    // ********************
    // ** Public methods **
    // ********************

    // *********************
    // ** Private methods **
    // *********************

    /**
     * - Iterate through the attachments.geojsonFiles object. For each file, do the following:
     *  - Parse the json string into a GeoJSON featureCollection
     *  - Iterate through the features of the feature collection and create Feature instances and LeafletLayer instances
     *  - Add the LeafletLayer instances to a new LayerGroup that has the same name as the file
     *  - Do not add the Feature instances to a FeatureGraph (at least, not yet)
     *  - Add the LayerGroup to the map
     *      - In order to not keep adding the same features over and over again, here's what I'll do:
     *          - I consider filenames to be unique identifiers for a set of Features/LeafletLayers
     *          - Have a "geojsonFiles" object as a property of this GeojsonModal. Keys are filenames and values are LayerGroup instances. If a file
     *            is deleted, modify the attachments object, remove the LayerGroup from the map, and delete the LayerGroup from the geojsonFiles
     *            object. If a file is added, modify the attachments object, create a new LayerGroup object, add the LeafletLayers to the LayerGroup,
     *            overwrite the geojsonFiles object with the new layer group (and remove the matching LayerGroup from the map if there was one), and
     *            add the new LayerGroup to the map
     * - In this way, the attachments object will be synchronized with the geojsonFiles object. The user will be able to show/hide the LayerGroups via
     *   the normal Leaflet controls
     * - When is this function called? On renderContent(), in response to a file upload, and if a GeoJSON file is edited in the attachments modal
     * @param {boolean} renderContent - whether this function was called on the initial renderContent() call
     * @returns {undefined}
     */
    #updateLayerGroups(renderContent=false) {
        const attachments = this.#controller.observableGraph.getObservable('omd').getProperty('attachments', 'meta');
        if (attachments.hasOwnProperty('geojsonFiles')) {
            const that = this;
            for (const [filename, obj] of Object.entries(attachments.geojsonFiles)) {
                const featureCollection = JSON.parse(obj.json);
                const layerGroup = L.featureGroup();
                featureCollection.features.map(f => new Feature(f)).map(f => new LeafletLayer(f, that.#controller)).forEach(ll => layerGroup.addLayer(ll.getLayer()));
                const layerControl = L.control.layers(null, {[filename]: layerGroup}, { position: 'topleft', collapsed: false });
                if (this.#filenameToLayerGroup.hasOwnProperty(filename)) {
                    this.#filenameToLayerGroup[filename].layerGroup.remove();
                    this.#filenameToLayerGroup[filename].layerControl.remove();
                }
                this.#filenameToLayerGroup[filename] = {
                    layerGroup: layerGroup,
                    layerControl: layerControl    
                };
                layerControl.addTo(LeafletLayer.map);
                if (renderContent) {
                    if (obj.displayOnLoad) {
                        layerGroup.addTo(LeafletLayer.map);
                    }
                } else {
                    layerGroup.addTo(LeafletLayer.map);
                }
            }
        }
    }
}