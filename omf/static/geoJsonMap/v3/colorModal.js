export { ColorModal };
import { Feature, UnsupportedOperationError } from './feature.js';
import { FeatureController } from './featureController.js';
import { LeafletLayer } from './leafletLayer.js';
import { Modal } from './modal.js';

// - Use voltDumpOlinBarre.csv, currDumpOlinBarre.csv and Olin Barre Fault.omd as examples

class ColorModal { // implements ModalInterface, ObserverInterface
    #colorFiles;            // - Object of ColorFiles
    #selectedColorFilename; // - The name of the file that contains the information for the currently applied coloring
    #selectedColorMapIndex; // - The 0-based index of the column in the color file for the currently applied coloring
    #controller;            // - ControllerInterface instance
    #modal;                 // - Modal instance
    #observables;           // - An array of ObservableInterface instances
    #removed;               // - Whether this ColorModal instance has already been deleted

    /**
     * @param {Array} observables - an array of ObservableInterface instances
     * @param {FeatureController} controller - a ControllerInterface instance
     */
    constructor(observables, controller) {
        if (!(observables instanceof Array)) {
            throw TypeError('"observables" argumnet must be an Array.');
        }
        if (!(controller instanceof FeatureController)) {
            throw Error('"controller" argument must be instanceof FeatureController.');
        }
        this.#colorFiles = {};
        this.#selectedColorFilename = null;
        this.#selectedColorMapIndex = null;
        this.#controller = controller;
        this.#modal = null;
        this.#observables = observables;
        this.#observables.forEach(ob => ob.registerObserver(this));
        this.#removed = false;
        this.renderContent();
        this.refreshContent();
    }

    // *******************************
    // ** ObserverInterface methods **
    // *******************************

