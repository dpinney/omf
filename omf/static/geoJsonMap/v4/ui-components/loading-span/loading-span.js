export { LoadingSpan };

class LoadingSpan {

    span;
    #gif;
    #label;

    constructor() {
        this.span = document.createElement('span');
        this.span.classList.add('loading-span');
        this.#gif = document.createElement('img');
        this.#gif.classList.add('gif');
        // - Sometimes, the gif comes from the web server
        this.#gif.src = '/static/geoJsonMap/v4/ui-components/loading-span/spinner.gif'
        // - In offline mode, check in the current directory for the gif
        this.#gif.setAttribute('onerror', "this.onerror=null;this.src='./spinner.gif';");
        this.span.append(this.#gif);
        this.#label = document.createElement('span');
        this.#label.classList.add('label');
        this.span.append(this.#label);
    }

    update({text=null, show=true, showGif=true}={}) {
        if (text !== null) {
            if (typeof text === 'string') {
                this.#label.textContent = text;
            } else if (text instanceof Node) {
                this.#label.replaceChildren(text);
            } else {
                throw TypeError('The "text" argument must be typeof "string" or instanceof "Node".');
            }
        }
        if (show) {
            this.span.classList.remove('-hidden');
        } else {
            this.span.classList.add('-hidden');
        }
        if (showGif) {
            this.#gif.classList.remove('-hidden');
        } else {
            this.#gif.classList.add('-hidden');
        }
    }
}