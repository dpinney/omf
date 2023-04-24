export { getLoadingModal, getAnonymizationDiv, getSaveDiv, getRawDataDiv, getRenameDiv, getLoadFeederDiv, getBlankFeederDiv, getWindmilDiv, getGridlabdDiv, getCymdistDiv, getOpendssDiv, getAmiDiv, getAttachmentsDiv, getClimateDiv, getScadaDiv, getStaticLoadsToHousesDiv };
import { Feature } from  './feature.js';
import { FeatureController } from './featureController.js';
import { FeatureGraph } from './featureGraph.js';
import { Modal } from './modal.js';
'use strict';

/**
 * @returns {Modal}
 */
function getLoadingModal() {
    const modal = new Modal();
    modal.showProgress(true, 'Loading Map...');
    modal.addStyleClass('outerModal',     'divElement');
    modal.addStyleClass('fitContent',   'divElement');
    return modal;
}

/**
 * @param {FeatureController} controller - a ControllerInterface instance
 * @returns {Modal}
 */
function _getAnonymizationModal(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('"controller" argument must be an instance of FeatureController.');
    }
    // - namesAndLabelsSelect
    const namesAndLabelsSelect = document.createElement('select');
    namesAndLabelsSelect.name = 'anonymizeNameOption';
    let option = document.createElement('option');    
    option.text = 'No Change';
    option.value = 'noChange';
    namesAndLabelsSelect.add(option);
    option = document.createElement('option');
    option.text = 'Pseudonymize';
    option.value = 'pseudonymize';
    namesAndLabelsSelect.add(option);
    option = document.createElement('option');
    option.text = 'Randomize';
    option.value = 'randomize';
    namesAndLabelsSelect.add(option);
    const namesAndLabelsSelectDiv = _getHorizontalFlexDiv();
    namesAndLabelsSelectDiv.classList.add('centerCrossAxisFlex');
    namesAndLabelsSelectDiv.classList.add('indent1');
    namesAndLabelsSelectDiv.appendChild(namesAndLabelsSelect);
    const namesAndLabelsHeading = document.createElement('span');
    namesAndLabelsHeading.textContent = 'Names and Labels';
    const namesAndLabelsHeadingDiv = _getHorizontalFlexDiv();
    namesAndLabelsHeadingDiv.classList.add('centerCrossAxisFlex');
    namesAndLabelsHeadingDiv.appendChild(namesAndLabelsHeading);
    // - locationsSelect
    const locationsSelect = document.createElement('select');
    locationsSelect.name = 'anonymizeLocationOption';
    option = document.createElement('option');
    option.text = 'No Change';
    option.value = 'noChange';
    locationsSelect.add(option);
    option = document.createElement('option');
    option.text = 'Randomize';
    option.value = 'randomize';
    locationsSelect.add(option);
    option = document.createElement('option');
    option.text = 'Force Layout';
    option.value = 'forceLayout';
    locationsSelect.add(option);
    option = document.createElement('option');
    option.text = 'Translate';
    option.value = 'translation';
    locationsSelect.add(option);
    const locationsSelectDiv = _getHorizontalFlexDiv();
    locationsSelectDiv.classList.add('centerCrossAxisFlex');
    locationsSelectDiv.classList.add('indent1');
    locationsSelectDiv.appendChild(locationsSelect);
    const locationsHeading = document.createElement('span');
    locationsHeading.textContent = 'Locations';
    const locationsHeadingDiv = _getHorizontalFlexDiv();
    locationsHeadingDiv.classList.add('centerCrossAxisFlex');
    locationsHeadingDiv.appendChild(locationsHeading);
    // - Locations inputs
    const coordinatesInput = document.createElement('input');
    coordinatesInput.name = 'new_center_coords';
    const horizontalTranslationInput = document.createElement('input');
    horizontalTranslationInput.name = 'translateRight';
    const verticalTranslationInput = document.createElement('input');
    verticalTranslationInput.name = 'translateUp'
    const rotationInput = document.createElement('input');
    rotationInput.name = 'rotate';
    const scaleInput = document.createElement('input');
    scaleInput.name = 'scale';
    scaleInput.value = '.01';
    const scaleTipDiv = document.createElement('div');
    scaleTipDiv.textContent = 'Estimates: 0.001 = street-density, 0.01 = neighborhood-density, 0.1 = city-density, 1 = state-density';
    // - Electrical properties
    const electricalPropertiesHeading = document.createElement('span');
    electricalPropertiesHeading.textContent = 'Electrical Properties';
    const electricalPropertiesHeadingDiv = _getHorizontalFlexDiv();
    electricalPropertiesHeadingDiv.appendChild(electricalPropertiesHeading);
    electricalPropertiesHeadingDiv.classList.add('centerCrossAxisFlex');
    // - conductorCheckbox
    const conductorCheckbox = document.createElement('input');
    conductorCheckbox.id = 'modifyLengthSize';
    conductorCheckbox.type = 'checkbox';
    conductorCheckbox.name = 'modifyLengthSize';
    const conductorLabel = document.createElement('label');    
    conductorLabel.htmlFor = 'modifyLengthSize';
    conductorLabel.innerText = 'Modify Conductor Length and Cable Size';
    // - smoothAMICheckbox
    const smoothAMICheckbox = document.createElement('input');
    smoothAMICheckbox.id = 'smoothLoadGen';
    smoothAMICheckbox.type = 'checkbox';
    smoothAMICheckbox.name = 'smoothLoadGen';
    const smoothAMILabel = document.createElement('label');    
    smoothAMILabel.htmlFor = 'smoothLoadGen';
    smoothAMILabel.innerText = 'Smooth AMI Loadshapes';
    // - shuffleLoadsCheckbox
    const shuffleLoadsCheckbox = document.createElement('input');
    shuffleLoadsCheckbox.id = 'shuffleLoadGen';
    shuffleLoadsCheckbox.type = 'checkbox';
    shuffleLoadsCheckbox.name = 'shuffleLoadGen';
    const shuffleLoadsLabel = document.createElement('label');    
    shuffleLoadsLabel.htmlFor = 'shuffleLoadGen';
    shuffleLoadsLabel.innerText = ' Shuffle Loads and Generators';
    const shuffleLoadsInput = document.createElement('input');
    shuffleLoadsInput.name = 'shufflePerc';
    // - addNoiseCheckbox
    const addNoiseCheckbox = document.createElement('input');
    addNoiseCheckbox.id = 'addNoise';
    addNoiseCheckbox.type = 'checkbox';
    addNoiseCheckbox.name = 'addNoise';
    const addNoiseLabel = document.createElement('label');    
    addNoiseLabel.htmlFor = 'addNoise';
    addNoiseLabel.innerText = 'Add Noise';
    const addNoiseInput = document.createElement('input');
    addNoiseInput.name = 'noisePerc';
    // - Submit button
    const submitButton = _getSubmitButton();
    const submitDiv = _getSubmitDiv(submitButton);
    // - Feature
    const feature = controller.getObservables()[0];
    // - Event listeners
    // - namesAndLabelsSelect
    namesAndLabelsSelect.addEventListener('change', function() {
        feature.setProperty(this.name, this.value, 'formProps');
    });
    // - locationsSelect
    locationsSelect.addEventListener('change', function() {
        feature.setProperty(this.name, this.value, 'formProps');
        const translateModal = this.parentElement.nextElementSibling;
        if (this.value === 'translation') {
            translateModal.classList.remove('collapsed');
            if (!translateModal.classList.contains('expanded')) {
                translateModal.classList.add('expanded');
            }
        } else {
            translateModal.classList.remove('expanded');
            if (!translateModal.classList.contains('collapsed')) {
                translateModal.classList.add('collapsed');
            }
        }
        const scaleModal = this.parentElement.nextElementSibling.nextElementSibling;
        if (this.value === 'forceLayout') {
            scaleModal.classList.remove('collapsed');
            if (!scaleModal.classList.contains('expanded')) {
                scaleModal.classList.add('expanded');
            }
        } else {
            scaleModal.classList.remove('expanded');
            if (!scaleModal.classList.contains('collapsed')) {
                scaleModal.classList.add('collapsed');
            }
        }
    });
    // - Locations inputs
    coordinatesInput.addEventListener('change', function() {
        const value = this.value.trim();
        feature.setProperty(this.name, value, 'formProps');
    });
    horizontalTranslationInput.addEventListener('change', function() {
        const value = this.value.trim();
        feature.setProperty(this.name, value, 'formProps');
    });
    verticalTranslationInput.addEventListener('change', function() {
        const value = this.value.trim();
        feature.setProperty(this.name, value, 'formProps');
    });
    rotationInput.addEventListener('change', function() {
        const value = this.value.trim();
        feature.setProperty(this.name, value, 'formProps');
    });
    scaleInput.addEventListener('change', function() {
        const value = this.value.trim();
        feature.setProperty(this.name, value, 'formProps');
    });
    // - conductorCheckbox
    conductorCheckbox.addEventListener('change', function() {
        let value = '';
        if (this.checked) {
            value = 'modifyLengthSize';
        }
        feature.setProperty(this.name, value, 'formProps');
    });
    // - smoothAMICheckbox
    smoothAMICheckbox.addEventListener('change', function() {
        let value = '';
        if (this.checked) {
            value = 'smoothLoadGen';
        }
        feature.setProperty(this.name, value, 'formProps');
    });
    // - shuffleLoadsCheckbox
    shuffleLoadsCheckbox.addEventListener('change', function() {
        let value = '';
        if (this.checked) {
            value = 'shuffleLoadGen';
        }
        feature.setProperty(this.name, value, 'formProps');
        let parentElement = this.parentElement;
        while (!parentElement.classList.contains('js-div--modal')) {
            parentElement = parentElement.parentElement;
        }
        if (this.checked) {
            parentElement.nextSibling.classList.remove('collapsed');
            parentElement.nextSibling.classList.add('expanded');
        } else {
            if (!parentElement.nextSibling.classList.contains('collapsed')) {
                parentElement.nextSibling.classList.add('collapsed');
            }
        }
    });
    shuffleLoadsInput.addEventListener('change', function() {
        const value = this.value.trim();
        feature.setProperty(this.name, value, 'formProps');
    });
    // - addNoiseCheckbox
    addNoiseCheckbox.addEventListener('change', function() {
        let value = '';
        if (this.checked) {
            value = 'addNoise';
        }
        feature.setProperty(this.name, value, 'formProps');
        let parentElement = this.parentElement;
        while (!parentElement.classList.contains('js-div--modal')) {
            parentElement = parentElement.parentElement;
        }
        if (this.checked) {
            parentElement.nextSibling.classList.remove('collapsed');
            parentElement.nextSibling.classList.add('expanded');
        } else {
            if (!parentElement.nextSibling.classList.contains('collapsed')) {
                parentElement.nextSibling.classList.add('collapsed');
            }
        }
    });
    addNoiseInput.addEventListener('change', function() {
        const value = this.value.trim();
        feature.setProperty(this.name, value, 'formProps');
    });
    // - Modal
    const mainModal = new Modal();
    mainModal.addStyleClass('outerModal',  'divElement');
    mainModal.addStyleClass('fitContent',  'divElement');
    submitButton.addEventListener('click', async function() {
        const feature = controller.observableGraph.getObservable('modal:save');
        feature.setProperty('feederObjectJson', JSON.stringify(controller.observableGraph.getObservablesExportData()), 'formProps')
        // - It's okay to create another FeatureController here because the page will be reloaded
        const saveController = new FeatureController(controller.observableGraph, ['modal:save']);
        const saveModal = _getSaveModal(controller);
        const modalInsert = document.getElementById('modalInsert');
        modalInsert.replaceChildren(saveModal.divElement);
        await saveController.submitFeature(saveModal, false);
        document.getElementById('modalInsert').classList.add('visible');
        modalInsert.replaceChildren(mainModal.divElement);
        mainModal.showProgress(true, 'Anonymization working...', 'caution');
        controller.submitFeature(mainModal);
    });
    mainModal.setTitle('Anonymization');
    mainModal.addStyleClass('horizontalFlex',       'titleElement');
    mainModal.addStyleClass('centerMainAxisFlex',   'titleElement');
    mainModal.addStyleClass('centerCrossAxisFlex',  'titleElement');
    mainModal.insertElement(namesAndLabelsHeadingDiv);
    mainModal.insertElement(namesAndLabelsSelectDiv);
    mainModal.insertElement(locationsHeadingDiv);
    mainModal.insertElement(locationsSelectDiv);
    const translateModal = new Modal();
    translateModal.insertTBodyRow(['Shift center to', coordinatesInput, '(latitude, longitude) coordinates']);
    translateModal.insertTBodyRow(['Translate', horizontalTranslationInput, 'meters rightwards']);
    translateModal.insertTBodyRow(['Translate', verticalTranslationInput, 'meters upwards']);
    translateModal.insertTBodyRow(['Rotate', rotationInput, 'degrees counterclockwise']);
    translateModal.addStyleClass('collapsed',   'divElement');
    translateModal.addStyleClass('indent2',     'divElement');
    mainModal.insertElement(translateModal.divElement);
    const scaleModal = new Modal();
    scaleModal.insertTBodyRow(['Force layout with following scale factor', scaleInput]);
    scaleModal.insertElement(scaleTipDiv);
    scaleModal.addStyleClass('collapsed',   'divElement');
    scaleModal.addStyleClass('indent2',     'divElement');
    mainModal.insertElement(scaleModal.divElement);
    const electricalPropertiesHeadingModal = new Modal();
    electricalPropertiesHeadingModal.insertElement(electricalPropertiesHeadingDiv);
    mainModal.insertElement(electricalPropertiesHeadingModal.divElement);
    const electricalPropertiesModal = new Modal();
    electricalPropertiesModal.insertTBodyRow([conductorCheckbox, conductorLabel]);
    electricalPropertiesModal.insertTBodyRow([smoothAMICheckbox, smoothAMILabel]);
    electricalPropertiesModal.insertTBodyRow([shuffleLoadsCheckbox, shuffleLoadsLabel]);
    electricalPropertiesModal.addStyleClass('indent1',      'divElement');
    mainModal.insertElement(electricalPropertiesModal.divElement);
    const shuffleLoadsInputModal = new Modal();
    shuffleLoadsInputModal.insertTBodyRow(['Shuffle', shuffleLoadsInput, 'percent']);
    shuffleLoadsInputModal.addStyleClass('collapsed',   'divElement');
    shuffleLoadsInputModal.addStyleClass('indent2',     'divElement');
    mainModal.insertElement(shuffleLoadsInputModal.divElement);
    const addNoiseCheckboxModal = new Modal();
    addNoiseCheckboxModal.insertTBodyRow([addNoiseCheckbox, addNoiseLabel])
    addNoiseCheckboxModal.addStyleClass('indent1', 'divElement');
    mainModal.insertElement(addNoiseCheckboxModal.divElement);
    const addNoiseInputModal = new Modal();
    addNoiseInputModal.insertTBodyRow(['Add', addNoiseInput, 'percent noise']);
    addNoiseInputModal.addStyleClass('collapsed',   'divElement');
    addNoiseInputModal.addStyleClass('indent2',     'divElement');
    mainModal.insertElement(addNoiseInputModal.divElement);
    const submitDivModal = new Modal();
    submitDivModal.insertElement(submitDiv);
    submitDivModal.addStyleClass('horizontalFlex',      'containerElement');
    submitDivModal.addStyleClass('centerMainAxisFlex',  'containerElement');
    submitDivModal.addStyleClass('centerCrossAxisFlex', 'containerElement');
    mainModal.insertElement(submitDivModal.divElement);
    return mainModal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getAnonymizationDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const feature = new Feature({
        geometry: { 'coordinates': [null, null], 'type': 'Point' },
        properties: {
            treeKey: 'modal:anonymization',
            urlProps: {
                fileExistsUrl: {
                    method: 'GET',
                    url: `/uniqObjName/Feeder/${gThisOwner}/${gThisFeederName}/${gThisModelName}`
                },
                pollUrl: {
                    method: 'GET',
                    url: `/checkConversion/${gThisModelName}/${gThisOwner}`
                },
                submitUrl: {
                    method: 'POST',
                    url: `/anonymize/${gThisOwner}/${gThisFeederName}`
                }
            },
            formProps: {
                modelName: gThisModelName,
                anonymizeNameOption: 'noChange',
                anonymizeLocationOption: 'noChange',
                new_center_coords: '',
                translateRight: '',
                translateUp: '',
                rotate: '',
                // - In Python, bool('') returns a False bool. FormData objects can only send strings
                modifyLengthSize: '',       // 'modifyLengthSize',
                smoothLoadGen: '',          // 'smoothLoadGen',
                shuffleLoadGen: '',         // 'shuffleLoadGen',
                shufflePerc: '',
                addNoise: '',               // 'addNoise'
                noisePerc: '',
                scale: '.01' 
            },
        },
        type: 'Feature'
    });
    featureGraph.insertObservable(feature);
    const controller = new FeatureController(featureGraph, ['modal:anonymization']);
    const modal = _getAnonymizationModal(controller);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('Anonymization...');
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
    });
    return div;
}

