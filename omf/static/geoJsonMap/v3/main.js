export { hideModalInsert };
import { DropdownDiv } from './dropdownDiv.js';
import { Feature } from  './feature.js';
import { FeatureGraph } from  './featureGraph.js';
import { FeatureController } from './featureController.js';
import { getLoadingModal, getAnonymizationDiv, getSaveDiv, getRawDataDiv, getRenameDiv, getLoadFeederDiv, getBlankFeederDiv, getWindmilDiv, getGridlabdDiv, getCymdistDiv, getOpendssDiv, getAmiDiv, getAttachmentsDiv, getClimateDiv, getScadaDiv, getColorDiv, getGeojsonDiv, getSearchDiv, getAddComponentsDiv } from './modalFeatures.js';
import { LeafletLayer } from './leafletLayer.js';
import { Nav } from './nav.js';
import { SearchModal } from './searchModal.js';
import { TopTab } from './topTab.js';
import { ClusterControlClass } from './clusterControl.js';
import { MultiselectControlClass } from './multiselectControl.js';
import { ZoomControlClass } from './zoomControl.js';

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
    const controller = new FeatureController(featureGraph);
    const nav = new Nav();
    setupNav(controller, nav);
    const topTab = new TopTab();
    setupMap(controller, nav);
    createSearchModal(controller, nav, topTab);
    setupControls(controller);
    const modalInsert = document.getElementById('modalInsert');
    modalInsert.addEventListener('click', hideModalInsert);
    createHelpMenu();
    createEditMenu(controller, nav, topTab);
    if (gIsOnline && gShowFileMenu) {
        createFileMenu(controller);
    }
    addMenuEventHandlers();
}

/**
 * @param {FeatureController} controller - a FeatureController instance
 * @param {Nav} nav - a Nav instance
 * @returns {undefined}
 */
function setupNav(controller, nav) {
    if (!(controller instanceof FeatureController)) {
        throw TypeError('The "controller" argument must be instanceof FeatureController.');
    }
    if (!(nav instanceof Nav)) {
        throw TypeError('The "nav" argument must be instanceof Nav.');
    }
    const header = document.getElementsByTagName('header')[0];
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
}

function setupMap(controller, nav) {
    if (!(controller instanceof FeatureController)) {
        throw Error('The "controller" argument must be instanceof controller.');
    }
    if (!(nav instanceof Nav)) {
        throw TypeError('The "nav" argument must be instanceof Nav.');
    }
    const div = document.createElement('div');
    div.id = 'map';
    nav.sideNavArticleElement.prepend(div);
    const maxZoom = 32;
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
    LeafletLayer.map = L.map('map', {
        // - This zoom level sensibly displays all circuits to start, even the ones with weird one-off players that skew where the center is
        zoom: 14,
        // - Provide the layers that the map should start with
        layers: [esri_satellite_layer, LeafletLayer.parentChildLineLayers, LeafletLayer.lineLayers, LeafletLayer.nodeLayers],
        // - Better performance for large datasets
        renderer: L.canvas(),
        // - Disable box zoom shortcut because we use the shift key for multiselection
        boxZoom: false
    });
    // - Whenever there is a mouseup event on the map, it's possible that a marker was being dragged. To prevent the marker from "sticking" to the
    //   cursor, just turn off the active trackCursor function
    LeafletLayer.map.on('mouseup', (e) => {
        if (LeafletLayer.trackCursor !== null) {
            LeafletLayer.map.off('mousemove', LeafletLayer.trackCursor);
        }
    });
    // - Prevent all leaflet popup "x" buttons from triggering a "mouseup" event on the map
    LeafletLayer.map.on('popupopen', (e) => {
        for (const btn of [...document.getElementsByClassName('leaflet-popup-close-button')]) {
            btn.addEventListener('mouseup', (e) => {
                e.stopPropagation();
            });
        }
    });
    // - This stops mouseup events from propagating from this pane to the map because otherwise clicking on a popup modal will highlight objects if
    //   multiselection is enabled
    L.DomEvent.on(LeafletLayer.map.getPane('popupPane'), 'mouseup', (e) => {
        e.stopPropagation();
    });
    const baseMaps = {
        'Satellite': esri_satellite_layer,
        'Streets': mapbox_layer,
        'Topo': esri_topography_layer,
        'Blank': blank_layer
    };
    // - overlayMaps is still needed for GeoJSON layers
    const overlayMaps = {}
    LeafletLayer.control = L.control.layers(baseMaps, overlayMaps, {
        position: 'topleft',
        collapsed: false,
    });
    LeafletLayer.control.addTo(LeafletLayer.map);
    // - I have to add the cluster control before LeafletLayer instances are created. I have no choice
    const clusterControl = new ClusterControlClass(controller);
    LeafletLayer.map.addControl(clusterControl);
    LeafletLayer.clusterControl = clusterControl;
    // - Create layers for all visible objects
    controller.observableGraph.getObservables().forEach(ob => {
        if (!ob.isConfigurationObject()) {
            // - Here, the first observer is added to every visible feature
            LeafletLayer.createAndGroupLayer(ob, controller);
        }
    });
    LeafletLayer.map.fitBounds(LeafletLayer.nodeLayers.getBounds());
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
    };
}

