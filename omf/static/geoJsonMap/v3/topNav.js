export { TopNav };

class TopNav {
    navElement;
    #anchor;
    #span;

    constructor(homepageName='<Site Name>', homepageUrl='/') {
        this.navElement = document.createElement('nav');
        this.navElement.classList.add('js-nav--topNav');
        //const button = document.createElement('button');
        //const svg = this.#getHamburgerSvg();
        //button.appendChild(svg);
        //this.navElement.appendChild(button);
        const divPlaceholder = document.createElement('div');
        this.navElement.appendChild(divPlaceholder);
        const div = document.createElement('div');
        this.#anchor = document.createElement('a');
        this.#anchor.setAttribute('href', homepageUrl);
        this.#span = document.createElement('span');
        this.#span.textContent = homepageName;
        this.#anchor.appendChild(this.#span);
        div.appendChild(this.#anchor);
        this.navElement.appendChild(div)
    }

    setHomepageName(val) {
        this.#span.textContent = val;
    }

    setHomepageUrl(val) {
        this.#anchor.setAttribute('href', val);
    }

    #getHamburgerSvg() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', '100%');
        svg.setAttribute('viewBox', '-2.5 -2.5 15 15');
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M0,1L10,1v1h-10v-1M0,5.5L10,5.5v-1h-10v1M0,9L10,9v-1h-10v1');
        svg.appendChild(path);
        return svg;
    }
}