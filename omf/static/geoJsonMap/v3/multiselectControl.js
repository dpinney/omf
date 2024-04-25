export { MultiselectControlClass };
import { FeatureController } from './featureController.js'
import { FeatureEditModal } from './featureEditModal.js';
import { LeafletLayer } from './leafletLayer.js';

/**
 * - Inherited methods: getPosition(), setPosition(), getContainer(), addTo(), remove()
 * - Extension methods: onAdd(), onRemove()
 */
const MultiselectControlClass = L.Control.extend({
    // - Set default values for L.Control options
    options: {
        position: 'topleft' // - Position the control in the top left corner by default
    },
    /**
     * @param {FeatureController} controller - a ControllerInterface instance 
     * @param {Object} options - a plain JavaScript object containing L.Control option values that should override the default values
     * @returns {undefined}
     */
    initialize: function(controller, options=null) {
        if (!(controller instanceof FeatureController)) {
            throw TypeError('"controller" argument must be instanceof FeatureController.');
        }
        this._controller = controller;
        this._div = null;
        this._on = null;
        this._mousedown = null;
        this._mousemove = null;
        this._mouseup = null;
        this._selectedObservables = [];
        if (options !== null) {
            L.setOptions(this, options);
        }
    },
    onAdd: function(map) {
        this._onAdd(map);
        return this._div;
    },
    onRemove: function(map) {
        // - Don't do anything. The MultiselectControl will never be removed from the map
    },
    _onAdd(map) {
        this._div = document.createElement('div');
        this._div.textContent = 'MultiselectControlClass';
        this._div.style.background = 'white';
        this._on = false;
        this._div.addEventListener('click', () => {
            if (!this._on) {
                this._on = true;
                this._activate(map);
            } else {
                this._on = false;
                this._deactivate(map);
            }
        });
    },
    _activate(map) {
        this._div.style.background = 'yellow';
        map.dragging.disable();
        const bounds = {};
        let rectangle = null;
        let mouseIsDown = false;
        this._mousedown = function(e) {
            if (rectangle !== null) {
                rectangle.remove();
            }
            bounds.start = e.latlng;
            mouseIsDown = true;
        };
        map.on('mousedown', this._mousedown);
        this._mousemove = function(e) {
            if (mouseIsDown) {
                if (rectangle !== null) {
                    rectangle.remove();
                }
                bounds.end = e.latlng;
                rectangle = L.rectangle([bounds.start, bounds.end], {color: "#ff7800", weight: 1});
                rectangle.addTo(map);
            }
        };
        map.on('mousemove', this._mousemove);
        this._mouseup = (e) => {
            if (rectangle !== null) {
                rectangle.remove();
            }
            bounds.end = e.latlng;
            if ((bounds.start.lat !== bounds.end.lat) || (bounds.start.lng !== bounds.end.lng)) {
                //rectangle = L.rectangle([bounds.start, bounds.end], {color: "#ff7800", weight: 1});
                //rectangle.addTo(map);
                const observables = this._controller.observableGraph.getObservables((ob) => {
                    // - This check is slow, but I can't think of a better way to do it right now
                    if (ob.hasCoordinates()) {
                        const layer = Object.values(ob.getObservers().filter(o => o instanceof LeafletLayer)[0].getLayer()._layers)[0];
                        if (LeafletLayer.map.hasLayer(layer)) {
                            if (ob.isNode()) {
                                return this._pointIsBounded(bounds, ob.getCoordinates());
                            } else if (ob.isLine()) {
                                return this._pointIsBounded(bounds, ob.getCoordinates()[0]) || this._pointIsBounded(bounds, ob.getCoordinates()[1]); 
                            } else {
                                throw Error('Multiselect control only works with nodes or lines with coordinates.');
                            }
                        }
                        return false;
                    }
                });
                if (observables.length > 0) {
                    const featureEditModal = new FeatureEditModal(observables, this._controller);
                    const div = featureEditModal.getDOMElement();
                    div.classList.add('outerModal');
                    $(div).draggable();
                    document.getElementById('multiselectInsert').replaceChildren(div);
                    this._selectedObservables = observables;
                    for (const ob of this._selectedObservables) {
                        //const svg = Object.values(ob.getObservers().filter(o => o instanceof LeafletLayer)[0].getLayer()._layers)[0]._icon.children[0];
                        const svg = Object.values(ob.getObservers().filter(o => o instanceof LeafletLayer)[0].getLayer()._layers)[0];
                        console.log(svg);
                        //svg.classList.add('highlighted');
                    }
                } else {
                    document.getElementById('multiselectInsert').replaceChildren();
                    // ?
                    this._selectedObservables = [];
                }
            }
            mouseIsDown = false;
        };
        map.on('mouseup', this._mouseup);
    },
    _deactivate(map) {
        document.getElementById('multiselectInsert').replaceChildren();
        this._div.style.background = 'white';
        map.dragging.enable();
        map.off('mousedown', this._mousedown);
        map.off('mousemove', this._mousemove);
        map.off('mouseup', this._mouseup);
        // ?
        this._selectedObservables = [];
    },
    /**
     * @param {Object} bounds - a bounds object
     * @param {Array} coordinates - coordinates with [<lon>, <lat>] format
     */
    _pointIsBounded(bounds, coordinates) {
        let latIsBounded = false;
        let lngIsBounded = false;
        if (bounds.start.lat < bounds.end.lat && coordinates[1] >= bounds.start.lat && coordinates[1] <= bounds.end.lat) {
            latIsBounded = true;
        } else if (bounds.start.lat > bounds.end.lat && coordinates[1] <= bounds.start.lat && coordinates[1] >= bounds.end.lat) {
            latIsBounded = true;
        }
        if (bounds.start.lng < bounds.end.lng && coordinates[0] >= bounds.start.lng && coordinates[0] <= bounds.end.lng) {
            lngIsBounded = true;
        } else if (bounds.start.lng > bounds.end.lng && coordinates[0] <= bounds.start.lng && coordinates[0] >= bounds.end.lng) {
            lngIsBounded = true;
        }
        return latIsBounded && lngIsBounded;
    }
});