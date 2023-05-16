export { ColorModal };
import { FeatureController } from './featureController.js';
import { LeafletLayer } from './leafletLayer.js';
import { Modal } from './modal.js';

// - Use voltDumpOlinBarre.csv and Olin Barre Fault.omd as examples

class ColorModal { // implements ModalInterface

    #colorFiles;    // - Array of ColorFiles
    #controller;    // - ControllerInterface instance
    #modal;         // - Modal instance
    #removed;       // - Whether this FeatureEditModal instance has already been deleted

    /**
     * @param {FeatureController} controller - a ControllerInterface instance
     * @returns {undefined}
     */
    constructor(controller) {
        if (!(controller instanceof FeatureController)) {
            throw Error('"controller" argument must be instanceof FeatureController');
        }
        this.#colorFiles = [];
        this.#controller = controller;
        this.#modal = null;
        this.#removed = false;
        this.renderContent();
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

    // - I don't want to set the class of the svg elements here. I couldn't possibly create a class for every possible color of the Viridis spectrum.
    //   Instead, I need to set "fill" and related properties on the path object inside of the svg object

    /**
     * @returns {undefined}
     */
    refreshContent() {
        const fileListModal = new Modal();
        const that = this;
        this.#colorFiles.forEach(cf => {
            const select = document.createElement('select');
            const colorMaps = cf.getColorMaps();
            for (const [idx, cm] of Object.entries(colorMaps)) {
                const option = document.createElement('option');
                option.text = `${cm.getTitle()} (column ${idx})`;
                option.value = idx;
                select.add(option);
            }
            //const buttonDiv = document.createElement('div');
            //buttonDiv.style.display = 'inline-block';
            //buttonDiv.classList.add('horizontalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex', 'halfWidth');
            const button = document.createElement('button');
            button.classList.add('horizontalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex', 'fullWidth');
            const span = document.createElement('span');
            span.textContent = 'Color';
            button.appendChild(span);
            //buttonDiv.appendChild(button);
            button.addEventListener('click', function() {
                const notFound = [];
                const colorMap = colorMaps[select.value];
                // - Color svgs
                for (const [name, obj] of Object.entries(colorMap.getColorMapping())) {
                    try {
                        const key = that.#controller.observableGraph.getKeyForComponent(name);
                        const observable = that.#controller.observableGraph.getObservable(key);
                        observable.getObservers().filter(ob => ob instanceof LeafletLayer).forEach(ll => {
                            const svg = Object.values(ll.getLayer()._layers)[0]._icon.children[0];
                            that.#colorSvg(svg, obj.color);
                        });
                    } catch (e) {
                        notFound.push(name);
                    }
                }
                console.log(`The following names did not match any visible object in the circuit: ${notFound}`);
                // - Display legend
                colorMap.displayLegend(cf.getTitle());
            });
            fileListModal.insertTBodyRow([cf.getTitle(), select, button])
        });
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
            this.#modal.divElement.remove();
            this.#removed = true;
        }
    }

    /**
     * - Render the modal for the first time
     * @returns {undefined}
     */
    renderContent() {
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
        colorInput.addEventListener('change', function() {
            that.#createColorFiles(this.files);
        });
        const colorLabel = document.createElement('label');
        colorLabel.htmlFor = 'colorInput';
        colorLabel.innerHTML = 'File(s) containing bus names and electrical readings (.csv)';
        modal.insertTBodyRow([colorLabel, colorInput]);
        //modal.addStyleClasses(['centeredTable'], 'tableElement');
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
    }

    // ********************
    // ** Public methods **
    // ********************

    // *********************
    // ** Private methods **
    // *********************

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
     * @param {FileList} files - the CSV file(s) to be used to color the graph
     */
    async #createColorFiles(files) {
        if (!(files instanceof FileList)) {
            throw TypeError('"files" argument must be instanceof FileList.');
        }
        for (const f of [...files]) {
            try {
                const cf = new ColorFile();
                await cf.buildColorMaps(f);
                this.#colorFiles.push(cf);
                this.refreshContent();
                this.#modal.setBanner('');
            } catch (e) {
                this.#modal.showProgress(false, `The CSV file "${f.name}" could not be parsed. Please double-check the CSV formatting.`, ['caution']);
            }
        };
    }

    #resetColors() {
        this.#controller.observableGraph.getObservables().forEach(observable => {
            observable.getObservers().filter(ob => ob instanceof LeafletLayer).forEach(ll => {
                // - Only nodes have marker HTMLDivElements
                const markerDiv = Object.values(ll.getLayer()._layers)[0]._icon;
                if (markerDiv !== undefined) {
                    const svg = markerDiv.children[0];
                    svg.style.removeProperty('fill');
                }
            });
        });
    }
}

class ColorFile {

    #colorMaps;
    #title;

    constructor() {
        this.#title = null;
        this.#colorMaps = {};   // - While columns in a CSV can have duplicate headings, they must have unique indexes
    }

    /**
     * - I can't use Promises in a constructor, so this function must be called after the constructor
     * @returns {undefined}
     */
    buildColorMaps(file) {
        if (!(file instanceof File)) {
            throw TypeError('"file" argumnet must be instanceof File.');
        }
        this.#title = file.name;
        const that = this;
        return new Promise(function(resolve, reject) {
            Papa.parse(file, {
                dynamicTyping: true,
                complete: function(results, file) {
                    try {
                        const headerRow = results.data[0];
                        // - i = 1 because the first column contains names, not numeric values
                        for (let i = 1; i < headerRow.length; i++) {
                            const cm = new ColorMap(headerRow[i].toString());
                            that.#colorMaps[i] = cm;
                        }
                        for (let i = 1; i < results.data.length; i++) {
                            const row = results.data[i];
                            for (let j = 1; j < row.length; j++) {
                                that.#colorMaps[j].mapNameToValue(row[0].toString(), {color: null, float: row[j]});
                            }
                        }
                        Object.values(that.#colorMaps).forEach(cm => cm.generateColorsFromFloats());
                        resolve();
                    } catch (e) {
                        reject();
                    }
                }
            });
        });
    }

    getColorMaps() {
        return this.#colorMaps;
    }

    getTitle() {
        return this.#title;
    }
}

class ColorMap {

    #nameToValue;
    #title;
    static viridisColors = ['#440154', '#482173', '#433e85', '#38588c', '#2d708e', '#25858e', '#1e9b8a', '#2ab07f', '#52c569', '#86d549', '#c2df23', '#fde725'];

    constructor(title) {
        this.#nameToValue = {};
        if (typeof title !== 'string') {
            throw TypeError('"title" argument must be typeof string.');
        }
        this.#title = title;
    }

    // ********************
    // ** Public methods **
    // ********************

    /**
     *
     */
    displayLegend(fileName) {
        if (typeof fileName !== 'string') {
            throw TypeError('"fileName" argument must be typeof string.');
        }
        const modal = new Modal();
        modal.divElement.style.width = '300px';
        // - Create titles
        const fileColumnDiv = document.createElement('div');
        fileColumnDiv.style.textAlign = 'center';
        fileColumnDiv.style.wordBreak = 'break-word';
        const fileNameHeading = document.createElement('h2');
        fileNameHeading.style.width = '100%';
        fileNameHeading.textContent = fileName;
        fileColumnDiv.appendChild(fileNameHeading);
        const columnNameHeading = document.createElement('h3');
        columnNameHeading.style.width = '100%';
        columnNameHeading.textContent = this.#title;
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

    getTitle() {
        return this.#title;
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