    /**
     * - Remove this ObserverInterface instance (i.e. "this") from the ObservableInterface instance (i.e. "observable") that has been deleted, and
     *   perform other actions as needed
     * @param {Feature} observable - an ObservableInterface instance
     * @returns {undefined}
     */
    handleDeletedObservable(observable) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!(observable instanceof Feature)) {
            throw TypeError('"observable" argument must be instanceof Feature.');
        }
        if (!this.#removed) {
            observable.removeObserver(this);
            const index = this.#observables.indexOf(observable);
            if (index > -1) {
                this.#observables.splice(index, 1);
            } else {
                throw Error('The observable was not found in this.#observables.');
            }
            if (this.#observables.length === 0) {
                this.remove();
            } else {
                this.refreshContent();
            }
        }
    }

    /**
     *
     */
    handleNewObservable(observable) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        throw new UnsupportedOperationError();
    }

    /**
     * - Update this ObserverInterface instance (i.e. "this") based on the coordinates of the ObservableInterface instance (i.e. "observable") that
     *   have just changed and perform other actions as needed
     * @param {Feature} observable - an ObservableInterface instance
     * @param {Array} oldCoordinates - the old coordinates of the observable prior to the change in coordinates
     * @returns {undefined}
     */
    handleUpdatedCoordinates(observable, oldCoordinates) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!(observable instanceof Feature)) {
            throw TypeError('"observable" argument must be instanceof Feature.');
        }
        if (!(oldCoordinates instanceof Array)) {
            throw TypeError('"oldCoordinates" argument must be an array.');
        }
        this.refreshContent();
    }

    /**
     * - Update this ObserverInstance (i.e. "this") based on the property of the ObservableInterface instance (i.e. "observable") that has just
     *   changed and perform other actions as needed
     * @param {Feature} observable - an ObservableInterface instance
     * @param {string} propertyKey - the property key of the property that has been created/changed/deleted in the observable
     * @param {(string|Object)} oldPropertyValue - the previous value of the property that has been created/changed/deleted in the observable
     * @param {string} namespace - the namespace of the property that has been created/changed/deleted in the observable
     * @returns {undefined}
     */
    handleUpdatedProperty(observable, propertyKey, oldPropertyValue, namespace='treeProps') {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!(observable instanceof Feature)) {
            throw TypeError('"observable" argument must be instanceof Feature.');
        }
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be a string.');
        }
        if (typeof namespace !== 'string') {
            throw TypeError('"namespace" argument must be a string.');
        }
        this.refreshContent();
    }

    // ****************************
    // ** ModalInterface methods **
    // ****************************

    getDOMElement() {
        return this.#modal.divElement;
    }

    /**
     * @returns {boolean}
     */
    isRemoved() {
        return this.#removed;
    }

    /**
     * @returns {undefined}
     */
    refreshContent() {
        const fileListModal = new Modal();
        fileListModal.addStyleClasses(['colorModal'], 'divElement');
        if (Object.values(this.#colorFiles).length > 0) {
            fileListModal.insertTHeadRow(['Filename', 'Color-by Column', 'Apply Column Color on Page Load' ]);
            fileListModal.addStyleClasses(['centeredTable'], 'tableElement');
        }
        const attachments = this.#controller.observableGraph.getObservable('omd').getProperty('attachments', 'meta');
        for (const colorFile of Object.values(this.#colorFiles)) {
            const select = document.createElement('select');
            for (const [idx, cm] of Object.entries(colorFile.getColorMaps())) {
                const option = document.createElement('option');
                option.text = `${cm.getColumnName()} (column ${idx})`;
                option.value = idx;
                select.add(option);
            }
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'colorOnLoadColumnIndex';
            select.addEventListener('change', function() {
                // - Get the checkbox and check or uncheck it depending on colorOnLoad
                if (this.value === attachments.coloringFiles[colorFile.getFilename()].colorOnLoadColumnIndex) {
                    checkbox.checked = true;
                } else {
                    checkbox.checked = false;
                }
            });
            // - On load, set the select option to the equivalent colorOnLoad column, if there was one
            if (attachments.coloringFiles[colorFile.getFilename()].hasOwnProperty('colorOnLoadColumnIndex')) {
                for (const op of select.options) {
                    if (op.value === attachments.coloringFiles[colorFile.getFilename()].colorOnLoadColumnIndex) {
                        select.selectedIndex = op.index;
                        checkbox.checked = true;
                    }
                }
            }
            checkbox.addEventListener('change', function() {
                for (const [filename, obj] of Object.entries(attachments.coloringFiles)) {
                    if (filename === colorFile.getFilename()) {
                        if (this.checked) {
                            obj.colorOnLoadColumnIndex = select.value;
                        } else {
                            delete obj.colorOnLoadColumnIndex;
                        }
                    } else {
                        if (this.checked) {
                            delete obj.colorOnLoadColumnIndex;
                            for (const input of [...fileListModal.divElement.querySelectorAll('input[type="checkbox"][name="colorOnLoadColumnIndex"]')]) {
                                if (input !== this) {
                                    input.checked = false;
                                }
                            }
                        }
                    }
                }
            });
            const colorButton = document.createElement('button');
            colorButton.classList.add('horizontalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex', 'fullWidth');
            let span = document.createElement('span');
            span.textContent = 'Color';
            colorButton.appendChild(span);
            colorButton.addEventListener('click', () => {
                const colorMap = colorFile.getColorMaps()[select.value];
                this.#applyColorMap(colorFile, colorMap);
                this.#selectedColorFilename = colorFile.getFilename();
                this.#selectedColorMapIndex = colorMap.getColumnIndex();
            });
            const removeButton = document.createElement('button');
            removeButton.classList.add('horizontalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex', 'fullWidth', 'delete');
            span = document.createElement('span');
            span.textContent = 'Remove';
            removeButton.appendChild(span);
            removeButton.addEventListener('click', () => {
                if (attachments.hasOwnProperty('coloringFiles')) {
                    const filename = colorFile.getFilename();
                    delete attachments.coloringFiles[filename];
                    delete this.#colorFiles[filename];
                    this.refreshContent();
                    if (Object.keys(attachments.coloringFiles).length === 0) {
                        delete attachments.coloringFiles;
                    }
                    this.#selectedColorFilename = null;
                    this.#selectedColorMapIndex = null;
                }
            });
            fileListModal.insertTBodyRow([colorFile.getFilename(), select, checkbox, colorButton, removeButton])
        }
        const containerElement = this.#modal.divElement.getElementsByClassName('div--modalElementContainer')[0];
        const oldModal = containerElement.getElementsByClassName('js-div--modal');
        if (oldModal.length === 0) {
            containerElement.prepend(fileListModal.divElement);
        } else {
            oldModal[0].replaceWith(fileListModal.divElement);
        }
    }

    /**
     * @returns {undefined}
     */
    remove() {
        if (!this.#removed) {
            this.#observables.forEach(ob => ob.removeObserver(this));
            this.#observables = null;
            this.#modal.divElement.remove();
            this.#removed = true;
        }
    }

    /**
     * - Render the modal for the first time
     * @returns {undefined}
     */
    renderContent() {
        // - Build the modal
        const modal = new Modal();
        modal.addStyleClasses(['outerModal', 'fitContent'], 'divElement');
        modal.setTitle('Color Circuit');
        modal.addStyleClasses(['horizontalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex'], 'titleElement');
        const colorInput = document.createElement('input');
        colorInput.type = 'file';
        colorInput.accept = '.csv';
        colorInput.required = true;
        colorInput.id = 'colorInput';
        const that = this;
        colorInput.addEventListener('change', async function() {
            const file = this.files[0];
            const results = await that.#parseCsv(file);
            if (results.errors.length > 0) {
                // - Papa Parse did parse the file, but there was some kind of small problem. Make the user fix it
                that.#modal.showProgress(false, `There was an error "${results.errors[0].message}" when parsing the CSV file "${file.name}". Please double-check the CSV formatting.`, ['caution']);
                return;
            } else {
                that.#modal.setBanner('', ['hidden']);
            }
            if (!attachments.hasOwnProperty('coloringFiles')) {
                attachments.coloringFiles = {};
            }
            attachments.coloringFiles[file.name] = {
                csv: Papa.unparse(results.data)
                // - colorOnLoadColumnIndex should specify a column index if the interface should color on load by a column, otherwise it shouldn't
                //   exist
            }
            that.#createColorFilesFromAttachments();
            that.refreshContent();
        });
        const colorLabel = document.createElement('label');
        colorLabel.htmlFor = 'colorInput';
        colorLabel.innerHTML = 'Add a file containing bus names and electrical readings (.csv)';
        modal.insertTBodyRow([colorLabel, colorInput]);
        modal.addStyleClasses(['centeredTable'], 'tableElement');
        const resetButton = document.createElement('button');
        let span = document.createElement('span');
        span.textContent = 'Reset Colors';
        resetButton.appendChild(span);
        resetButton.classList.add('horizontalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex', 'fullWidth');
        resetButton.addEventListener('click', () => this.#resetColors());
        const submitDiv = document.createElement('div');
        submitDiv.classList.add('horizontalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex', 'halfWidth');
        submitDiv.appendChild(resetButton);
        modal.insertElement(submitDiv);
        modal.addStyleClasses(['verticalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex'], 'containerElement');
        if (this.#modal === null) {
            this.#modal = modal;
        }
        if (document.body.contains(this.#modal.divElement)) {
            this.#modal.divElement.replaceWith(modal.divElement);
            this.#modal = modal;
        }
        // - Apply any colorOnLoad colorings
        this.#createColorFilesFromAttachments();
        const attachments = that.#controller.observableGraph.getObservable('omd').getProperty('attachments', 'meta');
        if (attachments.hasOwnProperty('coloringFiles')) {
            for (const [filename, obj] of Object.entries(attachments.coloringFiles)) {
                if (obj.hasOwnProperty('colorOnLoadColumnIndex')) {
                    const colorFile = this.#colorFiles[filename];
                    const colorMap = colorFile.getColorMaps()[obj.colorOnLoadColumnIndex];
                    // - This if-statement is just in case the colorOnLoadColumnIndex value is invalid for some reason
                    if (colorMap instanceof ColorMap) {
                        this.#applyColorMap(colorFile, colorMap);
                        this.#selectedColorFilename = colorFile.getFilename();
                        this.#selectedColorMapIndex = colorMap.getColumnIndex();
                    }
                }
            }
        }
        // - Add map event listener to re-apply coloring after hide and show
        LeafletLayer.map.on('overlayadd', (layerControlEvent) => {
            if (this.#selectedColorFilename !== null && this.#selectedColorMapIndex !== null) {
                const colorFile = this.#colorFiles[this.#selectedColorFilename];
                const colorMap = this.#colorFiles[this.#selectedColorFilename].getColorMaps()[this.#selectedColorMapIndex];
                this.#applyColorMap(colorFile, colorMap);
            }
        });
    }

    // ********************
    // ** Public methods **
    // ********************

    // *********************
    // ** Private methods **
    // *********************

    /**
     * @param {ColorFile} colorFile
     * @param {ColorMap} colorMap
     * @returns {undefined}
     */
    #applyColorMap(colorFile, colorMap) {
        if (!(colorFile instanceof ColorFile)) {
            throw TypeError('"colorFile" must be instanceof ColorFile.');
        }
        if (!(colorMap instanceof ColorMap)) {
            throw TypeError('"colorMap" must be instanceof ColorMap.');
        }
        const notFound = [];
        // - Color everything gray to get rid of default colors
        for (const ob of this.#controller.observableGraph.getObservables()) {
            ob.getObservers().filter(ob => ob instanceof LeafletLayer).forEach(ll => {
                // - Color nodes gray
                if (Object.values(ll.getLayer()._layers)[0].hasOwnProperty('_icon')) {
                    let svg = Object.values(ll.getLayer()._layers)[0];
                    // - Can be null when node clustering is active
                    if (svg._icon !== null) {
                        svg = svg._icon.children[0];
                        this.#colorSvg(svg, {_rgb: [128, 128, 128, 1]});
                    }
                // - Color lines gray
                } else {
                    const options = Object.values(ll.getLayer()._layers)[0].options;
                    if (options.color !== 'gray') {
                        options.originalColor = options.color;
                    }
                    options.color = 'gray';
                }
            });
        }
        // - Force refresh the map so that the lines change color
        LeafletLayer.map.setZoom(LeafletLayer.map.getZoom());
        // - Actually apply colors from color map (only nodes supported right now, I don't have a CSV with lines to color)
        for (const [name, obj] of Object.entries(colorMap.getColorMapping())) {
            try {
                const key = this.#controller.observableGraph.getKeyForComponent(name);
                const observable = this.#controller.observableGraph.getObservable(key);
                observable.getObservers().filter(ob => ob instanceof LeafletLayer).forEach(ll => {
                    const svg = Object.values(ll.getLayer()._layers)[0]._icon.children[0];
                    this.#colorSvg(svg, obj.color);
                });
            } catch (e) {
                notFound.push(name);
            }
        }
        console.log(`The following names in the CSV did not match any visible object in the circuit: ${notFound}`);
        // - Display legend
        colorMap.displayLegend(colorFile.getFilename());
    }

    /**
     * @param {SVGElement} svg
     * @param {Object} color - an object containing {_rgb: [<r>, <g>, <b>, <a>]}
     * @returns {undefined}
     */
    #colorSvg(svg, color) {
        if (!(svg instanceof SVGElement)) {
            throw TypeError('"svg" argument must be instanceof SVGElement.');
        }
        if (typeof color !== 'object') {
            throw TypeError('"color" argument must be typeof object.');
        }
        if (!color.hasOwnProperty('_rgb')) {
            throw Error('"color" argument must have "_rgb" property.');
        }
        svg.style.fill = `rgba(${color._rgb[0]}, ${color._rgb[1]}, ${color._rgb[2]}, ${color._rgb[3]})`;
    }

    /**
     * @param {File} file
     * @returns {string}
     */
    #parseCsv(file) {
        if (!(file instanceof File)) {
            throw TypeError('"file" argument must be instanceof File.');
        }
        return new Promise(function(resolve, reject) {
            Papa.parse(file, {
                dynamicTyping: true,
                complete: function(results, file) {
                    resolve(results);
                },
                error: function(error, file) {
                    reject(error.message);
                }
            });
        });
    }

    /**
     * - Iterate through the strings in the attachments and create a ColorFile instance for each string
     * @returns {undefined}
     */
    #createColorFilesFromAttachments() {
        const attachments = this.#controller.observableGraph.getObservable('omd').getProperty('attachments', 'meta');
        if (attachments.hasOwnProperty('coloringFiles')) {
            for (const [filename, obj] of Object.entries(attachments.coloringFiles)) {
                // - Create a ColorFile as a container for one or more ColorMaps
                const colorFile = new ColorFile(filename);
                // - Fill the ColorFile with actual data
                try {
                    colorFile.createColorMaps(obj.csv);
                    this.#modal.setBanner('', ['hidden']);
                } catch (e) {
                    // - Papa Parse did parse the file and didn't find any errors, but I still couldn't create a good ColorFile object, so tell the
                    //   user to remove or fix the file
                    this.#modal.showProgress(false, `The CSV "${filename}" was parsed, but there was an error "${e.message}" when converting the CSV values into colors. Please double-check the CSV content.`, ['caution']);
                }
                // - Save the colorFile so that refreshContent() can access it
                this.#colorFiles[filename] = colorFile;
            }
        }
    }

    /**
     * @returns {undefined}
     */
    #resetColors() {
        this.#controller.observableGraph.getObservables().forEach(observable => {
            observable.getObservers().filter(ob => ob instanceof LeafletLayer).forEach(ll => {
                // - Un-color nodes
                if (Object.values(ll.getLayer()._layers)[0].hasOwnProperty('_icon')) {
                    const svg = Object.values(ll.getLayer()._layers)[0]._icon.children[0];
                    svg.style.removeProperty('fill');
                // - Un-color lines
                } else {
                    const options = Object.values(ll.getLayer()._layers)[0].options;
                    if (options.hasOwnProperty('originalColor')) {
                        options.color = options.originalColor;
                    } else {
                        options.color = 'gray';
                    }
                }
            });
        });
        this.#selectedColorFilename = null;
        this.#selectedColorMapIndex = null;
        // - Force refresh the map so that the lines change color
        LeafletLayer.map.setZoom(LeafletLayer.map.getZoom());
    }
}

