export { ClusterControlClass };
import { FeatureController } from './featureController.js'
import { LeafletLayer } from './leafletLayer.js';

const ClusterControlClass = L.Control.extend({
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
        this._on = false;
        // - Create div
        this._div = L.DomUtil.create('div', 'leaflet-bar');
        this._div.classList.add('leaflet-customControlDiv');
        L.DomEvent.disableClickPropagation(this._div);
        this._div.appendChild(this._getExpandSvg());
        // - Add a tooltip
        this._div.title = '- The node grouping tool allows you to group nodes into a cluster\n- Click this button to enable\n- Click this button to disable'
        // - Attach listeners
        this._div.addEventListener('click', () => {
            // - Clustering was enabled, so disable it
            if (this._on) {
                this._div.style.removeProperty('border');
                this._div.replaceChildren(this._getExpandSvg());
                for (const node of LeafletLayer.nodeClusterLayers.getLayers()) {
                    LeafletLayer.nodeLayers.addLayer(node);
                }
                LeafletLayer.nodeClusterLayers.clearLayers();
                this._on = false;
            // - Clustering was disabled, so enable it
            } else {
                this._div.style.border = '2px solid #7FFF00';
                this._div.replaceChildren(this._getCompressSvg());
                for (const node of LeafletLayer.nodeLayers.getLayers()) {
                    LeafletLayer.nodeClusterLayers.addLayer(node);
                }
                LeafletLayer.nodeLayers.clearLayers();
                this._on = true;
            }
            // - Force redraw
            for (const layer of [LeafletLayer.nodeLayers, LeafletLayer.nodeClusterLayers]) {
                LeafletLayer.map.removeLayer(layer);
                LeafletLayer.map.addLayer(layer);
            }
        });
        if (options !== null) {
            L.setOptions(this, options);
        }
    },
    onAdd(map) {
        return this._div; 
    },
    onRemove(map) {

    },
    _getExpandSvg() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
        svg.setAttribute('width', '32px');
        svg.setAttribute('height', '32px');
        svg.setAttribute('viewBox', '0 0 24 24'); 
        svg.setAttribute('fill', 'none');
        let path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M9 9L5 5M5 5L5 9M5 5L9 5');
        path.setAttribute('stroke', '#000000');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        svg.appendChild(path);
        path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M15 9L19 5M19 5L15 5M19 5L19 9');
        path.setAttribute('stroke', '#000000');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        svg.appendChild(path);
        path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M9 15L5 19M5 19L9 19M5 19L5 15');
        path.setAttribute('stroke', '#000000');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        svg.appendChild(path);
        path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M15 15L19 19M19 19L19 15M19 19L15 19');
        path.setAttribute('stroke', '#000000');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        svg.appendChild(path);
        return svg;
    },
    _getCompressSvg() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
        svg.setAttribute('width', '32px');
        svg.setAttribute('height', '32px');
        svg.setAttribute('viewBox', '0 0 24 24'); 
        svg.setAttribute('fill', 'none');
        let path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M5 5L9 9M9 9V5M9 9H5');
        path.setAttribute('stroke', '#000000');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        svg.appendChild(path);
        path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M19 5L15 9M15 9L19 9M15 9L15 5');
        path.setAttribute('stroke', '#000000');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        svg.appendChild(path);
        path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M5 19L9 15M9 15L5 15M9 15L9 19');
        path.setAttribute('stroke', '#000000');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        svg.appendChild(path);
        path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M19 19L15 15M15 15L15 19M15 15L19 15');
        path.setAttribute('stroke', '#000000');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        svg.appendChild(path);
        return svg;
    }
});