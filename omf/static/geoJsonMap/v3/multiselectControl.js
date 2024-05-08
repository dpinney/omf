export { MultiselectControlClass };
import { FeatureController } from './featureController.js'
import { FeatureEditModal } from './featureEditModal.js';
import { LeafletLayer } from './leafletLayer.js';

// - If we need more coloring functionality in the future, I should move all coloring-related code into the colormodal and create an instance of the
//   color modal here

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
            throw TypeError('The "controller" argument must be instanceof FeatureController.');
        }
        this._controller = controller;
        // - Create div
        this._div = L.DomUtil.create('div', 'leaflet-bar');
        this._div.classList.add('leaflet-customControlDiv');
        L.DomEvent.disableClickPropagation(this._div);
        this._div.appendChild(this._getSvg());
        // - Add a tooltip
        this._div.title = '- The multiselect tool allows you to draw a box on the map to select elements\n- Click this button or press shift to enable\n- While enabled, hold and drag the mouse to select elements\n- Click this button or press shift or escape to disable';
        // - Attach listeners
        this._on = false;
        this._div.addEventListener('click', () => {
            if (!this._on) {
                this._on = true;
                this._activate(LeafletLayer.map);
            } else {
                this._on = false;
                this._deactivate(LeafletLayer.map);
            }
        });
        this._mousedown = null;
        this._mousemove = null;
        this._mouseup = null;
        this._selectedObservables = [];
        this._modal = null;
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
        map.on('keyup', (e) => {
            if (e.originalEvent.key === 'Shift' ) {
                if (!this._on) {
                    this._on = true;
                    this._activate(map);
                } else {
                    this._on = false;
                    this._deactivate(map);
                }
            }
        });
        map.on('keydown', (e) => {
            if (e.originalEvent.key === 'Escape') {
                this._on = false;
                this._deactivate(map);
            }
        });
    },
    _activate(map) {
        this._div.style.border = '2px solid #7FFF00';
        map.dragging.disable();
        document.getElementById('map').style.cursor = 'crosshair';
        const bounds = {};
        let rectangle = null;
        let mouseIsDown = false;
        this._mousedown = (e) => {
            // - Disable map dragging again just in case a marker was dragged which would have reenabled map dragging
            map.dragging.disable();
            this._removeHighlights();
            if (rectangle !== null) {
                rectangle.remove();
            }
            bounds.start = e.latlng;
            mouseIsDown = true;
        };
        map.on('mousedown', this._mousedown);
        this._mousemove = (e) => {
            if (mouseIsDown) {
                if (rectangle !== null) {
                    rectangle.remove();
                }
                bounds.end = e.latlng;
                rectangle = L.rectangle([bounds.start, bounds.end], {color: "#7FFF00", weight: 1});
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
                // - Highlight new paths
                const observables = this._controller.observableGraph.getObservables((ob) => {
                    // - This check is slow, but I can't think of a better way to do it right now
                    if (ob.hasCoordinates()) {
                        const layer = Object.values(ob.getObservers().filter(o => o instanceof LeafletLayer)[0].getLayer()._layers)[0];
                        if (map.hasLayer(layer)) {
                            if (ob.isNode()) {
                                return this._pointIsBounded(bounds, ob.getCoordinates());
                            } else if (ob.isLine()) {
                                const c = ob.getCoordinates();
                                return this._pointIsBounded(bounds, ob.getCoordinates()[0]) ||
                                    this._pointIsBounded(bounds, ob.getCoordinates()[1]) ||
                                    this._pointIsBounded(bounds, [(c[0][0] + c[1][0]) / 2, (c[0][1] + c[1][1]) / 2])
                            } else {
                                throw Error('Multiselect control only works with nodes or lines with coordinates.');
                            }
                        }
                        return false;
                    }
                });
                if (observables.length > 0) {
                    this._selectedObservables = observables;
                    for (const ob of this._selectedObservables) {
                        const path = Object.values(ob.getObservers().filter(o => o instanceof LeafletLayer)[0].getLayer()._layers)[0];
                        if (ob.isNode()) {
                            path.setStyle({
                                color: '#7FFF00'
                            });
                        } else if (ob.isLine()) {
                            if (!path.options.hasOwnProperty('originalColor')) {
                                path.options.originalColor = path.options.color;
                            }
                            path.setStyle({
                                color: '#7FFF00'
                            });
                        }
                    }
                    this._modal = new FeatureEditModal(observables, this._controller);
                    const div = this._modal.getDOMElement();
                    div.classList.add('outerModal');
                    const draggable = new L.Draggable(div);
                    draggable.enable()
                    document.getElementById('multiselectInsert').replaceChildren(div);
                }
            }
            mouseIsDown = false;
        };
        map.on('mouseup', this._mouseup);
    },
    _deactivate(map) {
        this._div.style.removeProperty('border');
        document.getElementById('map').style.removeProperty('cursor');
        this._removeHighlights();
        map.dragging.enable();
        map.off('mousedown', this._mousedown);
        map.off('mousemove', this._mousemove);
        map.off('mouseup', this._mouseup);
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
    },
    /**
     * - Remove the highlight from the previously selected nodes and lines
     */
    _removeHighlights() {
        for (const ob of this._selectedObservables) {
            const path = Object.values(ob.getObservers().filter(o => o instanceof LeafletLayer)[0].getLayer()._layers)[0];
            if (ob.isNode()) {
                path.setStyle({
                    color: 'black'
                });
            } else if (ob.isLine()) {
                if (path.options.hasOwnProperty('colorModalColor')) {
                    path.setStyle({
                        color: path.options.colorModalColor
                    });
                } else {
                    path.setStyle({
                        color: path.options.originalColor
                    });
                }
            }
        }
        for (const ob of this._selectedObservables) {
            ob.removeObserver(this._modal)
        }
        this._selectedObservables = [];
        document.getElementById('multiselectInsert').replaceChildren();
    },
    /**
     * - x
     */
    _getSvg() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
        svg.setAttribute('width', '32px');
        svg.setAttribute('height', '32px');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.setAttribute('fill', 'none');
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M5 6C5.55228 6 6 5.55228 6 5C6 4.44772 5.55228 4 5 4C4.44772 4 4 4.44772 4 5C4 5.55228 4.44772 6 5 6ZM18 13C18 12.4477 17.5523 12 17 12C16.4477 12 16 12.4477 16 13V16H13C12.4477 16 12 16.4477 12 17C12 17.5523 12.4477 18 13 18H16V21C16 21.5523 16.4477 22 17 22C17.5523 22 18 21.5523 18 21V18H21C21.5523 18 22 17.5523 22 17C22 16.4477 21.5523 16 21 16H18V13ZM10 5C10 5.55228 9.55228 6 9 6C8.44771 6 8 5.55228 8 5C8 4.44772 8.44771 4 9 4C9.55228 4 10 4.44772 10 5ZM13 6C13.5523 6 14 5.55228 14 5C14 4.44772 13.5523 4 13 4C12.4477 4 12 4.44772 12 5C12 5.55228 12.4477 6 13 6ZM18 5C18 5.55228 17.5523 6 17 6C16.4477 6 16 5.55228 16 5C16 4.44772 16.4477 4 17 4C17.5523 4 18 4.44772 18 5ZM17 10C17.5523 10 18 9.55228 18 9C18 8.44771 17.5523 8 17 8C16.4477 8 16 8.44771 16 9C16 9.55228 16.4477 10 17 10ZM10 17C10 17.5523 9.55228 18 9 18C8.44771 18 8 17.5523 8 17C8 16.4477 8.44771 16 9 16C9.55228 16 10 16.4477 10 17ZM5 18C5.55228 18 6 17.5523 6 17C6 16.4477 5.55228 16 5 16C4.44772 16 4 16.4477 4 17C4 17.5523 4.44772 18 5 18ZM6 13C6 13.5523 5.55228 14 5 14C4.44772 14 4 13.5523 4 13C4 12.4477 4.44772 12 5 12C5.55228 12 6 12.4477 6 13ZM5 10C5.55228 10 6 9.55228 6 9C6 8.44771 5.55228 8 5 8C4.44772 8 4 8.44771 4 9C4 9.55228 4.44772 10 5 10Z');
        path.setAttribute('fill-rule', 'evenodd');
        path.setAttribute('clip-rule', 'evenodd');
        path.setAttribute('fill', '#000000');
        svg.appendChild(path);
        return svg;
    }
});