/**
 * @param {FeatureController} controller - a ControllerInterface instance
 * @returns {Modal}
 */
function _getSaveModal(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('"controller" argument must be an instance of FeatureController.');
    }
    const modal = new Modal();
    modal.showProgress(true, 'Saving...');
    modal.addStyleClass('outerModal',     'divElement');
    modal.addStyleClass('fitContent',   'divElement');
    return modal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getSaveDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    // - Feature
    const feature = new Feature({
        geometry: { 'coordinates': [null, null], 'type': 'Point' },
        properties: {
            treeKey: 'modal:save',
            urlProps: {
                submitUrl: {
                    method: 'POST',
                    url: `/saveFeeder/${gThisOwner}/${gThisModelName}/${gThisFeederName}/${gThisFeederNum}`
                }
            },
            // - I need to read all of the data every time the save button is clicked, so set "feederObjectJson" in the event handler function
            formProps: {},
        },
        type: 'Feature'
    });
    featureGraph.insertObservable(feature);
    const controller = new FeatureController(featureGraph, ['modal:save']);
    const modal = _getSaveModal(controller);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('Save');
    div.id = 'saveDiv';
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
        // - I only export features that were originally in the OMD (i.e. those features with numeric tree keys)
        feature.setProperty('feederObjectJson', JSON.stringify(featureGraph.getObservablesExportData()), 'formProps')
        controller.submitFeature(modal, false); 
    });
    return div;
}