class ColorFile {

    #colorMaps;
    #filename;

    /**
     * @param {string} filename - the filename of the CSV
     */
    constructor(filename) {
        if (typeof filename !== 'string') {
            throw TypeError('"filename" argument must be typeof string.');
        }
        this.#colorMaps = {};   // - While columns in a CSV can have duplicate headings, they must have unique indexes
        this.#filename = filename;
    }

    /**
     * @param {string} text - the text content of the CSV as a string
     * @returns {undefined}
     */
    createColorMaps(text) {
        if (typeof text !== 'string') {
            throw TypeError('"text" argument must be typeof string.');
        }
        const results = Papa.parse(text, {dynamicTyping: true});
        const headerRow = results.data[0];
        // - i = 1 because the first column contains names, not numeric values
        for (let i = 1; i < headerRow.length; i++) {
            const cm = new ColorMap(headerRow[i].toString(), i);
            this.#colorMaps[i] = cm;
        }
        for (let i = 1; i < results.data.length; i++) {
            const row = results.data[i];
            for (let j = 1; j < row.length; j++) {
                this.#colorMaps[j].mapNameToValue(row[0].toString(), {color: null, float: row[j]});
            }
        }
        Object.values(this.#colorMaps).forEach(cm => cm.generateColorsFromFloats());
    }

    /**
     * @returns {Object}
     */
    getColorMaps() {
        return this.#colorMaps;
    }

    /**
     * @returns {string}
     */
    getFilename() {
        return this.#filename;
    }
}

class ColorMap {