/**
 * @param {FeatureController} controller - a FeatureController instance
 * @param {Nav} nav - a Nav instance
 * @param {TopTab} topTab - a TopTap instance
 * @returns {undefined}
 */
function createSearchModal(controller, nav, topTab) {
    if (!(controller instanceof FeatureController)) {
        throw TypeError('The "controller" argument must be instanceof FeatureController.');
    }
    if (!(nav instanceof Nav)) {
        throw TypeError('The "nav" argument must be instanceof Nav.');
    }
    if (!(topTab instanceof TopTab)) {
        throw TypeError('The "topTab" argument must be instanceof TopTab.');
    }
    nav.sideNavNavElement.appendChild(topTab.divElement); 
    // - Add tab for searching existing features
    const searchTab = document.createElement('div');
    topTab.addTab('Search Objects', searchTab);
    topTab.selectTab(topTab.getTab('Search Objects').tab);
    let searchModal = new SearchModal(controller);
    // - add static reference
    SearchModal.searchModal = searchModal;
    searchTab.appendChild(searchModal.getDOMElement());
    let searchResultsDiv = document.createElement('div');
    searchTab.appendChild(searchResultsDiv);
    searchResultsDiv.appendChild(searchModal.getConfigSearchResultsDiv());
    searchResultsDiv.appendChild(searchModal.getNodeSearchResultsDiv());
    searchResultsDiv.appendChild(searchModal.getLineSearchResultsDiv());
    // - Add tab for adding components
    const componentTab = document.createElement('div');
    topTab.addTab('Add New Objects', componentTab);
    let components = gComponentsCollection.features.filter(f => f.properties.componentType === 'gridlabd');
    const omdFeature = controller.observableGraph.getObservable('omd');
    if (omdFeature.hasProperty('syntax', 'meta')) {
        if (omdFeature.getProperty('syntax', 'meta') === 'DSS') {
            components = gComponentsCollection.features.filter(f => f.properties.componentType === 'opendss');
        }
    }
    components = components.map(f => {
        const feature = new Feature(f);
        if (feature.hasProperty('name') && feature.getProperty('name').toString().toLowerCase() === 'null') {
            feature.setProperty('name', 'new');
        }
        return feature;
    });
    searchModal = new SearchModal(controller, components);
    // - Add static reference
    SearchModal.componentModal = searchModal;
    componentTab.appendChild(searchModal.getDOMElement());
    searchResultsDiv = document.createElement('div');
    componentTab.appendChild(searchResultsDiv);
    searchResultsDiv.appendChild(searchModal.getConfigSearchResultsDiv()); 
    searchResultsDiv.appendChild(searchModal.getNodeSearchResultsDiv()); 
    searchResultsDiv.appendChild(searchModal.getLineSearchResultsDiv()); 
    // - Add legend insert
    const legendInsert = document.createElement('div');
    legendInsert.id = 'legendInsert';
    document.getElementsByTagName('main')[0].appendChild(legendInsert);
    // - Add multiselect insert
    const multiselectInsert = document.createElement('div');
    multiselectInsert.id = 'multiselectInsert';
    document.getElementsByTagName('main')[0].appendChild(multiselectInsert);
}

/**
 * - Set up the controls in the top left hand corner of the screen
 */
function setupControls(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('The "controller" argument must be instanceof controller.');
    }
    addCustomRadioControl(controller);
    addZoomControl(controller);
    addMultiselectControl(controller);
    addRuler();
    addGeocoding();
    // - Prevent mouse events from propagating from controls to the map
    for (const div of [...document.getElementsByClassName('leaflet-control')]) {
        L.DomEvent.on(div, 'mousedown', function (e) {
            L.DomEvent.stopPropagation(e);
        });
        L.DomEvent.on(div, 'mouseup', function (e) {
            L.DomEvent.stopPropagation(e);
        });
        L.DomEvent.on(div, 'click', function (e) {
            L.DomEvent.stopPropagation(e);
        });
    }
}

