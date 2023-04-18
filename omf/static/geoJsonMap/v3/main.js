import { DropdownDiv } from './dropdownDiv.js';
import { Feature } from  './feature.js';
import { FeatureGraph } from  './featureGraph.js';
import { FeatureController } from './featureController.js';
import { getLoadingModal, getAnonymizationDiv, getSaveDiv, getRawDataDiv, getRenameDiv, getLoadFeederDiv, 
    getBlankFeederDiv, getWindmilDiv, getGridlabdDiv, getCymdistDiv, getOpendssDiv, getAmiDiv, 
    getAttachmentsDiv, getClimateDiv, getScadaDiv, getStaticLoadsToHousesDiv } from './modalFeatures.js';
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
    // - Create and insert parent-child lines. This logic should be moved to and manged by the controller somehow
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
    featureGraph.getObservables().forEach(observable => {
        if (!observable.isConfigurationObject()) {
            // - Add first observer to a visible ObservableInterface instance
            const controller = new FeatureController(featureGraph, [observable.getProperty('treeKey', 'meta')]);
            // - Add second observer to a visible ObserverInterface instance
            new LeafletLayer(controller);
        }
    });
    setupHTML(featureGraph);
    const osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 29,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    });
    const baseMaps = {
        'Raster tiles': osm
        //'Vector tiles': mapTiler
    };
    const overlayMaps = {
        'Nodes': LeafletLayer.nodeLayers,
        'Lines': LeafletLayer.lineLayers,
        'Parent-Child Lines': LeafletLayer.parentChildLineLayers
    }
    const map = L.map('map', {
        center: LeafletLayer.nodeLayers.getBounds().getCenter(),
        // - This zoom level sensibly displays all circuits to start, even the ones with weird one-off players that skew where the center is
        zoom: 14,
        // - Provide the layers that the map should start with
        layers: [osm, LeafletLayer.nodeLayers, LeafletLayer.lineLayers, LeafletLayer.parentChildLineLayers],
        // - Better performance for large datasets
        renderer: L.canvas()
    });
    LeafletLayer.map = map;
    L.control.layers(baseMaps, overlayMaps).addTo(map);
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
}

function setupHTML(featureGraph) {
    createNav(featureGraph);
    createHelpMenu();
    createEditMenu(featureGraph);
    createFileMenu(featureGraph);
    // - Add event listeners to only allow either the file or edit menu to be open
    const menuInsert = document.getElementById('menuInsert');
    const buttons = menuInsert.getElementsByTagName('button');
    const fileButton = buttons[0];
    const editButton = buttons[1];
    fileButton.addEventListener('click', function() {
        if (this.classList.contains('expanded')) {
            if (editButton.classList.contains('expanded')) {
                editButton.click();
            }
        }
    });
    editButton.addEventListener('click', function() {
        if (this.classList.contains('expanded')) {
            if (fileButton.classList.contains('expanded')) {
                fileButton.click();
            }
        }
    });
    // - Save before rendering the interface to remove any previous error files
    document.getElementById('saveDiv').click();
    // - Allow the modal insert to be closed
    const modalInsert = document.getElementById('modalInsert');
    modalInsert.addEventListener('click', function() {
        modalInsert.classList.remove('visible');
    });
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my FeatureGraph class that has already been built
 * @returns {undefined}
 */
function createNav(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const header = document.getElementsByTagName('header')[0];
    const nav = new Nav();
    nav.topNav.setHomepageName(`"${gThisFeederName}" from ${gThisModelName}`);
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
    // - Add third observer to visible ObserverInterface instances
    let controller = new FeatureController(
        featureGraph,
        featureGraph.getObservables(f => {
            return !f.isModalFeature() && !f.isComponentFeature() && f.getProperty('treeKey', 'meta') !== 'omd';
        }).map(f => f.getProperty('treeKey', 'meta')));
    // - Add fourth observer to visible ObserverInterface instances
    let searchModal = new SearchModal(controller);
    searchTab.appendChild(searchModal.getDOMElement());
    searchTab.appendChild(searchModal.getSearchResultsElement());
    // - Add tab for adding components
    const componentTab = document.createElement('div');
    topTab.addTab('Add Components', componentTab);
    let components = gComponentsCollection.features.filter(f => f.properties.componentType === 'gridlabd');
    const omdFeature = featureGraph.getObservable('omd');
    if (omdFeature.hasProperty('syntax', 'meta')) {
        if (omdFeature.getProperty('syntax', 'meta') === 'DSS') {
            components = gComponentsCollection.features.filter(f => f.properties.componentType === 'opendss');
        }
    }
    const componentIDs = components.map(f => f.properties.treeKey);
    controller = new FeatureController(featureGraph, componentIDs, true);
    searchModal = new SearchModal(controller);
    componentTab.appendChild(searchModal.getDOMElement());
    componentTab.appendChild(searchModal.getSearchResultsElement());
    // - Add map and modal insert divs
    let div = document.createElement('div');
    div.id = 'map';
    nav.sideNavArticleElement.prepend(div);
}

function createHelpMenu() {
    const div = document.createElement('div');
    div.style.fontSize = '1.3rem';
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
 * @param {FeatureGraph} featureGraph - an instance of my FeatureGraph class that has already been built
 * @returns {undefined}
 */
function createEditMenu(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const dropdownDiv = new DropdownDiv();
    dropdownDiv.addStyleClass('menu');
    dropdownDiv.setButton('Edit', true);
    document.getElementById('menuInsert').appendChild(dropdownDiv.divElement);
    dropdownDiv.insertElement(getAmiDiv(featureGraph));
    dropdownDiv.insertElement(getAnonymizationDiv(featureGraph));
    dropdownDiv.insertElement(getAttachmentsDiv(featureGraph));
    dropdownDiv.insertElement(getClimateDiv(featureGraph));
    dropdownDiv.insertElement(getScadaDiv(featureGraph));
    //dropdownDiv.insertElement(getStaticLoadsToHousesDiv(featureGraph));
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my FeatureGraph class that has already been built
 * @returns {undefined}
 */
function createFileMenu(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const dropdownDiv = new DropdownDiv();
    dropdownDiv.addStyleClass('menu');
    dropdownDiv.setButton('File', true);
    document.getElementById('menuInsert').appendChild(dropdownDiv.divElement);
    dropdownDiv.insertElement(getSaveDiv(featureGraph));
    dropdownDiv.insertElement(getRawDataDiv(featureGraph));
    dropdownDiv.insertElement(getRenameDiv(featureGraph));
    dropdownDiv.insertElement(getLoadFeederDiv(featureGraph));
    dropdownDiv.insertElement(getBlankFeederDiv(featureGraph));
    dropdownDiv.insertElement(getWindmilDiv(featureGraph));
    dropdownDiv.insertElement(getGridlabdDiv(featureGraph));
    dropdownDiv.insertElement(getCymdistDiv(featureGraph));
    dropdownDiv.insertElement(getOpendssDiv(featureGraph));
}

(function loadInterface() {
    const modalInsert = document.createElement('div');
    modalInsert.classList.add('visible');
    modalInsert.id = 'modalInsert';
    modalInsert.replaceChildren(getLoadingModal().divElement);
    document.getElementsByTagName('main')[0].appendChild(modalInsert);
    setTimeout(() => main(), 1);
})();
