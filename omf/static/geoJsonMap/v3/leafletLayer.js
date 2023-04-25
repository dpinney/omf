export { LeafletLayer };
import { FeatureController } from "./featureController.js";
import { TreeFeatureModal } from './treeFeatureModal.js';

/**
 * - Each LeafletLayer instance (i.e. the view in the MVC pattern) observes an ObservableInterface instance (i.e. the model in the MVC pattern). An
 *   ObservableInterface instance does NOT observe a LeafletLayer instance. Instead, a LeafletLayer instance uses the controller to pass its own
 *   changes to the underlying ObservableInterface instance
 */
class LeafletLayer { // implements ObserverInterface
    layer;          // Leaflet layer
    #controller;    // ControllerInterface instance
    static nodeLayers = L.featureGroup();
    static lineLayers = L.featureGroup();
    static parentChildLineLayers = L.featureGroup();
    static map;

    /**
     * @param {FeatureController} controller - a ControllerInterface instance. This ControllerInterface instance has a reference to an
     * ObservableInterface instance that can be used to register this LeafletLayer as an observer of an ObservableInterface instance
     */
    constructor(controller) {
        if (!(controller instanceof FeatureController)) {
            throw Error('"controller" argument must be an instance of FeatureController');
        }
        this.#controller = controller;
        const observables = this.#controller.getObservables();
        if (observables.length !== 1) {
            throw Error('Each LeafletLayer instance should observe exactly one Feature');
        }
        const observable = observables[0];
        // - Here, the first observer is added to every visible feature
        observable.registerObserver(this);
        // - The Leaflet layer itself will contain a reference to a GeoJSON feature object that isn't part of the data model (i.e. it's a GeoJSON
        //   object that won't be updated or referenced at all). That's fine because I won't be working directly with the Leaflet layer. I'll be
        //   working with my own layer that actually will update the data model
        const feature = {'type': 'Feature', 'geometry': {}};
        if (observable.isNode()) {
            feature.geometry.type = 'Point';
        } else if (observable.isLine()) {
            feature.geometry.type = 'LineString';
        }
        feature.geometry.coordinates = observable.getCoordinates();
        feature.properties = observable.getProperties('meta');
        // - L.geoJSON() returns an instance of https://leafletjs.com/reference.html#geojson
        //  - A GeoJSON object extends FeatureGroup which extends LayerGroup which extends Layer
        //  - Therefore, a GeoJSON object can contain one or more layers
        //  - Access the underlying layer(s) with <GeoJSON>._layers, which is a map (i.e. object) that maps layer ids to actual layer objects
        this.layer = L.geoJSON(feature, {
            pointToLayer: this.#pointToLayer.bind(this), 
            style: this.#styleLines.bind(this)
        });
        if (observable.isNode()) {
            LeafletLayer.nodeLayers.addLayer(this.layer);
        } else if (observable.isLine()) {
            if (observable.isParentChildLine()) {
                LeafletLayer.parentChildLineLayers.addLayer(this.layer);
            } else {
                LeafletLayer.lineLayers.addLayer(this.layer);
            }
        } else {
            throw Error('"observable" was not a node or a line.');
        }
        const layer = Object.values(this.layer._layers)[0];
        let treeFeatureModal;
        layer.bindPopup(() => {
            // - Add temporary fifth observer to visible ObservableInterface instances
            treeFeatureModal = new TreeFeatureModal(this.#controller);
            return treeFeatureModal.getDOMElement();
        });
        this.layer.addEventListener('popupclose', () => observable.removeObserver(treeFeatureModal));
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
        const layer = Object.values(this.layer._layers)[0]; 
        layer.remove();
    }

    // ** Coordinate-related methods **

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
            Object.values(this.layer._layers)[0].setLatLng([coordinates[1], coordinates[0]]);
        } else {
            Object.values(this.layer._layers)[0].setLatLngs([[coordinates[0][1], coordinates[0][0]],[coordinates[1][1], coordinates[1][0]]]);
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

    // *******************************
    // ** Private methods ** 
    // *******************************

    #pointToLayer() {
        let svgClass = 'gray';
        const observable = this.#controller.getObservables()[0];
        // - TODO: verify pointColor works
        if (observable.hasProperty('pointColor')) {
            svgClass = observable.getProperty('pointColor');
        } else if (observable.hasProperty('object')) {
            const object = observable.getProperty('object');
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
        const coordinates = observable.getCoordinates();
        const marker = L.marker(
            [coordinates[1], coordinates[0]], {
            autoPan: true,
            draggable: true,
            icon: svgIcon 
        });
        const that = this;
        marker.on('drag', function(e) {
            const {lat, lng} = e.target.getLatLng();
            that.#controller.setCoordinates([lng, lat]);
        });
        return marker;
    }

    #styleLines() {
        const observable = this.#controller.getObservables()[0];
        if (observable.isLine()) {
            if (observable.hasProperty('edgeColor')) {
                return {
                    color: observable.getProperty('edgeColor')
                }
            } else if (observable.hasProperty('object') && observable.getProperty('object') === 'transformer') {
                return {
                    color: 'orange'
                }
            } else if (observable.hasProperty('object') && observable.getProperty('object') === 'regulator') {
                return {
                    color: 'red'
                }
            } else if (observable.hasProperty('object') && observable.getProperty('object') === 'underground_line') {
                return {
                    color: 'gray'
                }
            } else if (observable.isParentChildLine()) {
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
        } else if (observable.isPolygon()) {
            return {
                color: 'blue'
            }
        }
    }
}