/**
 * @param {FeatureController} controller - a ControllerInterface instance
 * @returns {Modal}
 */
function _getRawDataModal(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('"controller" argument must be an instance of FeatureController.');
    }
    const modal = new Modal();
    modal.showProgress(true, 'Opening a window with JSON in it that you can save as a .json file...');
    modal.addStyleClass('outerModal',   'divElement');
    modal.addStyleClass('fitContent',   'divElement');
    return modal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getRawDataDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const feature = new Feature({
        geometry: { 'coordinates': [null, null], 'type': 'Point' },
        properties: {
            treeKey: 'modal:rawData',
        },
        type: 'Feature'
    });
    featureGraph.insertObservable(feature);
    const controller = new FeatureController(featureGraph, ['modal:rawData']);
    const modal = _getRawDataModal(controller);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('View Raw Data');
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
        const json = JSON.stringify(featureGraph.getObservablesExportData());
        const win = window.open();
        win.document.write(json);
    });
    return div;
}

/**
 * @param {FeatureController} controller - a ControllerInterface instance
 * @returns {Modal}
 */
function _getRenameModal(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('"controller" argument must be an instance of FeatureController.');
    }
    // - Input
    const input = document.createElement('input');
    // - Submit div
    const submitButton = _getSubmitButton();
    const submitDiv = _getSubmitDiv(submitButton);
    // - Feature
    const feature = controller.getObservables()[0];
    // - Event listeners
    input.addEventListener('change', function() {
        let newName = this.value.trim();
        if (newName === '') {
            newName = 'Default Name';
        }
        const fileExistsUrl = {
            method: 'GET',
            url: `/uniqObjName/Feeder/${gThisOwner}/${newName}/${gThisModelName}`
        }
        feature.setProperty('fileExistsUrl', fileExistsUrl, 'urlProps');
        const submitUrl = {
            method: 'GET',
            url: `/renameFeeder/${gThisOwner}/${gThisModelName}/${gThisFeederName}/${newName}/${gThisFeederNum}`
        }
        feature.setProperty('submitUrl', submitUrl, 'urlProps');
    });
    // - Modal 
    const renameModal = new Modal();
    renameModal.addStyleClass('outerModal',  'divElement');
    renameModal.addStyleClass('fitContent',  'divElement');
    submitButton.addEventListener('click', async function() {
        const feature = controller.observableGraph.getObservable('modal:save');
        feature.setProperty('feederObjectJson', JSON.stringify(controller.observableGraph.getObservablesExportData()), 'formProps')
        // - It's okay to create another FeatureController here because the page will be reloaded
        const saveController = new FeatureController(controller.observableGraph, ['modal:save']);
        const saveModal = _getSaveModal(controller);
        const modalInsert = document.getElementById('modalInsert');
        modalInsert.replaceChildren(saveModal.divElement);
        await saveController.submitFeature(saveModal, false);
        document.getElementById('modalInsert').classList.add('visible');
        modalInsert.replaceChildren(renameModal.divElement);
        renameModal.showProgress(true, 'Renaming feeder...', 'caution');
        controller.submitFeature(renameModal);
    });
    renameModal.setTitle('Rename Feeder');
    renameModal.addStyleClass('horizontalFlex',       'titleElement');
    renameModal.addStyleClass('centerMainAxisFlex',   'titleElement');
    renameModal.addStyleClass('centerCrossAxisFlex',  'titleElement');
    renameModal.insertTBodyRow(['New feeder name:', input]);
    renameModal.addStyleClass('centeredTable', 'tableElement');
    renameModal.insertElement(submitDiv);
    renameModal.addStyleClass('verticalFlex',         'containerElement');
    renameModal.addStyleClass('centerMainAxisFlex',   'containerElement');
    renameModal.addStyleClass('centerCrossAxisFlex',  'containerElement');
    return renameModal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getRenameDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const feature = new Feature({
        geometry: { 'coordinates': [null, null], 'type': 'Point' },
        properties: {
            treeKey: 'modal:rename',
            urlProps: {
                fileExistsUrl: {
                    method: 'GET',
                    url: `/uniqObjName/Feeder/${gThisOwner}/Default Name/${gThisModelName}`
                },
                submitUrl: {
                    method: 'GET',
                    url: `/renameFeeder/${gThisOwner}/${gThisModelName}/${gThisFeederName}/Default Name/${gThisFeederNum}`
                }
            }
        },
        type: 'Feature'
    });
    featureGraph.insertObservable(feature);
    const controller = new FeatureController(featureGraph, ['modal:rename']);
    const modal = _getRenameModal(controller);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('Rename...');
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
    });
    return div;
}

/**
 * @param {FeatureController} controller - a ControllerInterface instance
 * @returns {Modal}
 */
