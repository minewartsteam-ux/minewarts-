// اسکریپت برای حذف کامل navbar از پنل ادمین و اضافه کردن header کوچک
(function() {
    'use strict';
    
    // اضافه کردن header کوچک
    function addMiniHeader() {
        if (document.querySelector('.admin-mini-header')) {
            return; // اگر قبلاً اضافه شده، نیازی نیست دوباره اضافه کنیم
        }
        
        const headerHTML = `
            <div class="admin-mini-header" style="
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                border-bottom: 2px solid #4CAF50;
                padding: 8px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 1000;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
                height: 50px;
                min-height: 50px;
                max-height: 50px;
            ">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <a href="/admin/" style="
                        color: #4CAF50;
                        font-size: 1.1rem;
                        font-weight: bold;
                        text-decoration: none;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    ">
                        <i class="fas fa-store" style="font-size: 1.2rem;"></i>
                        <span>پنل مدیریت</span>
                    </a>
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <a href="/admin/dashboard/" style="
                        color: #E0E0E0;
                        text-decoration: none;
                        font-size: 0.9rem;
                        padding: 5px 12px;
                        border-radius: 5px;
                        transition: all 0.3s;
                    " onmouseover="this.style.background='rgba(76, 175, 80, 0.2)'" onmouseout="this.style.background='transparent'">
                        <i class="fas fa-tachometer-alt"></i> داشبورد
                    </a>
                    <a href="/accounts/support-panel/" style="
                        color: #03A9F4;
                        text-decoration: none;
                        font-size: 0.9rem;
                        padding: 5px 12px;
                        border-radius: 5px;
                        transition: all 0.3s;
                    " onmouseover="this.style.background='rgba(3, 169, 244, 0.2)'" onmouseout="this.style.background='transparent'">
                        <i class="fas fa-headset"></i> پنل پشتیبانی
                    </a>
                    <a href="/" style="
                        color: #E0E0E0;
                        text-decoration: none;
                        font-size: 0.9rem;
                        padding: 5px 12px;
                        border-radius: 5px;
                        transition: all 0.3s;
                    " onmouseover="this.style.background='rgba(76, 175, 80, 0.2)'" onmouseout="this.style.background='transparent'">
                        <i class="fas fa-home"></i> سایت
                    </a>
                    <span style="color: #9E9E9E; font-size: 0.85rem;">
                        <i class="fas fa-user"></i> ${document.querySelector('.user-info')?.textContent || document.querySelector('a[href*="user"]')?.textContent || 'کاربر'}
                    </span>
                </div>
            </div>
        `;
        
        const body = document.body;
        body.insertAdjacentHTML('afterbegin', headerHTML);
    }
    
    function hideNavbar() {
        // حذف همه عناصر navbar - شامل navbar مدیریت Django
        const selectors = [
            '#jazzy-navbar',
            '.main-header',
            '.navbar',
            'header:not(.content-header)',
            'nav.navbar',
            '[class*="navbar"]',
            '[id*="navbar"]',
            '.navbar-custom',
            'header[role="banner"]',
            'nav[role="navigation"]',
            '.navbar-dark',
            '.navbar-expand',
            '.navbar-expand-lg',
            '.navbar-expand-md',
            '.navbar-expand-sm',
            '.navbar-expand-xl',
            '.navbar-collapse',
            '.navbar-brand',
            '.navbar-nav',
            '.navbar-toggler',
            '.main-header',
            'header.main-header',
            '.content-header:first-child',
            '.navbar-wrapper',
            '.header-wrapper',
            '.admin-header',
            '.admin-navbar',
            'body > header',
            'body > nav:not(.sidebar):not(.main-sidebar)',
            '.wrapper > header',
            '.wrapper > nav:not(.sidebar):not(.main-sidebar)'
        ];
        
        selectors.forEach(selector => {
            try {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    if (el && el.parentNode) {
                        el.style.display = 'none';
                        el.style.visibility = 'hidden';
                        el.style.height = '0';
                        el.style.padding = '0';
                        el.style.margin = '0';
                        el.style.overflow = 'hidden';
                        el.style.opacity = '0';
                        el.style.position = 'absolute';
                        el.style.width = '0';
                        el.style.zIndex = '-9999';
                        // حذف کامل از DOM
                        if (el.parentNode) {
                            el.parentNode.removeChild(el);
                        }
                    }
                });
            } catch(e) {
                // ignore errors
            }
        });
        
        // تنظیم فضای خالی برای header کوچک
        const contentWrapper = document.querySelector('.content-wrapper');
        if (contentWrapper) {
            contentWrapper.style.paddingTop = '50px';
            contentWrapper.style.marginTop = '0';
        }
        
        const wrapper = document.querySelector('.wrapper');
        if (wrapper) {
            wrapper.style.paddingTop = '0';
            wrapper.style.marginTop = '0';
        }
        
        // حذف کامل sidebar
        const sidebarSelectors = [
            '.main-sidebar',
            '.sidebar',
            'aside.main-sidebar',
            'aside.sidebar',
            'nav.main-sidebar',
            'nav.sidebar',
            '[class*="sidebar"]',
            '[id*="sidebar"]'
        ];
        
        sidebarSelectors.forEach(selector => {
            try {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    if (el && el.parentNode) {
                        el.style.display = 'none';
                        el.style.visibility = 'hidden';
                        el.style.width = '0';
                        el.style.height = '0';
                        el.style.padding = '0';
                        el.style.margin = '0';
                        el.style.overflow = 'hidden';
                        el.style.opacity = '0';
                        el.style.position = 'absolute';
                        el.style.zIndex = '-9999';
                        if (el.parentNode) {
                            el.parentNode.removeChild(el);
                        }
                    }
                });
            } catch(e) {
                // ignore errors
            }
        });
        
        // تنظیم content-wrapper برای حذف margin sidebar
        const contentWrapper = document.querySelector('.content-wrapper');
        if (contentWrapper) {
            contentWrapper.style.marginRight = '0';
            contentWrapper.style.marginLeft = '0';
            contentWrapper.style.width = '100%';
        }
    }
    
    // اجرا بلافاصله
    hideNavbar();
    addMiniHeader();
    
    // اجرا بعد از لود کامل صفحه
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            hideNavbar();
            addMiniHeader();
        });
    } else {
        hideNavbar();
        addMiniHeader();
    }
    
    // اجرا بعد از لود کامل
    window.addEventListener('load', function() {
        hideNavbar();
        addMiniHeader();
    });
    
    // استفاده از MutationObserver برای حذف عناصر جدید
    const observer = new MutationObserver(function(mutations) {
        hideNavbar();
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();


