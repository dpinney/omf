export { ColorModal };
import { Feature, UnsupportedOperationError } from './feature.js';
import { FeatureController } from './featureController.js';
import { LeafletLayer } from './leafletLayer.js';
import { PropTable } from '../v4/ui-components/prop-table/prop-table.js';
import { IconLabelButton } from '../v4/ui-components/iconlabel-button/iconlabel-button.js';
import { LoadingSpan } from '../v4/ui-components/loading-span/loading-span.js';

// - Use voltDumpOlinBarre.csv, currDumpOlinBarre.csv and Olin Barre Fault.omd as examples

class ColorModal { // implements ModalInterface, ObserverInterface
    #colorFiles;            // - Object of ColorFiles
    #selectedColorFilename; // - The name of the file that contains the information for the currently applied coloring
    #selectedColorMapIndex; // - The 0-based index of the column in the color file for the currently applied coloring
    #controller;            // - ControllerInterface instance
    #propTable;             // - PropTable instance
    #loadingSpan
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
        this.#propTable = null;
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
        return this.#propTable.div;
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
        const fileListTable = new PropTable();
        fileListTable.div.classList.add('fileListTable');
        if (Object.values(this.#colorFiles).length > 0) {
            fileListTable.insertTBodyRow({elements: ['Filename', 'Color-by column', 'Apply column color on page load' ]});
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
                            for (const input of [...fileListTable.div.querySelectorAll('input[type="checkbox"][name="colorOnLoadColumnIndex"]')]) {
                                if (input !== this) {
                                    input.checked = false;
                                }
                            }
                        }
                    }
                }
            });
            const colorButton = new IconLabelButton({text: 'Color'});
            colorButton.button.classList.add('-blue');
            colorButton.button.getElementsByClassName('label')[0].classList.add('-white');
            colorButton.button.addEventListener('click', () => {
                const colorMap = colorFile.getColorMaps()[select.value];
                this.#applyColorMap(colorFile, colorMap);
                this.#selectedColorFilename = colorFile.getFilename();
                this.#selectedColorMapIndex = colorMap.getColumnIndex();
            });
            const removeButton = new IconLabelButton({text: 'Remove'});
            removeButton.button.classList.add('-red');
            removeButton.button.getElementsByClassName('label')[0].classList.add('-white');
            removeButton.button.addEventListener('click', () => {
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
            fileListTable.insertTBodyRow({elements: [colorFile.getFilename(), select, checkbox, colorButton.button, removeButton.button]});
        }
        const existingRow = this.#propTable.div.getElementsByClassName('proptablediv');
        // - There was NOT already a fileListTable in place, so insert this fileListTable
        if (existingRow.length === 0) {
            this.#propTable.insertTBodyRow({elements: [fileListTable.div], colspans: [2], position: 'beforeEnd'});
        // - There was already a fileListTable in place. Replace it with this fileListTable
        } else {
            existingRow[0].replaceWith(fileListTable.div);
        }
    }

    /**
     * @returns {undefined}
     */
    remove() {
        if (!this.#removed) {
            this.#observables.forEach(ob => ob.removeObserver(this));
            this.#observables = null;
            this.#propTable.div.remove();
            this.#removed = true;
        }
    }

    /**
     * - Render the modal for the first time
     * @returns {undefined}
     */
    renderContent() {
        // - Build the modal
        const propTable = new PropTable();
        propTable.div.id = 'colorModal';
        propTable.div.addEventListener('click', function(e) {
            e.stopPropagation();
        });
        propTable.insertTHeadRow({elements: ['Color circuit'], colspans: [2]});
        const colorInput = document.createElement('input');
        colorInput.type = 'file';
        colorInput.accept = '.csv';
        colorInput.required = true;
        colorInput.id = 'colorInput';
        const that = this;
        const loadingSpan = new LoadingSpan();
        loadingSpan.span.classList.add('-yellow', '-hidden');
        propTable.insertTHeadRow({elements: [loadingSpan.span], position: 'prepend', colspans: [2]})
        colorInput.addEventListener('change', async function() {
            const file = this.files[0];
            const results = await that.#parseCsv(file);
            if (results.errors.length > 0) {
                // - Papa Parse did parse the file, but there was some kind of small problem. Make the user fix it
                loadingSpan.update({text: `There was an error "${results.errors[0].message}" when parsing the CSV file "${file.name}". Please double-check the CSV formatting.`, show: true, showGif: false});
                return;
            } else {
                loadingSpan.update({text: '', show: false});
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
        propTable.insertTBodyRow({elements: [colorLabel, colorInput]});
        const resetButton = new IconLabelButton({text: 'Reset colors'});
        resetButton.button.classList.add('-blue');
        resetButton.button.getElementsByClassName('label')[0].classList.add('-white');
        resetButton.button.addEventListener('click', () => this.#resetColors());
        propTable.insertTBodyRow({elements: [resetButton.button], colspans: [2]});
        if (this.#propTable === null) {
            this.#propTable = propTable;
            this.#loadingSpan = loadingSpan;
        }
        if (document.body.contains(this.#propTable.div)) {
            this.#propTable.div.replaceWith(propTable.div);
            this.#propTable = propTable;
            this.#loadingSpan.span.replaceWith(loadingSpan.span);
            this.#loadingSpan = loadingSpan;
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

    getColorFiles() {
        return this.#colorFiles;
    }

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
            throw TypeError('The "colorFile" argument must be instanceof ColorFile.');
        }
        if (!(colorMap instanceof ColorMap)) {
            throw TypeError('The "colorMap" argument must be instanceof ColorMap.');
        }
        const notFound = [];
        // - Color everything gray to get rid of default colors
        for (const observable of this.#controller.observableGraph.getObservables()) {
            observable.getObservers().filter(observer => observer instanceof LeafletLayer).forEach(ll => {
                const path = Object.values(ll.getLayer()._layers)[0];
                if (observable.isNode()) {
                    if (!path.options.hasOwnProperty('originalFillColor')) {
                        path.options.originalFillColor = path.options.fillColor;
                    }
                    path.setStyle({
                        fillColor: 'gray'
                    });
                } else if (observable.isLine()) {
                    if (!path.options.hasOwnProperty('originalColor')) {
                        path.options.originalColor = path.options.color;
                    }
                    if (!path.options.hasOwnProperty('colorModalColor')) {
                        path.options.colorModalColor = 'gray';
                    }
                    // - The line is highlighted
                    if (path.options.color === '#7FFF00') {
                        // - pass
                    } else {
                        path.setStyle({
                            color: 'gray'
                        });
                    }
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
                    const path = Object.values(ll.getLayer()._layers)[0];
                    const hex = ColorModal.rgbToHex(obj.color._rgb[0], obj.color._rgb[1], obj.color._rgb[2]);
                    if (observable.isNode()) {
                        path.setStyle({
                            fillColor: hex
                        });
                    }
                    if (observable.isLine()) {
                        observable.options.colorModalColor = hex;
                        path.setStyle({
                            color: hex
                        });
                    }
                });
            } catch (e) {
                notFound.push(name);
            }
        }
        if (notFound.length > 0) {
            console.log(`The following names in the CSV did not match any visible object in the circuit: ${notFound}.`);
        }
        // - Display legend
        colorMap.displayLegend(colorFile.getFilename());
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
                    this.#loadingSpan.update({text: '', show: false});
                } catch (e) {
                    // - Papa Parse did parse the file and didn't find any errors, but I still couldn't create a good ColorFile object, so tell the
                    //   user to remove or fix the file
                    this.#loadingSpan.update({text: `The CSV "${filename}" was parsed, but there was an error "${e.message}" when converting the CSV values into colors. Please double-check the CSV content.`, showGif: false});
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
            observable.getObservers().filter(observer => observer instanceof LeafletLayer).forEach(ll => {
                const path = Object.values(ll.getLayer()._layers)[0];
                if (observable.isNode() && path.options.hasOwnProperty('originalFillColor')) {
                    path.setStyle({
                        fillColor: path.options.originalFillColor
                    });
                } else if (observable.isLine()) {
                    delete path.options.colorModalColor;
                    // - The line is highlighted
                    if (path.options.color === '#7FFF00') {
                        // - pass
                    } else {
                        if (path.options.hasOwnProperty('originalColor')) {
                            path.setStyle({
                                color: path.options.originalColor
                            });
                        }
                    }
                }
            });
        });
        this.#selectedColorFilename = null;
        this.#selectedColorMapIndex = null;
        // - Force refresh the map so that the lines change color
        LeafletLayer.map.setZoom(LeafletLayer.map.getZoom());
    }

    static rgbToHex(r, g, b) {
        return '#' + [r, g, b].map(x => {
            const hex = x.toString(16)
            return hex.length === 1 ? '0' + hex : hex
        }).join('');
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
            throw TypeError('The "text" argument must be typeof string.');
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
                this.#colorMaps[j].mapNameToValue(row[0].toString(), {color: null, value: row[j]});
            }
        }
        Object.values(this.#colorMaps).forEach(cm => cm.generateColorsFromValues());
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
    static tab20Colors = ['#1f77b4', '#d62728', '#2ca02c', '#bcbd22', '#9467bd', '#ff7f0e', '#8c564b', '#17becf', '#e377c2', '#aec7e8', '#ff9896', '#98df8a', '#dbdb8d', '#c5b0d5', '#ffbb78', '#c49c94', '#9edae5', '#f7b6d2', '#7f7f7f', '#c7c7c7'];

    /**
     * @param {string} columnName
     */
    constructor(columnName, columnIndex) {
        if (typeof columnName !== 'string') {
            throw TypeError('The "columnName" argument must be typeof string.');
        }
        if (typeof columnIndex !== 'number') {
            throw TypeError('The "columnIndex" argument must be typeof number.');
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
            throw TypeError('The "filename" argument must be typeof string.');
        }
        const propTable = new PropTable();
        propTable.insertTHeadRow({elements: [filename]});
        propTable.insertTHeadRow({elements: [this.#columnName]});
        const legendDiv = document.createElement('div');
        legendDiv.classList.add('legenddiv');
        const legendGradient = document.createElement('div');
        legendGradient.classList.add('legendgradient');
        legendDiv.append(legendGradient);
        const legendLabels = document.createElement('div');
        legendLabels.classList.add('legendlabels');
        legendDiv.append(legendLabels);
        const values = Object.values(this.#nameToValue).map(obj => obj.value.toString());
        const uniqueValues = [...new Set(values)];
        uniqueValues.sort((a, b) => a.localeCompare(b, 'en', {numeric: true}));
        if (uniqueValues.length > 20) {
            legendLabels.style.justifyContent = 'space-between';
            legendGradient.style.background = `linear-gradient(0deg, ${ColorMap.viridisColors.join(',')})`;
            const numLabels = 5;
            const min = Math.min.apply(null, uniqueValues);
            let span = document.createElement('span');
            // - David wants two decimal points of precision
            span.textContent = min.toFixed(2);
            legendLabels.appendChild(span);
            const max = Math.max.apply(null, uniqueValues);
            const step = (max - min) / numLabels;
            for (let i = 1; i < numLabels; i++) {
                const span = document.createElement('span');
                span.textContent = `${ (min + (step * i)).toFixed(2)}`;
                legendLabels.prepend(span);
            }
            span = document.createElement('span');
            span.textContent = max.toFixed(2);
            legendLabels.prepend(span);
            // - Set 60px per label along the gradient since it's harder to differentiate values than the color blocks
            legendGradient.style.height = `${numLabels * 70}px`;
        } else {
            // - Set each label in the middle of its color
            legendLabels.style.justifyContent = 'space-around';
            const selectedColors = ColorMap.tab20Colors.slice(0, uniqueValues.length);
            const gradientStopIncrement = (100 / selectedColors.length).toFixed(2);
            let gradientString = 'linear-gradient(0deg, ';
            for (let i = 0; i < selectedColors.length; i++) {
                const span = document.createElement('span');
                span.textContent = uniqueValues[i];
                legendLabels.prepend(span);
                gradientString += `${selectedColors[i]} ${i * gradientStopIncrement}% ${(i + 1) * gradientStopIncrement}%`;
                if (i < selectedColors.length - 1) {
                    gradientString += ', ';
                } else {
                    gradientString += ')';
                }
            }
            legendGradient.style.background = gradientString;
            // - Set 30px per color block along the gradient
            legendGradient.style.height = `${selectedColors.length * 30}px`;
        }
        propTable.insertTBodyRow({elements: [legendDiv]});
        const button = new IconLabelButton({text: 'Close'});
        button.button.classList.add('-red');
        button.button.getElementsByClassName('label')[0].classList.add('-white');
        button.button.addEventListener('click', function() {
            document.getElementById('legendInsert').replaceChildren();
        });
        propTable.insertTBodyRow({elements: [button.button]});
        document.getElementById('legendInsert').replaceChildren(propTable.div);
        const draggable = new L.Draggable(propTable.div)
        draggable.enable()
    }

    /**
     * - After all names have been mapped to numeric values, iterate through the colorMap again and generate color objects
     *  - this.#nameToValue[<name>]: { color: null, value: <value> }
     * @returns {undefined}
     */
    generateColorsFromValues() {
        const values = Object.values(this.#nameToValue).map(obj => obj.value.toString());
        const uniqueValues = [...new Set(values)];
        uniqueValues.sort((a, b) => a.localeCompare(b, 'en', {numeric: true}));
        // - If there are greater than 20 unique values, assume those values are numeric and use the viridis color map
        if (uniqueValues.length > 20) {
            const min = Math.min.apply(null, uniqueValues);
            const max = Math.max.apply(null, uniqueValues);
            const func = chroma.scale(ColorMap.viridisColors).domain([min, max]);
            for (const obj of Object.values(this.#nameToValue)) {
                obj.color = func(obj.value);
                // - I round because later on I need to convert the integer values into a hex string
                obj.color._rgb = obj.color._rgb.map(float => Math.round(float));
            };
        // - If there are 20 or fewer unique values, use the tab20 color map
        } else {
            const nameToIndexMap = {};
            for (let i = 0; i < uniqueValues.length; i++) {
                nameToIndexMap[uniqueValues[i]] = i;
            }
            for (const obj of Object.values(this.#nameToValue)) {
                obj.color = chroma(ColorMap.tab20Colors[nameToIndexMap[obj.value]])
            };
        }
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

    getNameToValue() {
        return this.#nameToValue;
    }

    /**
     * @param {string} name - The name of an object to color (e.g. a node name)
     * @param {string|Object} value - When iterating over a CSV for the first time, only values are known. Once a Chroma scale has been generated,
     *  then colors are also mapped
     * @returns {undefined}
     */
    mapNameToValue(name, value) {
        if (typeof name !== 'string') {
            throw TypeError('The "name" argument must be typeof string.');
        }
        if (typeof value !== 'object') {
            throw TypeError('The "value" argument must be typeof object.');
        }
        if (!value.hasOwnProperty('color')) {
            throw TypeError('The "value" argument must have a "color" property.');
        }
        if (!value.hasOwnProperty('value')) {
            throw TypeError('The "value" argument must have a "value" property.');
        }
        if (this.#nameToValue[name] === undefined) {
            this.#nameToValue[name] = {};
        }
        if (value.hasOwnProperty('color')) {
            this.#nameToValue[name].color = value.color;
        }
        if (value.hasOwnProperty('value')) {
            this.#nameToValue[name].value = value.value;
        }
    }

    // *********************
    // ** Private methods **
    // *********************
}