function addCustomRadioControl(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('The "controller" argument must be instanceof controller.');
    }
    // - Create div for separator line
    let div = document.createElement('div');
    div.classList.add('leaflet-control-layers-separator');
    document.querySelector('section.leaflet-control-layers-list').append(div);
    // - Create div for custom radio buttons
    div = document.createElement('div');
    document.querySelector('section.leaflet-control-layers-list').append(div);
    // - Create circuit radio button
    let label = document.createElement('label');
    div.append(label);
    let outerSpan = document.createElement('span');
    label.append(outerSpan);
    let radio = document.createElement('input');
    radio.type = 'radio';
    radio.name = 'circuitDisplay'
    radio.checked = true;
    radio.value = 'displayCircuit';
    radio.addEventListener('change', function() {
        LeafletLayer.resetLayerGroups(controller);
    });
    outerSpan.append(radio);
    let innerSpan = document.createElement('span');
    innerSpan.textContent = 'Display full circuit';
    outerSpan.append(innerSpan);
    // - Create search results radio button
    label = document.createElement('label');
    div.append(label);
    outerSpan = document.createElement('span');
    label.append(outerSpan);
    radio = document.createElement('input');
    radio.type = 'radio';
    radio.name = 'circuitDisplay';
    radio.value = 'displaySearch';
    radio.addEventListener('change', function() {
        SearchModal.searchModal.filterLayerGroups();
    });
    outerSpan.append(radio);
    innerSpan = document.createElement('span');
    innerSpan.textContent = 'Display search results'
    outerSpan.append(innerSpan);
}

function addZoomControl(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('The "controller" argument must be instanceof controller.');
    }
    const zoomControl = new ZoomControlClass(controller);
    LeafletLayer.map.addControl(zoomControl);
}

function addMultiselectControl(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('The "controller" argument must be instanceof controller.');
    }
    const multiselectControl = new MultiselectControlClass(controller);
    LeafletLayer.map.addControl(multiselectControl);
}

function addRuler() {
    var options = {
        position: 'topleft',
        lengthUnit: {
            display: 'm',
            decimal: 3,
            factor: 1000,
            label: 'Distance (m):'
          },
          angleUnit: {
            display: '&deg;',
            decimal: 3,
            factor: null,
            label: 'Angle:'
          }
      };
    L.control.ruler(options).addTo(LeafletLayer.map);
}

function addGeocoding() {
    const provider = new GeoSearch.OpenStreetMapProvider();
    const search = new GeoSearch.GeoSearchControl({
        provider: provider,
        position: 'topleft',
        updateMap: false // - don't update the map because we don't like the default zoom level
    });
    // - Custom zoom behavior
    LeafletLayer.map.on('geosearch/showlocation', function(e) {
        // - The max zoom level without losing the map is 19
        LeafletLayer.map.flyTo([e.location.y, e.location.x], 19, {duration: .3});
    });
    LeafletLayer.map.addControl(search);
}

function createHelpMenu() {
    const div = document.createElement('div');
    div.style.fontSize = '13px';
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
 * @param {Nav} nav - a Nav instance
 * @param {TopTab} topTab - a TopTab instance
 * @returns {undefined}
 */
function createEditMenu(controller, nav, topTab) {
    if (!(controller instanceof FeatureController)) {
        throw TypeError('"controller" argument must be instanceof FeatureController.');
    }
    if (!(nav instanceof Nav)) {
        throw TypeError('"nav" argument must be instanceof Nav.');
    }
    if (!(topTab instanceof TopTab)) {
        throw TypeError('"topTab" argument must be instanceof TopTab.');
    }
    const dropdownDiv = new DropdownDiv();
    dropdownDiv.divElement.id = 'editMenu';
    dropdownDiv.addStyleClasses(['menu'], 'divElement');
    dropdownDiv.setButton('Edit', true);
    document.getElementById('menuInsert').appendChild(dropdownDiv.divElement);
    dropdownDiv.insertElement(getSearchDiv(nav, topTab));
    dropdownDiv.insertElement(getAddComponentsDiv(nav, topTab));
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
 * @returns {undefined}
 */
function addMenuEventHandlers() {
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

/**
 * @returns {undefined}
 */
function hideModalInsert() {
    const modalInsert = document.getElementById('modalInsert');
    modalInsert.classList.remove('visible');
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