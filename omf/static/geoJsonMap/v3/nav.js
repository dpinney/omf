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
        const hamburger = this.topNavNavElement.getElementsByTagName('button')[0];
        const that = this
        hamburger.addEventListener('click', function () {
            that.sideNavNavElement.classList.toggle('open');
            that.sideNavDivElement.classList.toggle('open');
            if (that.sideNavNavElement.classList.contains('open') && !that.sideNavArticleElement.classList.contains('compressed')) {
                that.sideNavArticleElement.classList.add('compressed');
            } else {
                that.sideNavArticleElement.classList.remove('compressed');
            }
        });
        that.sideNavDivElement.addEventListener('click', function() {
            that.sideNavNavElement.classList.remove('open');
            that.sideNavDivElement.classList.remove('open');
            that.sideNavArticleElement.classList.remove('compressed');
        });
    }
}