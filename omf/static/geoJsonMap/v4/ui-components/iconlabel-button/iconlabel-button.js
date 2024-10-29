export { IconLabelButton };

/**
 * - This is a class for creating styled buttons
 */
class IconLabelButton {

    // - Use regular DOM access methods through the button property to add variants to components and elements
    button;

    constructor({paths=null, viewBox=null, text=null, tooltip=null, textPosition='append'}={}) {
        this.button = document.createElement('button');
        this.button.classList.add('iconlabel-button');
        if (paths !== null) {
            const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
            svg.classList.add('icon');
            svg.setAttribute('viewBox', viewBox);
            this.button.append(svg);
            for (const path of paths) {
                svg.append(path)
            }
        }
        if (text !== null) {
            const span = document.createElement('span');
            span.classList.add('label');
            if (typeof text === 'string') {
                span.textContent = text;
            } else if (text instanceof Node) {
                span.append(text);
            } else {
                throw TypeError('The "text" argument must be typeof "string" or instanceof "Node".');
            }
            if (textPosition === 'append') {
                this.button.append(span);
            } else if (textPosition === 'prepend') {
                this.button.prepend(span);
            } else {
                throw Error('The "textPosition" argument must be "append" or "prepend".');
            }
        }
        if (tooltip !== null) {
            this.button.title = tooltip;
        }
    }

    /**
     * - If I need to shrink the negative space around an svg, don't try to edit the svg. Instead, just play with negative margins on the svg. I'll
     *   have to do that on a case-by-case basis unfortunately and shouldn't do it in the CSS
     */
    static getTrashCanPaths() {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M10 10V16M14 10V16M4 6H20M15 6V5C15 3.89543 14.1046 3 13 3H11C9.89543 3 9 3.89543 9 5V6M18 6V14M18 18C18 19.1046 17.1046 20 16 20H8C6.89543 20 6 19.1046 6 18V13M6 9V6');
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke-linecap', 'square');
        return [path]
    }

    static getPinPaths() {
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', '12');
        circle.setAttribute('cy', '10');
        circle.setAttribute('r', '3');
        circle.setAttribute('fill', 'none');
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', "M19 9.75C19 15.375 12 21 12 21C12 21 5 15.375 5 9.75C5 6.02208 8.13401 3 12 3C15.866 3 19 6.02208 19 9.75Z");
        path.setAttribute('fill', 'none');
        return [circle, path];
    }

    static getCirclePlusPaths() {
        const paths = [];
        let path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M9 12H15');
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke-linecap', 'square');
        paths.push(path);
        path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M12 9L12 15');
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke-linecap', 'square');
        paths.push(path);
        path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z');
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke-linecap', 'square');
        paths.push(path);
        return paths;
    }

    static getMagnifyingGlassPaths() {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', "M4 11C4 7.13401 7.13401 4 11 4C14.866 4 18 7.13401 18 11C18 14.866 14.866 18 11 18C7.13401 18 4 14.866 4 11ZM11 2C6.02944 2 2 6.02944 2 11C2 15.9706 6.02944 20 11 20C13.125 20 15.078 19.2635 16.6177 18.0319L20.2929 21.7071C20.6834 22.0976 21.3166 22.0976 21.7071 21.7071C22.0976 21.3166 22.0976 20.6834 21.7071 20.2929L18.0319 16.6177C19.2635 15.078 20 13.125 20 11C20 6.02944 15.9706 2 11 2Z");
        path.setAttribute('fill', 'white');
        path.setAttribute('fill-rule', 'evenodd');
        path.setAttribute('clip-rule', 'evenodd');
        return [path];
    }

    static getCircularArrowPaths() {
        const paths = [];
        let path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'm4.5 1.5c-2.4138473 1.37729434-4 4.02194088-4 7 0 4.418278 3.581722 8 8 8s8-3.581722 8-8-3.581722-8-8-8');
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke-linecap', 'round');
        paths.push(path);
        path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'm4.5 5.5v-4h-4');
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke-linecap', 'round');
        paths.push(path);
        return paths
    }

    static getChevronPaths() {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M13.9394 12.0001L8.46973 6.53039L9.53039 5.46973L16.0607 12.0001L9.53039 18.5304L8.46973 17.4697L13.9394 12.0001Z');
        return [path];
    }
}