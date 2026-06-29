// Theme configuration
const config = {
    // Mobile navigation breakpoint
    mobileBreakpoint: 768,
    // Reading progress bar color
    progressBarColor: '#2563eb',
    // Back to top button threshold
    backToTopThreshold: 300
};

// Mobile Navigation
class MobileNav {
    constructor() {
        this.nav = document.querySelector('.site-nav');
        this.toggle = document.createElement('button');
        this.toggle.className = 'mobile-nav-toggle';
        this.toggle.innerHTML = '<span></span><span></span><span></span>';
        this.toggle.setAttribute('aria-label', 'Toggle navigation');
        
        this.init();
    }

    init() {
        if (window.innerWidth <= config.mobileBreakpoint) {
            this.setupMobileNav();
        }
        
        window.addEventListener('resize', () => {
            if (window.innerWidth <= config.mobileBreakpoint) {
                this.setupMobileNav();
            } else {
                this.removeMobileNav();
            }
        });
    }

    setupMobileNav() {
        if (!this.nav.parentElement.querySelector('.mobile-nav-toggle')) {
            this.nav.parentElement.insertBefore(this.toggle, this.nav);
            this.toggle.addEventListener('click', () => this.toggleNav());
        }
    }

    removeMobileNav() {
        const toggle = this.nav.parentElement.querySelector('.mobile-nav-toggle');
        if (toggle) {
            toggle.remove();
            this.nav.classList.remove('active');
        }
    }

    toggleNav() {
        this.nav.classList.toggle('active');
        this.toggle.classList.toggle('active');
    }
}

// Reading Progress
class ReadingProgress {
    constructor() {
        this.progressBar = document.createElement('div');
        this.progressBar.className = 'reading-progress';
        this.init();
    }

    init() {
        document.body.insertBefore(this.progressBar, document.body.firstChild);
        window.addEventListener('scroll', () => this.updateProgress());
        window.addEventListener('resize', () => this.updateProgress());
    }

    updateProgress() {
        const winHeight = window.innerHeight;
        const docHeight = document.documentElement.scrollHeight - winHeight;
        const scrollTop = window.scrollY;
        const progress = (scrollTop / docHeight) * 100;
        this.progressBar.style.width = `${progress}%`;
    }
}

// Code Block Enhancements
class CodeBlocks {
    constructor() {
        this.init();
    }

    init() {
        document.querySelectorAll('pre code').forEach(block => {
            // Add copy button
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-button';
            copyButton.textContent = 'Copy';
            copyButton.addEventListener('click', () => this.copyCode(block, copyButton));
            
            const pre = block.parentElement;
            pre.style.position = 'relative';
            pre.appendChild(copyButton);
        });
    }

    async copyCode(block, button) {
        try {
            await navigator.clipboard.writeText(block.textContent);
            button.textContent = 'Copied!';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        } catch (err) {
            console.error('Failed to copy code:', err);
        }
    }
}

// Image Handling
class ImageHandler {
    constructor() {
        this.init();
    }

    init() {
        // Lazy loading
        if ('loading' in HTMLImageElement.prototype) {
            document.querySelectorAll('img[loading="lazy"]').forEach(img => {
                img.src = img.dataset.src;
            });
        } else {
            // Fallback for browsers that don't support lazy loading
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';
            document.body.appendChild(script);
        }

        // Lightbox
        document.querySelectorAll('img').forEach(img => {
            if (img.parentElement.tagName !== 'A') {
                img.addEventListener('click', () => this.openLightbox(img));
            }
        });
    }

    openLightbox(img) {
        const lightbox = document.createElement('div');
        lightbox.className = 'lightbox';
        lightbox.innerHTML = `
            <div class="lightbox-content">
                <img src="${img.src}" alt="${img.alt}">
                <button class="lightbox-close">&times;</button>
            </div>
        `;
        
        document.body.appendChild(lightbox);
        document.body.style.overflow = 'hidden';
        
        lightbox.addEventListener('click', (e) => {
            if (e.target === lightbox || e.target.className === 'lightbox-close') {
                lightbox.remove();
                document.body.style.overflow = '';
            }
        });
    }
}

// Back to Top Button
class BackToTop {
    constructor() {
        this.button = document.createElement('button');
        this.button.className = 'back-to-top';
        this.button.innerHTML = '↑';
        this.button.setAttribute('aria-label', 'Back to top');
        this.init();
    }

    init() {
        document.body.appendChild(this.button);
        window.addEventListener('scroll', () => this.toggleButton());
        this.button.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    toggleButton() {
        if (window.scrollY > config.backToTopThreshold) {
            this.button.classList.add('visible');
        } else {
            this.button.classList.remove('visible');
        }
    }
}

// Theme Toggle
class ThemeToggle {
    constructor() {
        this.init();
    }

    init() {
        const toggle = document.createElement('button');
        toggle.className = 'theme-toggle';
        toggle.innerHTML = '🌙';
        toggle.setAttribute('aria-label', 'Toggle theme');

        document.querySelector('.site-header .container').appendChild(toggle);

        // Check for saved theme preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
            toggle.innerHTML = savedTheme === 'dark' ? '☀️' : '🌙';
        }

        toggle.addEventListener('click', () => this.toggleTheme(toggle));
    }

    toggleTheme(button) {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        button.innerHTML = newTheme === 'dark' ? '☀️' : '🌙';
    }
}

// Share Buttons
class ShareButtons {
    constructor() {
        this.init();
    }

    init() {
        const copyButton = document.querySelector('.share-copy');
        if (!copyButton) return;

        copyButton.addEventListener('click', async () => {
            const url = copyButton.dataset.url;
            const copyText = copyButton.querySelector('.copy-text');
            const originalText = copyText.textContent;

            try {
                await navigator.clipboard.writeText(url);
                copyButton.classList.add('copied');
                copyText.textContent = 'Copied!';

                setTimeout(() => {
                    copyButton.classList.remove('copied');
                    copyText.textContent = originalText;
                }, 2000);
            } catch (err) {
                console.error('Failed to copy link:', err);
                copyText.textContent = 'Failed to copy';

                setTimeout(() => {
                    copyText.textContent = originalText;
                }, 2000);
            }
        });
    }
}

// Initialize all features
document.addEventListener('DOMContentLoaded', () => {
    new MobileNav();
    new ReadingProgress();
    new CodeBlocks();
    new ImageHandler();
    new BackToTop();
    new ThemeToggle();
    new ShareButtons();
}); 