function _getLoadFeederModal(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('"controller" argument must be an instance of FeatureController.');
    }
    // - Feature
    const feature = controller.getObservables()[0];
    // - Create list of public feeders
    let publicFeeders = [];
    if (gPublicFeeders !== null) {
        publicFeeders = [...gPublicFeeders];
        publicFeeders.sort((a, b) => a.name.localeCompare(b.name, 'en', {numeric: true}));
    }
    const publicFeedersModal = new Modal();
    publicFeeders.map(obj => {
        const outerDiv = document.createElement('div');
        const nameDiv = document.createElement('div');
        nameDiv.textContent = obj.name;
        outerDiv.appendChild(nameDiv);
        const modelDiv = document.createElement('div');
        modelDiv.textContent = `from "${obj.model}"`;
        outerDiv.appendChild(modelDiv);
        outerDiv.addEventListener('click', function() {
            feature.setProperty('fileExistsUrl', {
                method: 'GET', 
                url: `/uniqObjName/Feeder/public/${obj.name}/${obj.model}`
            }, 'urlProps');
            feature.setProperty('submitUrl', {
                method: 'POST',
                url: `/loadFeeder/${obj.name}/${obj.model}/${gThisModelName}/${gThisFeederNum}/public/${gThisOwner}`,
            }, 'urlProps');
            controller.submitFeature(publicFeedersModal); 
        });
        outerDiv.classList.add('hoverable');
        return outerDiv;
    }).forEach(div => publicFeedersModal.insertTBodyRow([div]));
    publicFeedersModal.setTitle('Public Feeders');
    publicFeedersModal.addStyleClass('horizontalFlex',      'titleElement');
    publicFeedersModal.addStyleClass('centerMainAxisFlex',  'titleElement');
    publicFeedersModal.addStyleClass('centerCrossAxisFlex', 'titleElement');
    publicFeedersModal.addStyleClass('fullWidth', 'tableElement');
    // - Create list of user feeders
    let userFeeders = [];
    if (gUserFeeders !== null) {
        userFeeders = [...gUserFeeders];
        userFeeders.sort((a, b) => a.name.localeCompare(b.name, 'en', {numeric: true}));
    }
    const userFeedersModal = new Modal();
    userFeeders.map(obj => {
        const outerDiv = document.createElement('div');
        const nameDiv = document.createElement('div');
        nameDiv.textContent = obj.name;
        outerDiv.appendChild(nameDiv);
        const modelDiv = document.createElement('div');
        modelDiv.textContent = `from "${obj.model}"`;
        outerDiv.appendChild(modelDiv);
        outerDiv.addEventListener('click', function() {
            feature.setProperty('fileExistsUrl', {
                method: 'GET',
                // - Let's say I'm an admin viewing some user's file. gCurrentUser = "admin" and gThisOwner = "test". userFeeders is all of the
                //   admin's feeders. Therefore, to see if the admin's feeders exist in order to load them, I need /uniqObjName to check the current
                //   user's feeders, NOT the owner's feeders. Usually, gThisOwner === gCurrentUser, but this one special case is why this url is
                //   different
                url: `/uniqObjName/Feeder/${gCurrentUser}/${obj.name}/${obj.model}`
            }, 'urlProps');
            feature.setProperty('submitUrl', {
                method: 'POST',
                url: `/loadFeeder/${obj.name}/${obj.model}/${gThisModelName}/${gThisFeederNum}/${gCurrentUser}/${gThisOwner}`,
            }, 'urlProps');
            controller.submitFeature(userFeedersModal); 
        });
        outerDiv.classList.add('hoverable');
        return outerDiv;
    }).forEach(div => userFeedersModal.insertTBodyRow([div]));
    userFeedersModal.setTitle('User Feeders');
    userFeedersModal.addStyleClass('horizontalFlex',        'titleElement');
    userFeedersModal.addStyleClass('centerMainAxisFlex',    'titleElement');
    userFeedersModal.addStyleClass('centerCrossAxisFlex',   'titleElement');
    userFeedersModal.addStyleClass('fullWidth', 'tableElement');
    // - Main modal
    const mainModal = new Modal();
    mainModal.addStyleClass('outerModal',       'divElement');
    mainModal.addStyleClass('loadFeederModal',  'divElement');
    mainModal.setTitle('Load Feeder');
    mainModal.addStyleClass('horizontalFlex',       'titleElement');
    mainModal.addStyleClass('centerMainAxisFlex',   'titleElement');
    mainModal.addStyleClass('centerCrossAxisFlex',  'titleElement');
    mainModal.insertElement(publicFeedersModal.divElement);
    mainModal.insertElement(userFeedersModal.divElement);
    mainModal.addStyleClass('horizontalFlex', 'containerElement');
    return mainModal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getLoadFeederDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const feature = new Feature({
        geometry: { 'coordinates': [null, null], 'type': 'Point' },
        properties: {
            treeKey: 'modal:loadFeeder',
            urlProps: {},
            formProps: {
                referrer: 'distribution'
            }
        },
        'type': 'Feature'
    });
    featureGraph.insertObservable(feature);
    const controller = new FeatureController(featureGraph, ['modal:loadFeeder']);
    const modal = _getLoadFeederModal(controller);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('Load from Model...');
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
    });
    return div;
}

/**
 * @param {FeatureController} controller - a ControllerInterface instance
 * @returns {Modal}
 */
function _getBlankFeederModal(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('"controller" argument must be an instance of FeatureController.');
    }
    // - Input
    const input = document.createElement('input');
    // - Submit div
    const submitButton = _getSubmitButton();
    const submitDiv = _getSubmitDiv(submitButton);
    // - Feature
    const feature = controller.getObservables()[0];
    // - Event listeners
    input.addEventListener('change', function() {
        let newName = this.value.trim();
        if (newName === '') {
            newName = 'Default Name';
        }
        feature.setProperty('feederNameNew', newName, 'formProps');
    });
    // - Modal
    const modal = new Modal();
    modal.addStyleClass('outerModal',   'divElement');
    modal.addStyleClass('fitContent',   'divElement');
    submitButton.addEventListener('click', function() {
        modal.showProgress(true, 'Creating new blank feeder...', 'caution');
        controller.submitFeature(modal);
    });
    modal.setTitle('New Blank Feeder');
    modal.addStyleClass('horizontalFlex',       'titleElement');
    modal.addStyleClass('centerMainAxisFlex',   'titleElement');
    modal.addStyleClass('centerCrossAxisFlex',  'titleElement');
    modal.insertTBodyRow(['Blank feeder name', input]);
    modal.addStyleClass('centeredTable', 'tableElement');
    modal.insertElement(submitDiv);
    modal.addStyleClass('verticalFlex',         'containerElement');
    modal.addStyleClass('centerMainAxisFlex',   'containerElement');
    modal.addStyleClass('centerCrossAxisFlex',  'containerElement');
    return modal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getBlankFeederDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const feature = new Feature({
        geometry: { 'coordinates': [null, null], 'type': 'Point' },
        properties: {
            treeKey: 'modal:blankFeeder',
            urlProps: {
                submitUrl: {
                    method: 'POST',
                    url: `/newBlankFeeder/${gThisOwner}`
                }
            },
            formProps: {
                modelName: gThisModelName,
                feederNameNew: 'Default Name',
                feederNum: gThisFeederNum,
                referrer: 'distribution'
            }
        },
        type: 'Feature'
    });
    featureGraph.insertObservable(feature);
    const controller = new FeatureController(featureGraph, ['modal:blankFeeder']);
    const modal = _getBlankFeederModal(controller);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('New blank feeder...');
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
    });
    return div;
}

/**
 * @param {FeatureController} controller - a ControllerInterface instance
 * @returns {Modal}
 */
function _getWindmilModal(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('"controller" argument must be an instance of FeatureController.');
    }
    // - Name input
    const nameInput = document.createElement('input');
    nameInput.required = true;
    nameInput.id = 'milsoftNameInput';
    const nameLabel = document.createElement('label');
    nameLabel.htmlFor = 'milsoftNameInput';
    nameLabel.innerText = 'Name';
    // - .std file input
    const stdInput = document.createElement('input');
    stdInput.type = 'file';
    stdInput.accept = '.std';
    stdInput.required = true;
    stdInput.id = 'milsoftStdInput';
    const stdLabel = document.createElement('label');
    stdLabel.htmlFor = 'milsoftStdInput';
    stdLabel.innerHTML = 'Data File (.std)';
    // .seq file input
    const seqInput = document.createElement('input');
    seqInput.type = 'file';
    seqInput.accept = '.seq';
    seqInput.required = true;
    seqInput.id = 'milsoftSeqInput';
    const seqLabel = document.createElement('label');
    seqLabel.htmlFor = 'milsoftSeqInput';
    seqLabel.innerText = 'Equipment File (.seq)';
    // - Submit div
    const submitButton = _getSubmitButton('Import');
    const submitDiv = _getSubmitDiv(submitButton);
    // - Feature
    const feature = controller.getObservables()[0];
    // - Event listeners
    nameInput.addEventListener('change', function() {
        let newName = this.value.trim();
        if (newName === '') {
            newName = 'Default Name';
        }
        feature.setProperty('feederNameM', newName, 'formProps');
        const fileExistsUrl = {
            method: 'GET',
            url: `/uniqObjName/Feeder/${gThisOwner}/${newName}/${gThisModelName}`
        }
        feature.setProperty('fileExistsUrl', fileExistsUrl, 'urlProps');
    });
    stdInput.addEventListener('change', function() {
        const stdFile = this.files[0];
        feature.setProperty('stdFile', stdFile, 'formProps');

    });
    seqInput.addEventListener('change', function() {
        const seqFile = this.files[0];
        feature.setProperty('seqFile', seqFile, 'formProps');
    });
    // - Modal
    const modal = new Modal();
    modal.addStyleClass('outerModal',   'divElement');
    modal.addStyleClass('fitContent',   'divElement');
    submitButton.addEventListener('click', function() {
        modal.showProgress(true, 'Importing file...', 'caution');
        controller.submitFeature(modal);
    });
    modal.setTitle('Milsoft Conversion');
    modal.addStyleClass('horizontalFlex',       'titleElement');
    modal.addStyleClass('centerMainAxisFlex',   'titleElement');
    modal.addStyleClass('centerCrossAxisFlex',  'titleElement');
    modal.insertTBodyRow([nameLabel, nameInput]);
    modal.insertTBodyRow([stdLabel, stdInput]);
    modal.insertTBodyRow([seqLabel, seqInput]);
    modal.insertElement(submitDiv);
    modal.addStyleClass('verticalFlex',         'containerElement');
    modal.addStyleClass('centerMainAxisFlex',   'containerElement');
    modal.addStyleClass('centerCrossAxisFlex',  'containerElement');
    return modal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getWindmilDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const feature = new Feature({
        geometry: { 'coordinates': [null, null], 'type': 'Point' },
        properties: {
            treeKey: 'modal:windmil',
            urlProps: {
                fileExistsUrl: {
                    method: 'GET',
                    url: `/uniqObjName/Feeder/${gThisOwner}/Default Name/${gThisModelName}`
                },
                pollUrl: {
                    method: 'GET',
                    url: `/checkConversion/${gThisModelName}/${gThisOwner}`
                },
                submitUrl: {
                    method: 'POST',
                    url: `/milsoftImport/${gThisOwner}`                    
                }
            },
            formProps: {
                modelName: gThisModelName,
                feederNameM: 'Default Name',
                feederNum: gThisFeederNum,
                stdFile: '',
                seqFile: ''
            }
        },
        type: 'Feature'
    });
    featureGraph.insertObservable(feature);
    const controller = new FeatureController(featureGraph, ['modal:windmil']);
    const modal = _getWindmilModal(controller);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('Windmil conversion...');
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
    });
    return div;
}

