// سیستم تغییر تم برای Admin Panel
(function() {
    'use strict';
    
           const THEMES = {
        blue: {
            name: 'Blue Ocean',
            icon: '🌊',
            bodyBg: 'linear-gradient(135deg, #667eea 0%, #764ba2 25%, #4facfe 50%, #00f2fe 75%)',
            bodyOverlay: 'rgba(102, 126, 234, 0.15)',
            bodyColor: '#1a202c',
            cardBg: 'rgba(255, 255, 255, 0.92)',
            cardBorder: 'rgba(79, 172, 254, 0.25)',
            textPrimary: '#2d3748',
            textSecondary: '#4a5568',
            tableBg: 'rgba(255, 255, 255, 0.95)',
            tableHeaderBg: 'rgba(79, 172, 254, 0.2)',
            tableHeaderColor: '#2b6cb0',
            tableRowHover: 'rgba(79, 172, 254, 0.1)',
            inputBg: 'rgba(255, 255, 255, 0.95)',
            inputBorder: 'rgba(79, 172, 254, 0.3)',
            inputColor: '#2d3748',
            buttonBg: 'linear-gradient(135deg, #4facfe, #00f2fe)',
            headerBg: 'linear-gradient(135deg, #667eea 0%, #4facfe 100%)',
            headerColor: '#ffffff',
        },
        green: {
            name: 'Nature',
            icon: '🌿',
            bodyBg: 'linear-gradient(135deg, #11998e 0%, #38ef7d 50%, #4facfe 100%)',
            bodyOverlay: 'rgba(17, 153, 142, 0.15)',
            bodyColor: '#1a202c',
            cardBg: 'rgba(255, 255, 255, 0.92)',
            cardBorder: 'rgba(56, 239, 125, 0.25)',
            textPrimary: '#2d3748',
            textSecondary: '#4a5568',
            tableBg: 'rgba(255, 255, 255, 0.95)',
            tableHeaderBg: 'rgba(76, 175, 80, 0.2)',
            tableHeaderColor: '#2e7d32',
            tableRowHover: 'rgba(76, 175, 80, 0.1)',
            inputBg: 'rgba(255, 255, 255, 0.95)',
            inputBorder: 'rgba(56, 239, 125, 0.3)',
            inputColor: '#2d3748',
            buttonBg: 'linear-gradient(135deg, #11998e, #38ef7d)',
            headerBg: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
            headerColor: '#ffffff',
        },
        purple: {
            name: 'Purple Dream',
            icon: '💜',
            bodyBg: 'linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%)',
            bodyOverlay: 'rgba(118, 75, 162, 0.15)',
            bodyColor: '#2d3748',
            cardBg: 'rgba(255, 255, 255, 0.92)',
            cardBorder: 'rgba(118, 75, 162, 0.25)',
            textPrimary: '#2d3748',
            textSecondary: '#4a5568',
            tableBg: 'rgba(255, 255, 255, 0.95)',
            tableHeaderBg: 'rgba(118, 75, 162, 0.2)',
            tableHeaderColor: '#6b46c1',
            tableRowHover: 'rgba(118, 75, 162, 0.1)',
            inputBg: 'rgba(255, 255, 255, 0.95)',
            inputBorder: 'rgba(118, 75, 162, 0.3)',
            inputColor: '#2d3748',
            buttonBg: 'linear-gradient(135deg, #667eea, #764ba2)',
            headerBg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            headerColor: '#ffffff',
        },
        orange: {
            name: 'Sunset',
            icon: '🌅',
            bodyBg: 'linear-gradient(135deg, #f093fb 0%, #f5576c 25%, #4facfe 50%, #00f2fe 75%)',
            bodyOverlay: 'rgba(245, 87, 108, 0.15)',
            bodyColor: '#2d3748',
            cardBg: 'rgba(255, 255, 255, 0.92)',
            cardBorder: 'rgba(245, 87, 108, 0.25)',
            textPrimary: '#2d3748',
            textSecondary: '#4a5568',
            tableBg: 'rgba(255, 255, 255, 0.95)',
            tableHeaderBg: 'rgba(245, 87, 108, 0.2)',
            tableHeaderColor: '#c53030',
            tableRowHover: 'rgba(245, 87, 108, 0.1)',
            inputBg: 'rgba(255, 255, 255, 0.95)',
            inputBorder: 'rgba(245, 87, 108, 0.3)',
            inputColor: '#2d3748',
            buttonBg: 'linear-gradient(135deg, #f093fb, #f5576c)',
            headerBg: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            headerColor: '#ffffff',
        },
               rgb: {
                   name: 'RGB',
                   icon: '🌈',
                   // پس‌زمینه چندبخشی ولی بدون انیمیشن (ثابت)
                   bodyBg: 'linear-gradient(135deg, #ff5f6d 0%, #ffc371 25%, #4facfe 50%, #43e97b 75%, #fa709a 100%)',
                   bodyOverlay: 'rgba(0, 0, 0, 0.15)',
                   bodyColor: '#1b1f2a',
                   cardBg: 'rgba(255, 255, 255, 0.96)',
                   cardBorder: 'rgba(255, 255, 255, 0.35)',
                   textPrimary: '#1b1f2a',
                   textSecondary: '#2d3748',
                   tableBg: 'rgba(255, 255, 255, 0.98)',
                   tableHeaderBg: 'linear-gradient(135deg, #ff8c37 0%, #ff3d77 100%)',
                   tableHeaderColor: '#ffffff',
                   tableRowHover: 'rgba(255, 99, 132, 0.12)',
                   inputBg: 'rgba(255, 255, 255, 0.96)',
                   inputBorder: 'rgba(255, 99, 132, 0.35)',
                   inputColor: '#1b1f2a',
                   buttonBg: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 50%, #4facfe 100%)',
                   headerBg: 'linear-gradient(135deg, #7f5af0 0%, #2cb8ff 50%, #00f2a9 100%)',
                   headerColor: '#ffffff',
               }
    };
    
    // بارگذاری تم ذخیره شده
    function loadTheme() {
        const savedTheme = localStorage.getItem('admin_theme') || 'blue';
        applyTheme(savedTheme);
        return savedTheme;
    }
    
    // اعمال تم - به صورت global
           window.applyTheme = function(themeName) {
        const theme = THEMES[themeName];
        if (!theme) {
            console.warn('Theme not found:', themeName);
            return;
        }
        
        const root = document.documentElement;
        const body = document.body;
        
        // تنظیم متغیرهای CSS
        root.style.setProperty('--admin-body-bg', theme.bodyBg);
        root.style.setProperty('--admin-body-overlay', theme.bodyOverlay);
        root.style.setProperty('--admin-body-color', theme.bodyColor);
        root.style.setProperty('--admin-card-bg', theme.cardBg);
        root.style.setProperty('--admin-card-border', theme.cardBorder);
        root.style.setProperty('--admin-text-primary', theme.textPrimary);
        root.style.setProperty('--admin-text-secondary', theme.textSecondary);
        root.style.setProperty('--admin-table-bg', theme.tableBg);
        root.style.setProperty('--admin-table-header-bg', theme.tableHeaderBg);
        root.style.setProperty('--admin-table-header-color', theme.tableHeaderColor);
        root.style.setProperty('--admin-table-row-hover', theme.tableRowHover);
        root.style.setProperty('--admin-input-bg', theme.inputBg);
        root.style.setProperty('--admin-input-border', theme.inputBorder);
        root.style.setProperty('--admin-input-color', theme.inputColor);
        root.style.setProperty('--admin-button-bg', theme.buttonBg);
        root.style.setProperty('--admin-header-bg', theme.headerBg);
        root.style.setProperty('--admin-header-color', theme.headerColor);
        
               // اضافه کردن کلاس به body
               body.classList.remove('theme-blue', 'theme-green', 'theme-purple', 'theme-orange', 'theme-rgb');
               body.classList.add(`theme-${themeName}`);

               // برای RGB انیمیشن حذف شد تا ثابت باشد
               body.style.removeProperty('animation');
               body.style.removeProperty('background-size');
        
        // ذخیره تم
        localStorage.setItem('admin_theme', themeName);
        
        // به‌روزرسانی دکمه تم
        updateThemeButton(themeName);
        
        // علامت‌گذاری تم فعال در منو
        document.querySelectorAll('.theme-option').forEach(option => {
            option.classList.remove('active');
            if (option.dataset.theme === themeName) {
                option.classList.add('active');
            }

           // انیمیشن RGB حذف شد تا رنگ‌ها ثابت باشند
        });
        
        console.log('Theme applied:', themeName);
    };
    
    // نگه داشتن تابع اصلی هم
    function applyTheme(themeName) {
        window.applyTheme(themeName);
    }
    
    // به‌روزرسانی دکمه تم
    function updateThemeButton(themeName) {
        const btn = document.querySelector('.theme-switcher-btn') || document.querySelector('#theme-switcher-button');
        if (!btn) return;
        
        const theme = THEMES[themeName];
        if (theme) {
            const iconElement = btn.querySelector('i');
            const textElement = btn.querySelector('.theme-switcher-text');
            if (iconElement && textElement) {
                // فقط آیکون را تغییر می‌دهیم، متن را نگه می‌داریم
                textElement.textContent = theme.icon;
            }
        }
    }
    
    // متصل کردن event listeners به دکمه
    function attachEventListeners(switcher) {
        if (!switcher) return;
        
        const btn = switcher.querySelector('.theme-switcher-btn') || switcher.querySelector('#theme-switcher-button');
        const menu = switcher.querySelector('.theme-switcher-menu') || switcher.querySelector('#theme-switcher-menu');
        
        if (!btn || !menu) {
            console.warn('Theme switcher elements not found', {btn: !!btn, menu: !!menu});
            return;
        }
        
        // رویداد کلیک روی دکمه - استفاده از onclick برای جلوگیری از duplicate
        btn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            menu.classList.toggle('show');
            console.log('Theme menu toggled');
        };
        
        // رویداد کلیک روی گزینه‌ها
        menu.querySelectorAll('.theme-option').forEach(option => {
            option.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                const theme = this.dataset.theme;
                if (theme) {
                    console.log('Applying theme:', theme);
                    window.applyTheme(theme);
                    menu.classList.remove('show');
                    
                    // علامت‌گذاری تم فعال
                    menu.querySelectorAll('.theme-option').forEach(opt => {
                        opt.classList.remove('active');
                    });
                    this.classList.add('active');
                }
            };
        });
        
        // بستن منو با کلیک خارج
        const closeHandler = function(e) {
            if (switcher && !switcher.contains(e.target)) {
                menu.classList.remove('show');
            }
        };
        
        // حذف listener قبلی و اضافه کردن جدید
        document.removeEventListener('click', closeHandler);
        document.addEventListener('click', closeHandler);
        
        // علامت‌گذاری تم فعال
        const currentTheme = localStorage.getItem('admin_theme') || 'blue';
        menu.querySelectorAll('.theme-option').forEach(option => {
            option.classList.remove('active');
            if (option.dataset.theme === currentTheme) {
                option.classList.add('active');
            }
        });
        
        console.log('✅ Theme switcher event listeners attached');
    }
    
    // ساخت دکمه تغییر تم - فقط اگر وجود نداشته باشد
    function createThemeSwitcher() {
        // بررسی اینکه آیا دکمه از قبل در HTML وجود دارد
        let switcher = document.querySelector('.theme-switcher') || document.querySelector('#admin-theme-switcher');
        
        if (!switcher) {
            // اگر در HTML وجود ندارد، از JavaScript ایجاد می‌کنیم
            const header = document.querySelector('.admin-mini-header .admin-header-right');
            if (!header) {
                console.warn('Admin header not found, retrying...');
                setTimeout(createThemeSwitcher, 200);
                return;
            }
            
            switcher = document.createElement('div');
            switcher.className = 'theme-switcher';
            switcher.id = 'admin-theme-switcher';
            switcher.innerHTML = `
                <button type="button" class="theme-switcher-btn" title="تغییر تم" id="theme-switcher-button">
                    <i class="fas fa-palette"></i>
                    <span class="theme-switcher-text">تم</span>
                </button>
                <div class="theme-switcher-menu" id="theme-switcher-menu">
                    <button type="button" class="theme-option" data-theme="blue">
                        <span class="theme-icon">🌊</span>
                        <span>Blue Ocean</span>
                    </button>
                    <button type="button" class="theme-option" data-theme="green">
                        <span class="theme-icon">🌿</span>
                        <span>Nature</span>
                    </button>
                    <button type="button" class="theme-option" data-theme="purple">
                        <span class="theme-icon">💜</span>
                        <span>Purple Dream</span>
                    </button>
                    <button type="button" class="theme-option" data-theme="orange">
                        <span class="theme-icon">🌅</span>
                        <span>Sunset</span>
                    </button>
                    <button type="button" class="theme-option" data-theme="rgb">
                        <span class="theme-icon">🌈</span>
                        <span>RGB</span>
                    </button>
                </div>
            `;
            
            header.insertBefore(switcher, header.firstChild);
            console.log('Theme switcher created dynamically');
        }
        
        // متصل کردن event listeners
        attachEventListeners(switcher);
    }
    
    // اجرا بعد از لود صفحه - چند بار تلاش برای اطمینان
    function initThemeSwitcher() {
        loadTheme();
        createThemeSwitcher();
    }
    
    // اجرای اولیه - چند بار تلاش برای اطمینان
    function startThemeSwitcher() {
        try {
            initThemeSwitcher();
        } catch (e) {
            console.error('Error initializing theme switcher:', e);
        }
    }
    
    // اجرای اولیه
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(startThemeSwitcher, 100);
        });
    } else {
        setTimeout(startThemeSwitcher, 100);
    }
    
    // تلاش مجدد بعد از لود کامل
    window.addEventListener('load', function() {
        setTimeout(startThemeSwitcher, 300);
    });
    
    // تلاش مجدد بعد از 1 ثانیه
    setTimeout(startThemeSwitcher, 1000);
    
    console.log('Theme switcher script loaded');
})();

