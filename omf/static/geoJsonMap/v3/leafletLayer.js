export { LeafletLayer };
import { Feature } from './feature.js';
import { FeatureController } from "./featureController.js";
import { FeatureEditModal } from './featureEditModal.js';

/**
 * - Each LeafletLayer instance is a view in the MVC pattern. Each observes an ObservableInterface instance, which is part of the model in the MVC
 *   pattern. An ObservableInterface instance does NOT observe a LeafletLayer instance. Instead, a LeafletLayer instance uses the controller to pass
 *   its own changes to the underlying ObservableInterface instance
 */
class LeafletLayer { // implements ObserverInterface
    #controller;    // ControllerInterface instance
    #layer;         // - Leaflet layer
    #observable;    // - ObservableInterface instance
    static lineLayers = L.featureGroup();
    static map;
    static nodeLayers = L.featureGroup();
    static parentChildLineLayers = L.featureGroup();

    /**
     * @param {Feature} observable - an ObservableInterface instance
     * @param {FeatureController} controller - a ControllerInterface instance
     * @returns {undefined}
     */
    constructor(observable, controller) {
        if (!(observable instanceof Feature)) {
            throw TypeError('"observable" argument must be instance of Feature.');
        }
        if (!(controller instanceof FeatureController)) {
            throw Error('"controller" argument must be an instance of FeatureController.');
        }
        this.#controller = controller;
        this.#observable = observable;
        // - Here, the first observer is added to every visible feature
        this.#observable.registerObserver(this);
        const feature = {'type': 'Feature', 'geometry': {}};
        if (this.#observable.isNode()) {
            feature.geometry.type = 'Point';
        } else if (this.#observable.isLine()) {
            feature.geometry.type = 'LineString';
        }
        feature.geometry.coordinates = structuredClone(this.#observable.getCoordinates());
        feature.properties = structuredClone(this.#observable.getProperties('meta'));
        // - L.geoJSON() returns an instance of https://leafletjs.com/reference.html#geojson
        //  - A GeoJSON object extends FeatureGroup which extends LayerGroup which extends Layer
        //  - Therefore, a GeoJSON object can contain one or more layers
        //  - Access the underlying layer(s) with <GeoJSON>._layers, which is a map (i.e. object) that maps layer ids to actual layer objects
        this.#layer = L.geoJSON(feature, {
            pointToLayer: this.#pointToLayer.bind(this), 
            style: this.#styleLines.bind(this)
        });
        if (this.#observable.isNode()) {
            LeafletLayer.nodeLayers.addLayer(this.#layer);
        } else if (this.#observable.isLine()) {
            if (this.#observable.isParentChildLine()) {
                LeafletLayer.parentChildLineLayers.addLayer(this.#layer);
            } else {
                LeafletLayer.lineLayers.addLayer(this.#layer);
            }
        } else {
            // - TODO: get polygons working!
            throw Error('"observable" argument was not a node or a line.');
        }
        const layer = Object.values(this.#layer._layers)[0];
        let featureEditModal;
        layer.bindPopup(() => {
            featureEditModal = new FeatureEditModal([this.#observable], controller);
            return featureEditModal.getDOMElement();
        });
        this.#layer.addEventListener('popupclose', () => this.#observable.removeObserver(featureEditModal));
    }

    // *******************************
    // ** ObserverInterface methods ** 
    // *******************************

    /**
     * - Remove this ObserverInterface instance (i.e. "this") from the ObservableInterface instance (i.e. "observable") that has been deleted, and
     *   perform other actions as needed
     *  - E.g. delete this layer if its underlying feature was deleted
     * @param {Object} observable - an instance of ObservableInterface that this Observer is observing
     * @returns {undefined}
     */
    handleDeletedObservable(observable) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        observable.removeObserver(this);
        const layer = Object.values(this.#layer._layers)[0]; 
        // - Why does this also delete the FeatureEditModal in the pop-up? I don't know but I have to deal with it
        layer.remove();
    }

    /**
     * - Update this ObserverInterface instance (i.e. "this") based on the coordinates of the ObservableInterface instance (i.e. "observable") that
     *   have just changed and perform other actions as needed
     *  - E.g. update this layer's coordinates if the coordinates of the underlying feature changed
     * @param {Object} observable - an instance of ObservableInterface that this Observer is observing
     * @param {Array} oldCoordinates - the old coordinates of the observable prior to the change in coordinates
     * @param {Array} visited - an array of ObserverInterface instances. It's required to prevent infinite recursion caused by Observers updating each
     * other
     * @returns {undefined}
     */
    handleUpdatedCoordinates(observable, oldCoordinates) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!(oldCoordinates instanceof Array)) {
            throw TypeError('"oldCoordinates" argument must be an array.')
        }
        const coordinates = observable.getCoordinates();
        if (observable.isNode()) {
            // - Object.values(this.<GeoJSON>.<mapping object>)[0] === <Layer>
            Object.values(this.#layer._layers)[0].setLatLng([coordinates[1], coordinates[0]]);
        } else {
            Object.values(this.#layer._layers)[0].setLatLngs([[coordinates[0][1], coordinates[0][0]],[coordinates[1][1], coordinates[1][0]]]);
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
        // - Change colors?
    }

    // ********************
    // ** Public methods **
    // ********************

    /**
     * @returns {GeoJSON}
     */
    getLayer() {
        return this.#layer;
    }

    // *********************
    // ** Private methods ** 
    // *********************

    #pointToLayer() {
        let svgClass = 'gray';
        // - TODO: verify pointColor works
        if (this.#observable.hasProperty('pointColor')) {
            svgClass = this.#observable.getProperty('pointColor');
        } else if (this.#observable.hasProperty('object')) {
            const object = this.#observable.getProperty('object');
            if (object === 'capacitor') {
                svgClass = 'purple';
            }
            if (object === 'generator') {
                svgClass = 'red';
            }
            if (object == 'load') {
                svgClass = 'blue';
            }
        }
        const svgIcon = L.divIcon({
            html: `<svg width="16" height="16" viewBox="-2 -2 20 20">
                <circle cx="8" cy="8" r="8" stroke="black"/>
                </svg>`,
            className: `svg--icon-${svgClass}`,
            iconSize: [16, 16],
          });
        // - TODO: fix uneven panning speed
        const coordinates = this.#observable.getCoordinates();
        const marker = L.marker(
            [coordinates[1], coordinates[0]], {
            autoPan: true,
            draggable: true,
            icon: svgIcon 
        });
        const that = this;
        marker.on('drag', function(e) {
            const {lat, lng} = e.target.getLatLng();
            that.#controller.setCoordinates([that.#observable], [lng, lat]);
        });
        return marker;
    }

    #styleLines() {
        if (this.#observable.isLine()) {
            if (this.#observable.hasProperty('edgeColor')) {
                return {
                    color: this.#observable.getProperty('edgeColor')
                }
            } else if (this.#observable.hasProperty('object') && this.#observable.getProperty('object') === 'transformer') {
                return {
                    color: 'orange'
                }
            } else if (this.#observable.hasProperty('object') && this.#observable.getProperty('object') === 'regulator') {
                return {
                    color: 'red'
                }
            } else if (this.#observable.hasProperty('object') && this.#observable.getProperty('object') === 'underground_line') {
                return {
                    color: 'gray'
                }
            } else if (this.#observable.isParentChildLine()) {
                return {
                    color: 'black',
                    // - Dashed lines are only useful if the child is reasonably far from the parent, so I need other differences in style
                    dashArray: '.5 10',
                    lineCap: 'square',
                    weight: '3'
                }
            } else {
                return {
                    color: 'black'
                }
            }
        } else if (this.#observable.isPolygon()) {
            return {
                color: 'blue'
            }
        }
    }
}