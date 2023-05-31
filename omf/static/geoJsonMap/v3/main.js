import { DropdownDiv } from './dropdownDiv.js';
import { Feature } from  './feature.js';
import { FeatureGraph } from  './featureGraph.js';
import { FeatureController } from './featureController.js';
import { getLoadingModal, getAnonymizationDiv, getSaveDiv, getRawDataDiv, getRenameDiv, getLoadFeederDiv, getBlankFeederDiv, getWindmilDiv, getGridlabdDiv, getCymdistDiv, getOpendssDiv, getAmiDiv, getAttachmentsDiv, getClimateDiv, getScadaDiv, getColorDiv, getGeojsonDiv } from './modalFeatures.js';
import { LeafletLayer } from './leafletLayer.js';
import { Nav } from './nav.js';
import { SearchModal } from './searchModal.js';
import { TopTab } from './topTab.js';

function main() {
    const features = gFeatureCollection.features.map(f => new Feature(f));
    const featureGraph = new FeatureGraph();
    // - Insert nodes
    features.filter(f => !f.isLine()).forEach(f => featureGraph.insertObservable(f));
    // - Insert lines. Lines can be parents, so they must be inserted before parent-child lines
    features.filter(f => f.isLine()).forEach(f => featureGraph.insertObservable(f));
    // - Create and insert parent-child lines
    features.filter(f => f.isChild()).forEach(f => {
        const parentKey = featureGraph.getKey(f.getProperty('parent'), f.getProperty('treeKey', 'meta'));
        const childKey = f.getProperty('treeKey', 'meta');
        const parentChildLineFeature = featureGraph.getParentChildLineFeature(parentKey, childKey);
        featureGraph.insertObservable(parentChildLineFeature);
    });
    // debug
    window.gFeatures = features;
    window.gFeatureGraph = featureGraph;
    // debug
    const controller = new FeatureController(featureGraph);
    featureGraph.getObservables().forEach(ob => {
        if (!ob.isConfigurationObject()) {
            // - Here, the first observer is added to every visible feature
            const ll = new LeafletLayer(ob, controller);
            if (ob.isNode()) {
                LeafletLayer.nodeLayers.addLayer(ll.getLayer());
            } else if (ob.isLine()) {
                if (ob.isParentChildLine()) {
                    LeafletLayer.parentChildLineLayers.addLayer(ll.getLayer());
                } else {
                    LeafletLayer.lineLayers.addLayer(ll.getLayer());
                }
            } else if (ob.isPolygon()) {
                // - Do nothing for now
            } else if (ob.isMultiPoint()) {
                // - Do nothing for now
            } else if (ob.isMultiLineString()) {
                // - Do nothing for now
            } else if (ob.isMultiPolygon()) {
                // - Do nothing for now
            } else {
                throw Error('The observable does not reference a valid GeoJSON feature (is it a configuration object or GeometryCollection?)');
            }
        }
    });
    createNav(controller);

    /****************/
    /* Setup layers */
    /****************/

    const maxZoom = 30;
    var esri_satellite_layer = L.esri.basemapLayer('Imagery', {
        maxZoom: maxZoom
    });
    const mapbox_layer = L.mapboxGL({
        attribution: "",
        // - Odd behavior: maxboxGL will let the user keep zooming in past maxZoom, but the tiles won't change. No other layers do this
        maxZoom: maxZoom,
        style: 'https://api.maptiler.com/maps/basic/style.json?key=WOwRKyy0L6AwPBuM4Ggj'
    });
    const esri_topography_layer = L.esri.basemapLayer('Streets', {
        maxZoom: maxZoom
    });
    const blank_layer = L.tileLayer('', {
        maxZoom: maxZoom
    });
    const baseMaps = {
        'Satellite': esri_satellite_layer,
        'Streets': mapbox_layer,
        'Topo': esri_topography_layer,
        'Blank': blank_layer
    };
    const overlayMaps = {
        'Nodes': LeafletLayer.nodeLayers,
        'Lines': LeafletLayer.lineLayers,
        'Parent-Child Lines': LeafletLayer.parentChildLineLayers,
    }
    const map = L.map('map', {
        center: LeafletLayer.nodeLayers.getBounds().getCenter(),
        // - This zoom level sensibly displays all circuits to start, even the ones with weird one-off players that skew where the center is
        zoom: 14,
        // - Provide the layers that the map should start with
        layers: [esri_satellite_layer, LeafletLayer.nodeLayers, LeafletLayer.lineLayers, LeafletLayer.parentChildLineLayers],
        // - Better performance for large datasets
        renderer: L.canvas()
    });
    LeafletLayer.map = map;
    L.control.layers(baseMaps, overlayMaps, { position: 'topleft', collapsed: false }).addTo(map);
    // - Disable the following annoying default Leaflet keyboard shortcuts:
    //  - TODO: do a better job and stop the event(s) from propagating in text inputs instead
    document.getElementById('map').onkeydown = function(e) {
        if ([
            '-',    // disable zoom-out for "-" key
            '_',    // disable mega zoom-out for "_" key
            '=',    // disable zoom-in for "=" key
            '+',    // disable mega zoom-in for "+" key
        ].includes(e.key)) {
            e.stopPropagation();
        }
        //console.log(e.key);
	};
    // - Allow the modal insert to be closed (remove this event listener when a server process is running)
    const modalInsert = document.getElementById('modalInsert');
    modalInsert.addEventListener('click', function() {
        modalInsert.classList.remove('visible');
    });
    setupHTML(controller);
}