    #columnName;
    #columnIndex;
    #nameToValue;
    static viridisColors = ['#440154', '#482173', '#433e85', '#38588c', '#2d708e', '#25858e', '#1e9b8a', '#2ab07f', '#52c569', '#86d549', '#c2df23', '#fde725'];

    /**
     * @param {string} columnName
     */
    constructor(columnName, columnIndex) {
        if (typeof columnName !== 'string') {
            throw TypeError('"columnName" argument must be typeof string.');
        }
        if (typeof columnIndex !== 'number') {
            throw TypeError('"columnIndex" argument must be typeof number.');
        }
        this.#columnName = columnName;
        this.#nameToValue = {};
        this.#columnIndex = columnIndex;
    }

    // ********************
    // ** Public methods **
    // ********************

    /**
     * @param {string} filename
     * @returns {undefined}
     */
    displayLegend(filename) {
        if (typeof filename !== 'string') {
            throw TypeError('"filename" argument must be typeof string.');
        }
        const modal = new Modal();
        modal.divElement.style.width = '300px';
        // - Create titles
        const fileColumnDiv = document.createElement('div');
        fileColumnDiv.style.textAlign = 'center';
        fileColumnDiv.style.wordBreak = 'break-word';
        const filenameHeading = document.createElement('h2');
        filenameHeading.style.width = '100%';
        filenameHeading.textContent = filename;
        fileColumnDiv.appendChild(filenameHeading);
        const columnNameHeading = document.createElement('h3');
        columnNameHeading.style.width = '100%';
        columnNameHeading.textContent = this.#columnName;
        fileColumnDiv.appendChild(columnNameHeading);
        modal.setTitle(fileColumnDiv);
        // - Create color gradient
        const legendDiv = document.createElement('div');
        legendDiv.classList.add('horizontalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex');
        const legendGradient = document.createElement('div');
        legendGradient.style.height = '400px';
        legendGradient.style.width = '50px';
        legendGradient.style.background = `linear-gradient(0deg, ${ColorMap.viridisColors.join(',')})`;
        legendDiv.appendChild(legendGradient);
        const legendValues = document.createElement('div');
        legendValues.style.height = '400px';
        const floats = Object.values(this.#nameToValue).map(obj => obj.float);
        const min = Math.min.apply(null, floats);
        let span = document.createElement('span');
        span.textContent = min.toFixed(3);
        legendValues.appendChild(span);
        const max = Math.max.apply(null, floats);
        const step = (max - min) / 6;
        for (let i = 1; i < 6; i++) {
            const span = document.createElement('span');
            span.textContent = `${ (min + (step * i)).toFixed(3)}`;
            legendValues.prepend(span);
        }
        span = document.createElement('span');
        span.textContent = max.toFixed(3);
        legendValues.prepend(span);
        legendValues.classList.add('verticalFlex');
        legendValues.style.justifyContent = 'space-between';
        legendValues.style.paddingLeft = '5px';
        legendDiv.appendChild(legendValues);
        modal.insertElement(legendDiv);
        modal.addStyleClasses(['verticalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex'], 'containerElement');
        // - Create button
        const button = document.createElement('button');
        button.classList.add('horizontalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex', 'fullWidth');
        button.addEventListener('click', function() {
            document.getElementById('legendInsert').replaceChildren();
        });
        span = document.createElement('span');
        span.textContent = 'Close';
        button.appendChild(span);
        const buttonDiv = document.createElement('div');
        buttonDiv.classList.add('horizontalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex', 'halfWidth');
        buttonDiv.appendChild(button);
        modal.insertElement(buttonDiv);
        document.getElementById('legendInsert').replaceChildren(modal.divElement);
        $(modal.divElement).draggable();
    }

    /**
     * - After all names have been mapped to numeric values, iterate through the colorMap again and generate color objects
     * @returns {undefined}
     */
    generateColorsFromFloats() {
        const floats = Object.values(this.#nameToValue).map(obj => obj.float);
        const min = Math.min.apply(null, floats);
        const max = Math.max.apply(null, floats);
        const func = chroma.scale(ColorMap.viridisColors).domain([min, max]);
        Object.values(this.#nameToValue).forEach(obj => {
            obj.color = func(obj.float);
        });
    }

    getColorMapping() {
        return this.#nameToValue;
    }

    getColumnName() {
        return this.#columnName;
    }

    getColumnIndex() {
        return this.#columnIndex;
    }

    /**
     * @param {string} name - the name of an object to color (e.g. a node name)
     * @param {string|Object} value - when iterating over a CSV for the first time, the only floats are known. Once a Chroma scale has been generated,
     *      then colors are also mapped
     * @returns {undefined}
     */
    mapNameToValue(name, value) {
        if (typeof name !== 'string') {
            throw TypeError('"name" argument must be typeof string.');
        }
        if (typeof value !== 'object') {
            throw TypeError('"value" argument must be typeof object.');
        }
        if (!value.hasOwnProperty('color')) {
            throw TypeError('"value" argument must have a "color" property.');
        }
        if (!value.hasOwnProperty('float')) {
            throw TypeError('"value" argument must have a "float" property.');
        }
        if (this.#nameToValue[name] === undefined) {
            this.#nameToValue[name] = {};
        }
        if (value.hasOwnProperty('color')) {
            this.#nameToValue[name].color = value.color;
        }
        if (value.hasOwnProperty('float')) {
            this.#nameToValue[name].float = value.float;
        }
    }

    // *********************
    // ** Private methods **
    // *********************
}