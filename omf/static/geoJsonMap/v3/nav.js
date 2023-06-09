export { Nav };
import { SideNav } from './sideNav.js';
import { TopNav } from './topNav.js';

class Nav {
    sideNav;
    sideNavNavElement;
    sideNavDivElement;
    sideNavArticleElement;
    topNav;
    topNavNavElement;

    /**
     * - Connect a SideNav and TopNav together
     */
    constructor() {
        this.sideNav = new SideNav();
        this.sideNavNavElement = this.sideNav.navElement;
        this.sideNavDivElement = this.sideNav.divElement;
        this.sideNavArticleElement = this.sideNav.articleElement;
        this.topNav = new TopNav();
        this.topNavNavElement = this.topNav.navElement;
        //const hamburger = this.topNavNavElement.getElementsByTagName('button')[0];
        //hamburger.addEventListener('click', function () {
        //});
        const that = this
        this.sideNavDivElement.addEventListener('click', function() {
            that.sideNavNavElement.classList.remove('open');
            that.sideNavDivElement.classList.remove('open');
            that.sideNavArticleElement.classList.remove('compressed');
        });
    }
}