/**
 * @param {FeatureController} controller - a ControllerInterface instance
 * @returns {Modal}
 */
function _getGridlabdModal(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('"controller" argument must be an instance of FeatureController.');
    }
    // - Name input
    const nameInput = document.createElement('input');
    nameInput.required = true;
    nameInput.id = 'gridlabdNameInput';
    const nameLabel = document.createElement('label');
    nameLabel.htmlFor = 'gridlabdNameInput';
    nameLabel.innerText = 'Name';
    // - .glm file input
    const glmInput = document.createElement('input');
    glmInput.type = 'file';
    glmInput.accept = '.glm';
    glmInput.required = true;
    glmInput.id = 'glmInput';
    const glmLabel = document.createElement('label');
    glmLabel.htmlFor = 'glmInput';
    glmLabel.innerHTML = 'Data File (.glm)';
    // - Submit div
    const submitButton = _getSubmitButton('Import');
    const submitDiv = _getSubmitDiv(submitButton);
    // - Feature
    const feature = controller.getObservables()[0];
    // - Event listeners
    nameInput.addEventListener('change', function() {
        let newName = this.value.trim();
        if (newName === '') {
            newName = 'Default Name';
        }
        feature.setProperty('feederNameG', newName, 'formProps');
        const fileExistsUrl = {
            method: 'GET',
            url: `/uniqObjName/Feeder/${gThisOwner}/${newName}/${gThisModelName}`
        }
        feature.setProperty('fileExistsUrl', fileExistsUrl, 'urlProps');
    });
    glmInput.addEventListener('change', function() {
        const glmFile = this.files[0];
        feature.setProperty('glmFile', glmFile, 'formProps');
    });
    // - Modal
    const modal = new Modal();
    modal.addStyleClass('outerModal',   'divElement');
    modal.addStyleClass('fitContent',   'divElement');
    submitButton.addEventListener('click', function() {
        modal.showProgress(true, 'Importing file...', 'caution');
        controller.submitFeature(modal);
    });
    modal.setTitle('GridLABD-D Conversion');
    modal.addStyleClass('horizontalFlex',       'titleElement');
    modal.addStyleClass('centerMainAxisFlex',   'titleElement');
    modal.addStyleClass('centerCrossAxisFlex',  'titleElement');
    modal.insertTBodyRow([nameLabel, nameInput]);
    modal.insertTBodyRow([glmLabel, glmInput]);
    modal.insertElement(submitDiv);
    modal.addStyleClass('verticalFlex',         'containerElement');
    modal.addStyleClass('centerMainAxisFlex',   'containerElement');
    modal.addStyleClass('centerCrossAxisFlex',  'containerElement');
    return modal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getGridlabdDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const feature = new Feature({
        geometry: { 'coordinates': [null, null], 'type': 'Point' },
        properties: {
            treeKey: 'modal:gridlabd',
            urlProps: {
                fileExistsUrl: {
                    method: 'GET',
                    url: `/uniqObjName/Feeder/${gThisOwner}/Default Name/${gThisModelName}`
                },
                pollUrl: {
                    method: 'GET',
                    url: `/checkConversion/${gThisModelName}/${gThisOwner}`
                },
                submitUrl: {
                    method: 'POST',
                    url: `/gridlabdImport/${gThisOwner}`
                }
            },
            formProps: {
                modelName: gThisModelName,
                feederNameG: 'Default Name',
                feederNum: gThisFeederNum,
                glmFile: ''
            }
        },
        type: 'Feature'
    });
    featureGraph.insertObservable(feature);
    const controller = new FeatureController(featureGraph, ['modal:gridlabd']);
    const modal = _getGridlabdModal(controller);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('GridLAB-D conversion...');
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
    });
    return div;
}
/**
 * @param {FeatureController} controller - a ControllerInterface instance
 * @returns {Modal}
 */
function _getCymdistModal(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('"controller" argument must be an instance of FeatureController.');
    }
    // - Name input
    const nameInput = document.createElement('input');
    nameInput.required = true;
    nameInput.id = 'cymdistNameInput';
    const nameLabel = document.createElement('label');
    nameLabel.htmlFor = 'cymdistNameInput';
    nameLabel.innerText = 'Name';
    // - .mdb file input
    const mdbInput = document.createElement('input');
    mdbInput.type = 'file';
    mdbInput.accept = '.mdb';
    mdbInput.required = true;
    mdbInput.id = 'mdbInput';
    const mdbLabel = document.createElement('label');
    mdbLabel.htmlFor = 'mdbInput';
    mdbLabel.innerHTML = 'Network File (.mdb)';
    // - Submit div
    const submitButton = _getSubmitButton('Import');
    const submitDiv = _getSubmitDiv(submitButton);
    // - Feature
    const feature = controller.getObservables()[0];
    // - Event listeners
    nameInput.addEventListener('click', function() {
        let newName = this.value.trim();
        if (newName === '') {
            newName = 'Default Name';
        }
        feature.setProperty('feederNameC', newName, 'formProps');
        const fileExistsUrl = {
            method: 'GET',
            url: `/uniqObjName/Feeder/${gThisOwner}/${newName}/${gThisModelName}`
        }
        feature.setProperty('fileExistsUrl', fileExistsUrl, 'urlProps');
    });
    mdbInput.addEventListener('change', function() {
        const mdbFile = this.files[0];
        feature.setProperty('mdbNetFile', mdbFile, 'formProps');
    });
    // - Modal
    const modal = new Modal();
    modal.addStyleClass('outerModal',   'divElement');
    modal.addStyleClass('fitContent',   'divElement');
    submitButton.addEventListener('click', function() {
        modal.showProgress(true, 'Importing file...', 'caution');
        controller.submitFeature(modal);
    });
    modal.setTitle('Cyme Conversion');
    modal.addStyleClass('horizontalFlex',       'titleElement');
    modal.addStyleClass('centerMainAxisFlex',   'titleElement');
    modal.addStyleClass('centerCrossAxisFlex',  'titleElement');
    modal.insertTBodyRow([nameLabel, nameInput]);
    modal.insertTBodyRow([mdbLabel, mdbInput]);
    modal.insertElement(submitDiv);
    modal.addStyleClass('verticalFlex',         'containerElement');
    modal.addStyleClass('centerMainAxisFlex',   'containerElement');
    modal.addStyleClass('centerCrossAxisFlex',  'containerElement');
    return modal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getCymdistDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const feature = new Feature({
        geometry: { 'coordinates': [null, null], 'type': 'Point' },
        properties: {
            treeKey: 'modal:cymdist',
            urlProps: {
                fileExistsUrl: {
                    method: 'GET',
                    url: `/uniqObjName/Feeder/${gThisOwner}/Default Name/${gThisModelName}`
                },
                pollUrl: {
                    method: 'GET',
                    url: `/checkConversion/${gThisModelName}/${gThisOwner}`
                },
                submitUrl: {
                    method: 'POST',
                    url: `/cymeImport/${gThisOwner}`
                }
            },
            formProps: {
                modelName: gThisModelName,
                feederNum: gThisFeederNum,
                feederNameC: 'Default Name',
                mdbNetFile: ''
            }
        },
        type: 'Feature'
    });
    featureGraph.insertObservable(feature);
    const controller = new FeatureController(featureGraph, ['modal:cymdist']);
    const modal = _getCymdistModal(controller);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('CYMDIST conversion...');
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
    });
    return div;
}

/**
 * @param {FeatureController} controller - a ControllerInterface instance
 * @returns {Modal}
 */