/**
 * @param {FeatureController} controller - a FeatureController instance 
 * @returns {undefined}
 */
function setupHTML(controller) {
    if (!(controller instanceof FeatureController)) {
        throw TypeError('"controller" argument must be instanceof FeatureController.');
    }
    createHelpMenu();
    createEditMenu(controller);
    if (gIsOnline && gShowFileMenu) {
        createFileMenu(controller);
    }
    // - Add event listeners to only allow either the file or edit menu to be open
    const fileMenu = document.getElementById('fileMenu');
    let fileButton = null;
    if (fileMenu !== null) {
        fileButton = fileMenu.getElementsByTagName('button')[0];
        fileButton.addEventListener('click', function() {
            if (this.classList.contains('expanded')) {
                if (editButton !== null && editButton.classList.contains('expanded')) {
                    editButton.click();
                }
            }
        });
    }
    const editMenu = document.getElementById('editMenu');
    let editButton = null;
    if (editMenu !== null) {
        editButton = editMenu.getElementsByTagName('button')[0];
        editButton.addEventListener('click', function() {
            if (this.classList.contains('expanded')) {
                if (fileButton !== null && fileButton.classList.contains('expanded')) {
                    fileButton.click();
                }
            }
        });
    }
    // - Save before rendering the interface to remove any previous error files, but only in "online mode"
    if (gIsOnline) {
        document.getElementById('saveDiv').click();
    }
}

/**
 * @param {FeatureController} controller - a FeatureController instance
 * @returns {undefined}
 */
function createNav(controller) {
    if (!(controller instanceof FeatureController)) {
        throw TypeError('"controller" argument must be instanceof FeatureController.');
    }
    const header = document.getElementsByTagName('header')[0];
    const nav = new Nav();
    if (gIsOnline) {
        nav.topNav.setHomepageName(`"${gThisFeederName}" from ${gThisModelName}`);
    } else {
        nav.topNav.setHomepageName('');
    }
    header.prepend(nav.topNavNavElement); 
    const main = document.getElementsByTagName('main')[0];
    main.prepend(nav.sideNavArticleElement);
    main.prepend(nav.sideNavDivElement);
    main.prepend(nav.sideNavNavElement);
    const topTab = new TopTab();
    nav.sideNavNavElement.appendChild(topTab.divElement); 
    // - Add tab for searching existing features
    const searchTab = document.createElement('div');
    topTab.addTab('Search', searchTab);
    topTab.getTab('Search').tab.click();
    let searchModal = new SearchModal(controller);
    searchTab.appendChild(searchModal.getDOMElement());
    let searchResultsDiv = document.createElement('div');
    searchTab.appendChild(searchResultsDiv);
    searchResultsDiv.appendChild(searchModal.getConfigSearchResultsDiv());
    searchResultsDiv.appendChild(searchModal.getNodeSearchResultsDiv());
    searchResultsDiv.appendChild(searchModal.getLineSearchResultsDiv());
    // - Add tab for adding components
    const componentTab = document.createElement('div');
    topTab.addTab('Add', componentTab);
    let components = gComponentsCollection.features.filter(f => f.properties.componentType === 'gridlabd');
    const omdFeature = controller.observableGraph.getObservable('omd');
    if (omdFeature.hasProperty('syntax', 'meta')) {
        if (omdFeature.getProperty('syntax', 'meta') === 'DSS') {
            components = gComponentsCollection.features.filter(f => f.properties.componentType === 'opendss');
        }
    }
    components = components.map(f => new Feature(f));
    searchModal = new SearchModal(controller, components);
    componentTab.appendChild(searchModal.getDOMElement());
    searchResultsDiv = document.createElement('div');
    componentTab.appendChild(searchResultsDiv);
    searchResultsDiv.appendChild(searchModal.getConfigSearchResultsDiv()); 
    searchResultsDiv.appendChild(searchModal.getNodeSearchResultsDiv()); 
    searchResultsDiv.appendChild(searchModal.getLineSearchResultsDiv()); 
    // - Add map div
    let div = document.createElement('div');
    div.id = 'map';
    nav.sideNavArticleElement.prepend(div);
    // - Add legend insert
    const legendInsert = document.createElement('div');
    legendInsert.id = 'legendInsert';
    document.getElementsByTagName('main')[0].appendChild(legendInsert);
}

