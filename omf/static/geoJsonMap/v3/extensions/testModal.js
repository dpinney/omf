export { TestModal };
import { Modal } from '../modal.js';
import { FeatureController } from '../featureController.js';

class TestModal {
    #controller;    // - ControllerInterface instance
    #modal;         // - A single Modal instance
    #observables;   // - An array of ObservableInterface instances

    /**
     * @param {Array} observables - an array of ObservableInterface instances
     * @param {FeatureController} controller - a ControllerInterface instance
     * @returns {undefined}
     */
    constructor(observables, controller) {
        if (!(observables instanceof Array)) {
            throw TypeError('"observables" argumnet must be an Array.');
        }
        if (!(controller instanceof FeatureController)) {
            throw Error('"controller" argument must be instanceof FeatureController');
        }
        this.#controller = controller;
        this.#modal = null;
        this.#observables = observables;
        this.renderContent();
    }

    /**
     * - A render a static, read-only table for arbitrary GeoJSON objects. Does not support editing data in any way. See featureEditModal.js for
     *   examples of how to edit data in a table
     */
    renderContent() {
        const modal = new Modal();
        modal.addStyleClasses(['featureEditModal'], 'divElement');
        for (const [key, val] of Object.entries(this.#observables[0].getProperties('meta'))) {
            const keySpan = document.createElement('span');
            keySpan.textContent = key;
            keySpan.dataset.propertyKey = key;
            keySpan.dataset.propertyNamespace = 'meta';
            const valueSpan = document.createElement('span');
            valueSpan.textContent = val;
            modal.insertTBodyRow([keySpan, valueSpan]);
        }
        modal.addStyleClasses(['centeredTable', 'plainTable'], 'tableElement');
        modal.addStyleClasses(['verticalFlex', 'centerMainAxisFlex', 'centerCrossAxisFlex'], 'containerElement');
        if (this.#modal === null) {
            this.#modal = modal;
        }
        if (document.body.contains(this.#modal.divElement)) {
            this.#modal.divElement.replaceWith(modal.divElement);
            this.#modal = modal;
        }
        // - Example of how to get to underlying data
        console.log(this.#controller.observableGraph.getObservable('omd').getProperty('attachments', 'meta').geojsonFiles);
    }

    // ****************************
    // ** ModalInterface methods **
    // ****************************

    getDOMElement() {
        return this.#modal.divElement;
    }
}