function _getOpendssModal(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('"controller" argument must be an instance of FeatureController.');
    }
    // - Name input
    const nameInput = document.createElement('input');
    nameInput.required = true;
    nameInput.id = 'opendssNameInput';
    const nameLabel = document.createElement('label');
    nameLabel.htmlFor = 'opendssNameInput';
    nameLabel.innerText = 'Name';
    // - .dss file input
    const dssInput = document.createElement('input');
    dssInput.type = 'file';
    dssInput.accept = '.dss';
    dssInput.required = true;
    dssInput.id = 'dssInput';
    const dssLabel = document.createElement('label');
    dssLabel.htmlFor = 'dssInput';
    dssLabel.innerHTML = 'Data File (.dss)';
    // - Submit div
    const submitButton = _getSubmitButton('Import');
    const submitDiv = _getSubmitDiv(submitButton);
    // - Feature
    const feature = controller.getObservables()[0];
    // - Event listeners 
    nameInput.addEventListener('change', function() {
        let newName = this.value.trim();
        if (newName === '') {
            newName = 'Default Name';
        }
        feature.setProperty('feederNameOpendss', newName, 'formProps');
        const fileExistsUrl = {
            method: 'GET',
            url: `/uniqObjName/Feeder/${gThisOwner}/${newName}/${gThisModelName}`
        }
        feature.setProperty('fileExistsUrl', fileExistsUrl, 'urlProps');
    });
    dssInput.addEventListener('change', function() {
        const dssFile = this.files[0];
        feature.setProperty('dssFile', dssFile, 'formProps');
    });
    // - Modal
    const modal = new Modal();
    modal.addStyleClass('outerModal',   'divElement');
    modal.addStyleClass('fitContent',   'divElement');
    submitButton.addEventListener('click', function() {
        modal.showProgress(true, 'Importing .dss file...', 'caution');
        controller.submitFeature(modal);
    });
    modal.setTitle('OpenDSS Conversion');
    modal.addStyleClass('horizontalFlex',       'titleElement');
    modal.addStyleClass('centerMainAxisFlex',   'titleElement');
    modal.addStyleClass('centerCrossAxisFlex',  'titleElement');
    modal.insertTBodyRow([nameLabel, nameInput]);
    modal.insertTBodyRow([dssLabel, dssInput]);
    modal.insertElement(submitDiv);
    modal.addStyleClass('verticalFlex',         'containerElement');
    modal.addStyleClass('centerMainAxisFlex',   'containerElement');
    modal.addStyleClass('centerCrossAxisFlex',  'containerElement');
    return modal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getOpendssDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const feature = new Feature({
        geometry: { 'coordinates': [null, null], 'type': 'Point' },
        properties: {
            treeKey: 'modal:opendss',
            urlProps: {
                fileExistsUrl: {
                    method: 'GET',
                    url: `/uniqObjName/Feeder/${gThisOwner}/Default Name/${gThisModelName}`
                },
                pollUrl: {
                    method: 'GET',
                    url: `/checkConversion/${gThisModelName}/${gThisOwner}`
                },
                submitUrl: {
                    method: 'POST',
                    url: `/opendssImport/${gThisOwner}`
                }
            },
            formProps: {
                modelName: gThisModelName,
                feederNameOpendss: 'Default Name',
                feederNum: gThisFeederNum,
                dssFile: ''
            }
        },
        type: 'Feature'
    });
    featureGraph.insertObservable(feature);
    const controller = new FeatureController(featureGraph, ['modal:opendss']);
    const modal = _getOpendssModal(controller);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('OpenDSS conversion...');
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
    });
    return div;
}

/**
 * @param {FeatureController} controller - a ControllerInterface instance
 * @returns {Modal}
 */
function _getAmiModal(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('"controller" argument must be an instance of FeatureController.');
    }
    // - csv file input
    const amiInput = document.createElement('input');
    amiInput.type = 'file';
    amiInput.accept = '.csv';
    amiInput.required = true;
    amiInput.id = 'amiInput'; 
    const amiLabel = document.createElement('label');
    amiLabel.htmlFor = 'amiInput';
    amiLabel.innerHTML = 'File containing AMI load data (.csv)';
    // - Format help anchor
    const anchor = document.createElement('a');
    anchor.href = 'https://github.com/dpinney/omf/wiki/Tools-~-gridEdit#ami-load-modeling';
    anchor.textContent = 'Format Help';
    anchor.target = '_blank';
    // - Note div
    const noteDiv = _getHorizontalFlexDiv();
    noteDiv.classList.add('centerCrossAxisFlex');
    noteDiv.style.alignSelf = 'start';
    const span = document.createElement('span');
    span.textContent = 'Note: model "Simulation Start Data" should lie within the AMI profile\'s dates';
    noteDiv.appendChild(span);
    // - Submit div
    const submitButton = _getSubmitButton('Import');
    const submitDiv = _getSubmitDiv(submitButton);
    // - Feature
    const feature = controller.getObservables()[0];
    // - Event listeners
    amiInput.addEventListener('change', function() {
        const amiFile = this.files[0];
        feature.setProperty('amiFile', amiFile, 'formProps');
    });
    // - Modal
    const modal = new Modal();
    modal.addStyleClass('outerModal',   'divElement');
    modal.addStyleClass('fitContent',   'divElement');
    submitButton.addEventListener('click', function() {
        modal.showProgress(true, 'Importing file...', 'caution');
        controller.submitFeature(modal);
    });
    modal.setTitle('AMI Profiles');
    modal.addStyleClass('horizontalFlex',       'titleElement');
    modal.addStyleClass('centerMainAxisFlex',   'titleElement');
    modal.addStyleClass('centerCrossAxisFlex',  'titleElement');
    modal.insertTBodyRow([anchor]);
    modal.insertTBodyRow([amiLabel, amiInput]);
    modal.insertElement(noteDiv);
    modal.insertElement(submitDiv);
    modal.addStyleClass('verticalFlex',         'containerElement');
    modal.addStyleClass('centerMainAxisFlex',   'containerElement');
    modal.addStyleClass('centerCrossAxisFlex',  'containerElement');
    return modal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getAmiDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const feature = new Feature({
        geometry: { 'coordinates': [null, null], 'type': 'Point' },
        properties: {
            treeKey: 'modal:ami',
            urlProps: {
                fileExistsUrl: {
                    method: 'GET',
                    url: `/uniqObjName/Feeder/${gThisOwner}/${gThisFeederName}/${gThisModelName}`
                },
                pollUrl: {
                    method: 'GET',
                    url: `/checkConversion/${gThisModelName}/${gThisOwner}`
                },
                submitUrl: {
                    method: 'POST',
                    url: `/loadModelingAmi/${gThisOwner}/${gThisFeederName}`
                }
            },
            formProps: {
                modelName: gThisModelName,
                amiFile: ''
            }
        },
        type: 'Feature'
    });
    featureGraph.insertObservable(feature);
    const controller = new FeatureController(featureGraph, ['modal:ami']);
    const modal = _getAmiModal(controller);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('Add AMI Profiles...');
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
    });
    return div;
}

/**
 * @param {FeatureController} controller - a ControllerInterface instance
 * @returns {Modal}
 */
function _getAttachmentsModal(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('"controller" argument must be an instance of FeatureController.');
    }
    // - Feature
    const feature = controller.getObservables()[0];
    // - Modal
    const mainModal = new Modal();
    mainModal.addStyleClass('outerModal', 'divElement');
    mainModal.setTitle('Attachments');
    mainModal.addStyleClass('horizontalFlex',       'titleElement');
    mainModal.addStyleClass('centerMainAxisFlex',   'titleElement');
    mainModal.addStyleClass('centerCrossAxisFlex',  'titleElement');
    const attachments = feature.getProperty('attachments', 'meta');
    for (const [key, val] of Object.entries(attachments)) {
        const modal = new Modal();
        const attachmentTitleDiv = _getHorizontalFlexDiv();
        attachmentTitleDiv.classList.add('centerCrossAxisFlex');
        const span = document.createElement('span');
        span.textContent = key;
        attachmentTitleDiv.appendChild(span);
        modal.insertElement(attachmentTitleDiv);
        modal.addStyleClass('horizontalFlex',       'titleElement');
        modal.addStyleClass('centerCrossAxisFlex',  'titleElement');
        const textArea = document.createElement('textarea');
        textArea.value = val;
        textArea.addEventListener('change', function() {
            attachments[key] = textArea.value;
        });
        modal.insertElement(textArea);
        mainModal.insertElement(modal.divElement);
    }
    return mainModal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getAttachmentsDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const controller = new FeatureController(featureGraph, ['omd']); 
    const modal = _getAttachmentsModal(controller);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('Attachments...');
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
    });
    return div;
}

/**
 * @param {FeatureController} controller - a ControllerInterface instance
 * @returns {Modal}
 */
