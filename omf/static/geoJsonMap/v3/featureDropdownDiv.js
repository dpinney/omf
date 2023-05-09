export { FeatureDropdownDiv };
import { DropdownDiv } from './dropdownDiv.js';
import { Feature, UnsupportedOperationError } from './feature.js';
import { FeatureController } from './featureController.js';
import { FeatureEditModal } from './featureEditModal.js';

class FeatureDropdownDiv {
    #controller;        // - a ControllerInterface instance
    #dropdownDiv;       // - a DropdownDiv instance
    #featureEditModal;  // - a FeatureEditModal instance
    #observable;        // - an ObservableInterface instance
    #removed;           // - Whether this FeatureDropdownDiv instance has already been deleted

    constructor(observable, controller) {
        if (!(observable instanceof Feature)) {
            throw TypeError('"observable" argument must be instanceof Feature.');
        }
        if (!(controller instanceof FeatureController)) {
            throw TypeError('"controller" argument must be instanceof FeatureController.');
        }
        this.#controller = controller;
        this.#dropdownDiv = null;
        this.#featureEditModal = null;
        this.#observable = observable;
        this.#observable.registerObserver(this);
        this.#removed = false;
        this.renderContent();
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
        this.remove();
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
        // - Do nothing. Any inner FeatureEditModal should update itself
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
        // - Do nothing. Any inner FeatureEditModal should update itself
    } 

    // ****************************
    // ** ModalInterface methods **
    // ****************************

    getDOMElement() {
        return this.#dropdownDiv.divElement;
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

    }

    /**
     * @returns {undefined}
     */
    remove() {
        if (!this.#removed) {
            // - I have to check if this.#featureEditModal === null because often a FeatureDropdownDiv will be rendered, but the user will not have
            //   clicked on it to expand it, so it won't contain a FeatureEditModal
            if (this.#featureEditModal !== null) {
                this.#featureEditModal.remove();
                this.#featureEditModal = null;
            }
            this.#dropdownDiv.divElement.remove();
            this.#dropdownDiv = null;
            this.#observable.removeObserver(this);
            this.#observable = null;
            this.#controller = null;
            this.#removed = true;
        }
    }

    /**
     * @returns {undefined}
     */
    renderContent() {
        const dropdownDiv = new DropdownDiv();
        dropdownDiv.addStyleClasses(['sideNav'], 'divElement');
        const buttonTextSpan = document.createElement('span');
        buttonTextSpan.classList.add('indent2');
        if (this.#observable.hasProperty('object')) {
            if (this.#observable.hasProperty('name')) {
                let div = document.createElement('div');
                div.textContent = this.#observable.getProperty('object');
                buttonTextSpan.appendChild(div);
                div = document.createElement('div');
                div.textContent = this.#observable.getProperty('name');
                buttonTextSpan.appendChild(div);
            } else {
                buttonTextSpan.textContent = this.#observable.getProperty('object');
            }
        } else if (this.#observable.hasProperty('name')) {
            buttonTextSpan.textContent = this.#observable.getProperty('name');
        } else {
            buttonTextSpan.textContent = this.#observable.getProperty('treeKey', 'meta');
        }
        dropdownDiv.setButton(buttonTextSpan, true);
        const that = this;
        dropdownDiv.buttonElement.addEventListener('click', function() {
            if (dropdownDiv.contentDivElement.classList.contains('expanded')) {
                that.#featureEditModal = new FeatureEditModal([that.#observable], that.#controller);
                dropdownDiv.insertElement(that.#featureEditModal.getDOMElement());
            } else {
                that.#featureEditModal.remove();
            }
        });
        if (this.#dropdownDiv === null) {
            this.#dropdownDiv = dropdownDiv;
        }
        if (document.body.contains(this.#dropdownDiv.divElement)) {
            this.#dropdownDiv.divElement.replaceWith(dropdownDiv.divElement);
            this.#dropdownDiv = dropdownDiv;
        }
    }
}