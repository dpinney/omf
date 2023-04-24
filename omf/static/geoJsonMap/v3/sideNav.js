export { SideNav };
'use strict';

class SideNav {
    navElement; // Navigation pane. Contains divs
    divElement; // Cover pane for when the SideNav is opened in a narrow browser
    articleElement; // Content that shifts when the SideNav opens

    constructor() {
        this.navElement = document.createElement('nav');
        this.navElement.classList.add('js-nav--sideNav');
        this.divElement = document.createElement('div');
        this.divElement.classList.add('js-div--sideNavCover');
        this.articleElement = document.createElement('article');
        this.articleElement.classList.add('js-article--sideNavArticle');
    }
}