function _getClimateModal(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('"controller" argument must be an instance of FeatureController.');
    }
    // - Climate import select
    const climateImportSelect = document.createElement('select');
    climateImportSelect.name = 'climateImportOption';
    let option = document.createElement('option');
    option.text = 'USCRN import';
    option.value = 'USCRNImport';
    climateImportSelect.add(option);
    option = document.createElement('option');
    option.text = 'tmy import';
    option.value = 'tmyImport';
    climateImportSelect.add(option);
    // - USCRN year select
    const uscrnYearSelect = document.createElement('select');
    uscrnYearSelect.id = 'uscrnYearSelect';
    uscrnYearSelect.name = 'uscrnYear';
    [2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019].forEach(year => {
        const option = document.createElement('option');
        option.text = year;
        option.value = year;
        uscrnYearSelect.add(option);
    });
    // - USCRN station select
    const uscrnStationSelect = document.createElement('select');
    uscrnStationSelect.name = 'uscrnStation';
    ["AK_Bethel_87_WNW", "AK_Cordova_14_ESE", "AK_Deadhorse_3_S", "AK_Denali_27_N", "AK_Fairbanks_11_NE", "AK_Glennallen_64_N", "AK_Gustavus_2_NE",
	"AK_Ivotuk_1_NNE", "AK_Kenai_29_ENE", "AK_King_Salmon_42_SE", "AK_Metlakatla_6_S", "AK_Port_Alsworth_1_SW", "AK_Red_Dog_Mine_3_SSW", "AK_Ruby_44_ESE",
    "AK_Sand_Point_1_ENE", "AK_Selawik_28_E", "AK_Sitka_1_NE", "AK_St._Paul_4_NE", "AK_Tok_70_SE", "AK_Toolik_Lake_5_ENE", "AK_Utqiagvik_formerly_Barrow_4_ENE",
    "AK_Yakutat_3_SSE", "AL_Brewton_3_NNE", "AL_Clanton_2_NE", "AL_Courtland_2_WSW", "AL_Cullman_3_ENE", "AL_Fairhope_3_NE", "AL_Gadsden_19_N", "AL_Gainesville_2_NE",
	"AL_Greensboro_2_WNW", "AL_Highland_Home_2_S", "AL_Muscle_Shoals_2_N", "AL_Northport_2_S", "AL_Russellville_4_SSE", "AL_Scottsboro_2_NE", "AL_Selma_6_SSE",
	"AL_Selma_13_WNW", "AL_Talladega_10_NNE", "AL_Thomasville_2_S", "AL_Troy_2_W", "AL_Valley_Head_1_SSW", "AR_Batesville_8_WNW", "AZ_Elgin_5_S", "AZ_Tucson_11_W",
	"AZ_Williams_35_NNW", "AZ_Yuma_27_ENE", "CA_Bodega_6_WSW", "CA_Fallbrook_5_NE", "CA_Merced_23_WSW", "CA_Redding_12_WNW", "CA_Santa_Barbara_11_W", "CA_Stovepipe_Wells_1_SW",
	"CA_Yosemite_Village_12_W", "CO_Boulder_14_W", "CO_Cortez_8_SE", "CO_Dinosaur_2_E", "CO_La_Junta_17_WSW", "CO_Montrose_11_ENE", "CO_Nunn_7_NNE", "FL_Everglades_City_5_NE",
	"FL_Sebring_23_SSE", "FL_Titusville_7_E", "GA_Brunswick_23_S", "GA_Newton_8_W", "GA_Newton_11_SW", "GA_Watkinsville_5_SSE", "HI_Hilo_5_S", "HI_Mauna_Loa_5_NNE",
	"IA_Des_Moines_17_E", "ID_Arco_17_SW", "ID_Murphy_10_W", "IL_Champaign_9_SW", "IL_Shabbona_5_NNE", "IN_Bedford_5_WNW", "KS_Manhattan_6_SSW", "KS_Oakley_19_SSW",
	"KY_Bowling_Green_21_NNE", "KY_Versailles_3_NNW", "LA_Lafayette_13_SE", "LA_Monroe_26_N", "ME_Limestone_4_NNW", "ME_Old_Town_2_W", "MI_Chatham_1_SE", "MI_Gaylord_9_SSW",
	"MN_Goodridge_12_NNW", "MN_Sandstone_6_W", "MO_Chillicothe_22_ENE", "MO_Joplin_24_N", "MO_Salem_10_W", "MS_Holly_Springs_4_N", "MS_Newton_5_ENE", "MT_Dillon_18_WSW",
	"MT_Lewistown_42_WSW", "MT_St._Mary_1_SSW", "MT_Wolf_Point_29_ENE", "MT_Wolf_Point_34_NE", "NC_Asheville_8_SSW", "NC_Asheville_13_S", "NC_Durham_11_W", "ND_Jamestown_38_WSW",
	"ND_Medora_7_E", "ND_Northgate_5_ESE", "NE_Harrison_20_SSE", "NE_Lincoln_8_ENE", "NE_Lincoln_11_SW", "NE_Whitman_5_ENE", "NH_Durham_2_N", "NH_Durham_2_SSW", "NM_Las_Cruces_20_N",
	"NM_Los_Alamos_13_W", "NM_Socorro_20_N", "NV_Baker_5_W", "NV_Denio_52_WSW", "NV_Mercury_3_SSW", "NY_Ithaca_13_E", "NY_Millbrook_3_W", "OH_Wooster_3_SSE", "OK_Goodwell_2_E",
	"OK_Goodwell_2_SE", "OK_Stillwater_2_W", "OK_Stillwater_5_WNW", "ON_Egbert_1_W", "OR_Coos_Bay_8_SW", "OR_Corvallis_10_SSW", "OR_John_Day_35_WNW", "OR_Riley_10_WSW",
	"PA_Avondale_2_N", "RI_Kingston_1_NW", "RI_Kingston_1_W", "SC_Blackville_3_W", "SC_McClellanville_7_NE", "SD_Aberdeen_35_WNW", "SD_Buffalo_13_ESE", "SD_Pierre_24_S",
	"SD_Sioux_Falls_14_NNE", "TN_Crossville_7_NW", "TX_Austin_33_NW", "TX_Bronte_11_NNE", "TX_Edinburg_17_NNE", "TX_Monahans_6_ENE", "TX_Muleshoe_19_S", "TX_Palestine_6_WNW",
	"TX_Panther_Junction_2_N", "TX_Port_Aransas_32_NNE", "UT_Brigham_City_28_WNW", "UT_Torrey_7_E", "VA_Cape_Charles_5_ENE", "VA_Charlottesville_2_SSE", "WA_Darrington_21_NNE",
    "WA_Quinault_4_NE", "WA_Spokane_17_SSW", "WI_Necedah_5_WNW", "WV_Elkins_21_ENE", "WY_Lander_11_SSE", "WY_Moose_1_NNE", "WY_Sundance_8_NNW"].forEach(station => {
        const option = document.createElement('option');
        option.text = station;
        option.value = station;
        uscrnStationSelect.add(option); 
    });
    // - tmy zip code input
    const tmyInput = document.createElement('input');
    tmyInput.id = 'tmyInput';
    tmyInput.name = 'tmyInput';
    const tmyInputLabel = document.createElement('label');
    tmyInputLabel.htmlFor = 'tmyInput';
    tmyInputLabel.innerText = 'ZIP code';
    // - Submit div
    const submitButton = _getSubmitButton();
    const submitDiv = _getSubmitDiv(submitButton);
    // - Feature
    const feature = controller.getObservables()[0];
    // - Event listeners
    uscrnYearSelect.addEventListener('change', function() {
        feature.setProperty('uscrnYear', this.value, 'formProps');
    });
    uscrnStationSelect.addEventListener('change', function() {
        feature.setProperty('uscrnStation', this.value, 'formProps');
    });
    tmyInput.addEventListener('change', function() {
        const value = this.value.trim();
        feature.setProperty('zipCode', value, 'formProps');
    });
    // - Modal
    const mainModal = new Modal();
    submitButton.addEventListener('click', function() {
        mainModal.showProgress(true, 'Adding climate data...', 'caution');
        controller.submitFeature(mainModal);
    });
    mainModal.addStyleClass('outerModal', 'divElement');
    mainModal.addStyleClass('fitContent', 'divElement');
    mainModal.setTitle('Climate Change');
    mainModal.addStyleClass('horizontalFlex',       'titleElement');
    mainModal.addStyleClass('centerMainAxisFlex',   'titleElement');
    mainModal.addStyleClass('centerCrossAxisFlex',  'titleElement');
    mainModal.insertTBodyRow([climateImportSelect]);
    const uscrnModal = new Modal();
    uscrnModal.addStyleClass('indent1', 'divElement');
    uscrnModal.insertTBodyRow(['Year', uscrnYearSelect]);
    uscrnModal.insertTBodyRow(['Station', uscrnStationSelect]);
    mainModal.insertElement(uscrnModal.divElement);
    const tmyModal = new Modal();
    tmyModal.addStyleClass('indent1', 'divElement');
    tmyModal.addStyleClass('collapsed', 'divElement');
    tmyModal.insertTBodyRow([tmyInputLabel, tmyInput]);
    mainModal.insertElement(tmyModal.divElement);
    climateImportSelect.addEventListener('change', function() {
        feature.setProperty('climateImportOption', this.value, 'formProps');
        if (this.value === 'USCRNImport') {
            uscrnModal.removeStyleClass('collapsed', 'divElement');
            tmyModal.addStyleClass('collapsed', 'divElement');
        } else {
            uscrnModal.addStyleClass('collapsed', 'divElement');
            tmyModal.removeStyleClass('collapsed', 'divElement');
        }
    });
    const submitDivModal = new Modal();
    submitDivModal.insertElement(submitDiv);
    submitDivModal.addStyleClass('horizontalFlex', 'containerElement');
    submitDivModal.addStyleClass('centerMainAxisFlex',   'containerElement');
    submitDivModal.addStyleClass('centerCrossAxisFlex',  'containerElement');
    mainModal.insertElement(submitDivModal.divElement);
    return mainModal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getClimateDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const feature = new Feature({
        geometry: { 'coordinates': [null, null], 'type': 'Point' },
        properties: {
            treeKey: 'modal:climate',
            urlProps: {
                fileExistsUrl: {
                    method: 'GET',
                    url: `/uniqObjName/Feeder/${gThisOwner}/${gThisFeederName}/${gThisModelName}`
                },
                pollUrl: {
                    method: 'GET',
                    url: `/checkConversion/${gThisModelName}/${gThisOwner}`
                },
                submitUrl: {
                    method: 'POST',
                    url: `/climateChange/${gThisOwner}/${gThisFeederName}`
                }
            },
            formProps: {
                modelName: gThisModelName,
                climateImportOption: 'USCRNImport',
                uscrnStation: 'AK_Bethel_87_WNW',
                uscrnYear: '2006',
                zipCode: ''
            }
        },
        type: 'Feature'
    });
    featureGraph.insertObservable(feature);
    const controller = new FeatureController(featureGraph, ['modal:climate']); 
    const modal =_getClimateModal(controller);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('Climate...');
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
    });
    return div;
}

