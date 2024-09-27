export { PropTable };

/**
 * - This is a class for creating tables
 */
class PropTable {

    // - Remember: to control the height of a table, the table must be in a div and I must control the height of the div
    div;
    #table;

    constructor() {
        this.div = document.createElement('div');
        this.div.classList.add('proptablediv');
        this.#table = document.createElement('table');
        this.#table.classList.add('prop-table');
        this.div.append(this.#table);
    }

    /**
     * - It is possible to nest tables, so don't support multiple tBodies
     */
    insertTBodyRow({elements=null, colspans=null, position='append'}={}) {
        if (!(elements instanceof Array)) {
            throw TypeError('The "elements" argument must be instanceof Array.');
        }
        if (colspans !== null) {
            if (!(colspans instanceof Array)) {
                throw TypeError('The "colspans" argument must be null or instanceof Array.');
            }
            if (elements.length !== colspans.length) {
                throw Error('The "colspans" array must have the same length as the "elements" array.');
            }
        }
        if (!['append', 'beforeEnd', 'prepend'].includes(position)) {
            throw Error('The "position" argument must be "append", "beforeEnd", or "prepend".');
        }
        if (this.#table.tBodies.length === 0) {
            const tbody = document.createElement('tbody');
            tbody.classList.add('proptbody');
            this.#table.append(tbody);
        }
        const tr = document.createElement('tr');
        tr.classList.add('proptr');
        for (let i = 0; i < elements.length; i++) {
            const td = document.createElement('td');
            td.classList.add('proptd');
            if (colspans !== null) {
                td.colSpan = colspans[i];
            }
            const div = document.createElement('div');
            div.classList.add('propdiv');
            const e = elements[i];
            if (typeof e === 'string') {
                const span = document.createElement('span');
                span.classList.add('propspan');
                span.textContent = e;
                div.appendChild(span);
                td.appendChild(div)
            } else if (e instanceof Node) {
                div.appendChild(e);
                td.appendChild(div);
            } else if (e !== null) {
                throw TypeError('Each element in the "elements" argument must be typeof "string", instanceof Node, or null');
            }
            tr.append(td);
        }
        if (position === 'append') {
            this.#table.tBodies[0].append(tr);
        } else if (position === 'prepend') {
            this.#table.tBodies[0].prepend(tr);
        } else {
            const lastNodeIndex = this.#table.tBodies[0].children.length - 1;
            const lastNode = this.#table.tBodies[0].children.item(lastNodeIndex);
            this.#table.tBodies[0].insertBefore(tr, lastNode);
        }
    }

    insertTHeadRow({elements=null, colspans=null, position='append'}={}) {
        if (!(elements instanceof Array)) {
            throw TypeError('The "elements" argument must be instanceof Array.');
        }
        if (colspans !== null) {
            if (!(colspans instanceof Array)) {
                throw TypeError('The "colspans" argument must be null or instanceof Array.');
            }
            if (elements.length !== colspans.length) {
                throw Error('The "colspans" array must have the same length as the "elements" array.');
            }
        }
        if (!['append', 'beforeEnd', 'prepend'].includes(position)) {
            throw Error('The "position" argument must be "append", "beforeEnd", or "prepend".');
        }
        if (this.#table.tHead === null) {
            const thead = document.createElement('thead');
            thead.classList.add('propthead');
            this.#table.prepend(thead);
        }
        const tr = document.createElement('tr');
        tr.classList.add('proptr');
        for (let i = 0; i < elements.length; i++) {
            const th = document.createElement('th');
            th.classList.add('propth');
            if (colspans !== null) {
                th.colSpan = colspans[i];
            }
            const div = document.createElement('div');
            div.classList.add('propdiv');
            const e = elements[i];
            if (typeof e === 'string') {
                const span = document.createElement('span');
                span.classList.add('propspan');
                span.textContent = e;
                div.appendChild(span);
                th.appendChild(div)
            } else if (e instanceof Node) {
                div.appendChild(e);
                th.appendChild(div);
            } else if (e !== null) {
                throw TypeError('Each element in the "elements" argument must be typeof "string", instanceof Node, or null');
            }
            tr.append(th);
        }
        if (position === 'append') {
            this.#table.tHead.append(tr);
        } else if (position === 'prepend') {
            this.#table.tHead.prepend(tr);
        } else {
            const lastNodeIndex = this.#table.tHead.children.length - 1;
            const lastNode = this.#table.tHead.children.item(lastNodeIndex);
            this.#table.tHead.insertBefore(tr, lastNode);
        }
    }
}