function createHelpMenu() {
    const div = document.createElement('div');
    div.style.fontSize = '1rem';
    div.style.height = '39px';
    div.style.width = '55px';
    div.style.color = 'white';
    const innerDiv = document.createElement('div');
    div.appendChild(innerDiv);
    innerDiv.style.display = 'flex';
    innerDiv.style.alignItems = 'center';
    innerDiv.style.height = '100%';
    const anchor = document.createElement('a');
    anchor.style.color = 'white'
    anchor.href = 'https://github.com/dpinney/omf/wiki/Tools-~-gridEdit';
    anchor.textContent = 'Help';
    anchor.target = '_blank';
    innerDiv.appendChild(anchor);
    document.getElementById('menuInsert').appendChild(div);
}

/**
 * @param {FeatureController} controller - a FeatureController instance
 * @returns {undefined}
 */
function createEditMenu(controller) {
    if (!(controller instanceof FeatureController)) {
        throw TypeError('"controller" argument must be instanceof FeatureController.');
    }
    const dropdownDiv = new DropdownDiv();
    dropdownDiv.divElement.id = 'editMenu';
    dropdownDiv.addStyleClasses(['menu'], 'divElement');
    dropdownDiv.setButton('Edit', true);
    document.getElementById('menuInsert').appendChild(dropdownDiv.divElement);
    if (gIsOnline) {
        dropdownDiv.insertElement(getAmiDiv(controller));
        dropdownDiv.insertElement(getAnonymizationDiv(controller));
    }
    dropdownDiv.insertElement(getAttachmentsDiv(controller));
    dropdownDiv.insertElement(getRawDataDiv(controller));
    if (gIsOnline) {
        dropdownDiv.insertElement(getClimateDiv(controller));
        dropdownDiv.insertElement(getScadaDiv(controller));
    }
    dropdownDiv.insertElement(getColorDiv(controller));
    dropdownDiv.insertElement(getGeojsonDiv(controller));
}

/**
 * @param {FeatureController} controller - a FeatureController instance
 * @returns {undefined}
 */
function createFileMenu(controller) {
    if (!(controller instanceof FeatureController)) {
        throw TypeError('"controller" argument must be instanceof FeatureController.');
    }
    const dropdownDiv = new DropdownDiv();
    dropdownDiv.divElement.id = 'fileMenu';
    dropdownDiv.addStyleClasses(['menu'], 'divElement');
    dropdownDiv.setButton('File', true);
    document.getElementById('menuInsert').appendChild(dropdownDiv.divElement);
    dropdownDiv.insertElement(getSaveDiv(controller));
    dropdownDiv.insertElement(getRenameDiv(controller));
    dropdownDiv.insertElement(getLoadFeederDiv(controller));
    dropdownDiv.insertElement(getBlankFeederDiv(controller));
    dropdownDiv.insertElement(getWindmilDiv(controller));
    dropdownDiv.insertElement(getGridlabdDiv(controller));
    dropdownDiv.insertElement(getCymdistDiv(controller));
    dropdownDiv.insertElement(getOpendssDiv(controller));
}

(function loadInterface() {
    const modalInsert = document.createElement('div');
    modalInsert.id = 'modalInsert';
    if (gIsOnline) {
        modalInsert.classList.add('visible');
        modalInsert.replaceChildren(getLoadingModal().divElement);
    }
    document.getElementsByTagName('main')[0].appendChild(modalInsert);
    setTimeout(() => main(), 1);
})();