/**
 * @param {FeatureController} controller - a ControllerInterface instance
 * @returns {Modal}
 */
function _getScadaModal(controller) {
    if (!(controller instanceof FeatureController)) {
        throw Error('"controller" argument must be an instance of FeatureController.');
    }
    // - csv file input
    const scadaInput = document.createElement('input');
    scadaInput.type = 'file';
    scadaInput.accept = '.csv';
    scadaInput.required = true;
    scadaInput.id = 'scadaInput'; 
    const scadaLabel = document.createElement('label');
    scadaLabel.htmlFor = 'scadaInput';
    scadaLabel.innerHTML = 'File containing SCADA load data (.csv)';
    // - Format help anchor
    const anchor = document.createElement('a');
    anchor.href = 'https://github.com/dpinney/omf/wiki/Tools-~-gridEdit#scada-loadshapes';
    anchor.textContent = 'Format Help';
    anchor.target = '_blank';
    // - Note div
    const noteDiv = _getHorizontalFlexDiv();
    noteDiv.classList.add('centerCrossAxisFlex');
    noteDiv.style.alignSelf = 'start';
    const span = document.createElement('span');
    span.textContent = 'Note: model "Simulation Start Data" should lie within the SCADA load\'s dates.';
    noteDiv.appendChild(span);
    // - Submit div
    const submitButton = _getSubmitButton('Import');
    const submitDiv = _getSubmitDiv(submitButton);
    // - Feature
    const feature = controller.getObservables()[0];
    // - Event listeners
    scadaInput.addEventListener('change', function() {
        const scadaFile = this.files[0];
        feature.setProperty('scadaFile', scadaFile, 'formProps');
    }); 
    // - Modal
    const modal = new Modal();
    modal.addStyleClass('outerModal',   'divElement');
    modal.addStyleClass('fitContent',   'divElement');
    submitButton.addEventListener('click', function() {
        modal.showProgress(true, 'Importing file...', 'caution');
        controller.submitFeature(modal);
    });
    modal.setTitle('SCADA Loadshapes');
    modal.addStyleClass('horizontalFlex',       'titleElement');
    modal.addStyleClass('centerMainAxisFlex',   'titleElement');
    modal.addStyleClass('centerCrossAxisFlex',  'titleElement');
    modal.insertTBodyRow([anchor]);
    modal.insertTBodyRow([scadaLabel, scadaInput]);
    modal.insertElement(noteDiv);
    modal.insertElement(submitDiv);
    modal.addStyleClass('verticalFlex',         'containerElement');
    modal.addStyleClass('centerMainAxisFlex',   'containerElement');
    modal.addStyleClass('centerCrossAxisFlex',  'containerElement');
    return modal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getScadaDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const feature = new Feature({
        geometry: { 'coordinates': [null, null], 'type': 'Point' },
        properties: {
            treeKey: 'modal:scada',
            urlProps: {
                fileExistsUrl: {
                    method: 'GET',
                    url: `/uniqObjName/Feeder/${gThisOwner}/${gThisFeederName}/${gThisModelName}`
                },
                pollUrl: {
                    method: 'GET',
                    url: `/checkConversion/${gThisModelName}/${gThisOwner}`
                },
                submitUrl: {
                    method: 'POST',
                    url: `/scadaLoadshape/${gThisOwner}/${gThisFeederName}`
                }
            },
            formProps: {
                modelName: gThisModelName,
                scadaFile: ''
            }
        },
        type: 'Feature'
    });
    featureGraph.insertObservable(feature);
    const controller = new FeatureController(featureGraph, ['modal:scada']);
    const modal = _getScadaModal(controller);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('SCADA Loadshapes...');
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
    });
    return div; 
}

// - TODO: implement replacement function? I need to do components now
/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function _getStaticLoadsToHousesModal(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const modal = new Modal();
    modal.addStyleClass('outerModal',   'divElement');
    modal.addStyleClass('fitContent',   'divElement');
    const triplex_objects = featureGraph.getObservables(f => {
        return f.hasProperty('object') && (f.getProperty('object') === 'triplex_load' || f.getProperty('object') === 'triplex_node')
    });
    if (triplex_objects.length > 0) {
        modal.showProgress(true, 'Converting every triplex load and/or triplex node into a house with children. This could take a few seconds...');
        //
    } else {
        modal.showProgress(false, 'This data has no triplex load or triplex node objects that can be converted into houses.');
        //
    }
    return modal;
}

/**
 * @param {FeatureGraph} featureGraph - an instance of my ObservableGraph interface
 * @returns {HTMLDivElement}
 */
function getStaticLoadsToHousesDiv(featureGraph) {
    if (!(featureGraph instanceof FeatureGraph)) {
        throw Error('"featureGraph argument must be instanceof FeatureGraph');
    }
    const modal = _getStaticLoadsToHousesModal(featureGraph);
    const modalInsert = document.getElementById('modalInsert');
    const div = _getMenuDiv('Static Loads to Houses');
    div.addEventListener('click', function() {
        modalInsert.replaceChildren(modal.divElement);
        modalInsert.classList.add('visible');
    });
    return div;
}

/*********************************/
/* Private convenience functions */
/*********************************/

function _getSubmitButton(text='Submit') {
    const submitButton = document.createElement('button');
    let span = document.createElement('span');
    span.textContent = text;
    submitButton.appendChild(span);
    submitButton.classList.add('horizontalFlex');        
    submitButton.classList.add('centerMainAxisFlex');
    submitButton.classList.add('centerCrossAxisFlex');
    submitButton.classList.add('fullWidth');
    return submitButton;
}

function _getSubmitDiv(button) {
    if (!(button instanceof HTMLButtonElement)) {
        throw TypeError('"button" argument must be instanceof HTMLButtonElement');
    }
    const submitDiv = document.createElement('div');
    submitDiv.classList.add('horizontalFlex');
    submitDiv.classList.add('centerMainAxisFlex');
    submitDiv.classList.add('centerCrossAxisFlex');
    submitDiv.classList.add('halfWidth');
    submitDiv.appendChild(button);
    return submitDiv;
}

function _getMenuDiv(text) {
    if (typeof text !== 'string') {
        throw TypeError('"text" argument must be a string');
    }
    const div = document.createElement('div');
    div.classList.add('hoverable', 'horizontalFlex', 'centerCrossAxisFlex');
    div.textContent = text;
    return div;
}

function _getHorizontalFlexDiv() {
    const div = document.createElement('div');
    div.classList.add('horizontalFlex');
    return div;
}