export { ZoomControlClass };
import { FeatureController } from './featureController.js'
import { LeafletLayer } from './leafletLayer.js';

const ZoomControlClass = L.Control.extend({
    options: {
        position: 'topleft' // - Position the control in the top left corner by default
    },
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
        this._div.title = '- The focus button pans the map to show the circuit';
        // - Attach listeners
        this._div.addEventListener('click', () => {
            LeafletLayer.map.fitBounds(LeafletLayer.nodeLayers.getBounds());
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
    _getSvg() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '32px');
        svg.setAttribute('height', '32px');
        svg.setAttribute('viewBox', '0 0 64 64');
        svg.setAttribute('fill', 'none');
        let element = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        element.setAttribute('cx', '32');
        element.setAttribute('cy', '32');
        element.setAttribute('r', '18.5');
        element.setAttribute('stroke', '#000000');
        element.setAttribute('stroke-width', '4');
        svg.appendChild(element);
        element = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        element.setAttribute('cx', '32');
        element.setAttribute('cy', '32');
        element.setAttribute('r', '10.68');
        element.setAttribute('stroke', '#000000');
        element.setAttribute('stroke-width', '4');
        svg.appendChild(element);
        element = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        element.setAttribute('x1', '32');
        element.setAttribute('y1', '4.56');
        element.setAttribute('x2', '32');
        element.setAttribute('y2', '26.56');
        element.setAttribute('stroke', '#000000');
        element.setAttribute('stroke-width', '4');
        element.setAttribute('stroke-linecap', 'round');
        svg.appendChild(element);
        element = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        element.setAttribute('x1', '32');
        element.setAttribute('y1', '37');
        element.setAttribute('x2', '32');
        element.setAttribute('y2', '59');
        element.setAttribute('stroke', '#000000');
        element.setAttribute('stroke-width', '4');
        element.setAttribute('stroke-linecap', 'round');
        svg.appendChild(element);
        element = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        element.setAttribute('x1', '37');
        element.setAttribute('y1', '32');
        element.setAttribute('x2', '59');
        element.setAttribute('y2', '32');
        element.setAttribute('stroke', '#000000');
        element.setAttribute('stroke-width', '4');
        element.setAttribute('stroke-linecap', 'round');
        svg.appendChild(element);
        element = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        element.setAttribute('x1', '5.06');
        element.setAttribute('y1', '32');
        element.setAttribute('x2', '26.94');
        element.setAttribute('y2', '32');
        element.setAttribute('stroke', '#000000');
        element.setAttribute('stroke-width', '4');
        element.setAttribute('stroke-linecap', 'round');
        svg.appendChild(element);
        return svg;
    }
});