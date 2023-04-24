export { FeatureDropdownDiv };
import { DropdownDiv } from './dropdownDiv.js';
import { FeatureController } from './featureController.js';
import { TreeFeatureModal } from './treeFeatureModal.js';
'use strict';

class FeatureDropdownDiv {
    #controller;    // - ControllerInterface instance
    #dropdownDiv;   // - DropdownDiv instance
    #observables;   // - An array of ObservableInterface instances
    #removed;       // - Whether this FeatureDropdownDiv instance has already been deleted

    constructor(controller) {
        if (!(controller instanceof FeatureController)) {
            throw Error('"controller" argument must be an instance of FeatureController');
        }
        this.#controller = controller;
        this.#dropdownDiv = null;
        this.#observables = null;
        this.#removed = false;
        this.renderContent();
    }

    // *******************************
    // ** ObserverInterface methods ** 
    // *******************************

    /**
     * - Remove this ObserverInterface instance (i.e. "this") from the ObservableInterface instance (i.e. "observable") that has been deleted, and
     *   perform other actions as needed
     * @param {Object} observable - an instance of ObservableInterface that this Observer is observing
     * @returns {undefined}
     */
    handleDeletedObservable(observable) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!this.#removed) {
            observable.removeObserver(this);
            this.#observables = this.#observables.filter(ob => ob !== observable);
            if (this.#observables.length === 0) {
                this.remove();
            } else {
                this.renderContent();
            }
        }
    }

    /**
     * - Update this ObserverInterface instance (i.e. "this") based on the coordinates of the ObservableInterface instance (i.e. "observable") that
     *   have just changed and perform other actions as needed
     * @param {Object} observable - an instance of ObservableInterface that this Observer is observing
     * @param {Array} oldCoordinates - the old coordinates of the observable prior to the change in coordinates
     * @returns {undefined}
     */
    handleUpdatedCoordinates(observable, oldCoordinates) {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (!(oldCoordinates instanceof Array)) {
            throw TypeError('"oldCoordinates" argument must be an array.');
        }
        // - Do nothing. Any inner TreeFeatureModal instance should update itself
    } 

    /**
     * - Update this ObserverInstance (i.e. "this") based on the property of the ObservableInterface instance (i.e. "observable") that has just
     *   changed and perform other actions as needed
     * @param {Object} observable - the observable that this observer is observing
     * @param {string} propertyKey - the property key of the property that has been created/changed/deleted in the observable
     * @param {(string|Object)} oldPropertyValue - the previous value of the property that has been created/changed/deleted in the observable
     * @param {string} namespace - the namespace of the property that has been created/changed/deleted in the observable
     * @returns {undefined}
     */
    handleUpdatedProperty(observable, propertyKey, oldPropertyValue, namespace='treeProps') {
        // - The function signature above is part of the ObserverInterface API. The implementation below is not
        if (typeof propertyKey !== 'string') {
            throw TypeError('"propertyKey" argument must be a string.');
        }
        if (typeof namespace !== 'string') {
            throw TypeError('"namespace" argument must be a string.');
        }
        // - Do nothing. Any inner TreeFeatureModal instance should update itself
    } 

    // ********************
    // ** Public methods ** 
    // ********************

    getDOMElement() {
        return this.#dropdownDiv.divElement;
    }

    remove() {
        // - Do not deregister this.#controller from the same observables. It's possible that the controller is managing multiple views 
        //  - The controller has its own remove() method that can be called
        if (!this.#removed) {
            this.#observables.forEach(ob => ob.removeObserver(this));
            this.#observables = null;
            this.#dropdownDiv.divElement.remove(); 
            this.#removed = true;
        }
    }

    renderContent() {
        // - Click on the outermost button if the content div was open to ensure removal of all inner FeatureController instances and TreeFeatureModal
        //   instances
        if (this.#dropdownDiv !== null) {
            if (this.#dropdownDiv.contentDivElement.classList.contains('expanded')) {
                this.#dropdownDiv.buttonElement.click();
            }
        }
        // - Deregister from previous ObservableInterface instances (e.g. let's say this FeatureDropdownDiv has been observing 10 features)
        if (this.#observables !== null) {
            this.#observables.forEach(ob => ob.removeObserver(this));
        }
        // - Ask the controller for the new ObservableInterface instances that should be observed (e.g. let's say a new search has updated the
        //   FeatureController to only manage 5 of the original 10 features)
        this.#observables = this.#controller.getObservables();
        // - Register on the new ObservableInterface instances in case one of them gets deleted and a dropdown div needs to be removed
        this.#observables.forEach(ob => ob.registerObserver(this));
        let dropdownDiv;
        if (this.#observables.length === 1) {
            dropdownDiv = this.#getSingleObservableDropdownDiv(this.#observables[0]);
        } else if (this.#observables.length > 1) {
            dropdownDiv = new DropdownDiv();
            dropdownDiv.setButton(`Search Results: ${this.#observables.length}`, true);
            // - TODO: do I get better or worse performance by adding/removing inner DropdownDiv instances instead of just showing/hiding them?
            this.#observables.forEach(ob => {
                const innerDropdownDiv = this.#getSingleObservableDropdownDiv(ob);
                dropdownDiv.insertElement(innerDropdownDiv.divElement);
            });
        } else {
            throw Error('This TreeFeatureDropdownDiv must observe at least one Feature');
        }
        dropdownDiv.addStyleClass('sideNav');
        if (this.#dropdownDiv === null) {
            this.#dropdownDiv = dropdownDiv;
        } else if (document.body.contains(this.#dropdownDiv.divElement)) {
            this.#dropdownDiv.divElement.replaceWith(dropdownDiv.divElement);
            this.#dropdownDiv = dropdownDiv;
        } else {
            throw Error('Error when creating a FeatureDropdownDiv.');
        }
    }

    // *********************
    // ** Private methods ** 
    // *********************

    /**
     * @param {Feature} - an ObservableInterface instance
     * @returns {DropdownDiv}
     */
    #getSingleObservableDropdownDiv(observable) {
        const dropdownDiv = new DropdownDiv();
        const buttonTextSpan = document.createElement('span');
        if (observable.hasProperty('object')) {
            if (observable.hasProperty('name')) {
                let div = document.createElement('div');
                div.textContent = observable.getProperty('object');
                buttonTextSpan.appendChild(div);
                div = document.createElement('div');
                div.textContent = observable.getProperty('name');
                buttonTextSpan.appendChild(div);
            } else {
                buttonTextSpan.textContent = observable.getProperty('object');
            }
        } else if (observable.hasProperty('name')) {
            buttonTextSpan.textContent = observable.getProperty('name');
        } else {
            buttonTextSpan.textContent = observable.getProperty('treeKey', 'meta');
        }
        dropdownDiv.setButton(buttonTextSpan, true);
        // - Here, the third observer is added to non-modal, non-component features
        // - Here, the fifth observer is added to visible features
        let controller;
        let modal;
        const that = this;
        const treeKey = observable.getProperty('treeKey', 'meta');
        dropdownDiv.buttonElement.addEventListener('click', function() {
            if (dropdownDiv.contentDivElement.classList.contains('expanded')) {
                // - Add sixth observer to visible ObservableInterface instances                
                controller = new FeatureController(that.#controller.observableGraph, [treeKey], that.#controller.isComponentManager);
                modal = new TreeFeatureModal(controller);
                dropdownDiv.insertElement(modal.getDOMElement());
            } else {
                modal.remove();
                controller.remove();
            }
        });
        return dropdownDiv;
    }
}