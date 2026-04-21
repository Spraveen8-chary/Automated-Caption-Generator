(function () {
    const storageKey = 'caption-generator-theme';

    function getStoredTheme() {
        try {
            const value = localStorage.getItem(storageKey);
            if (value === 'dark' || value === 'light') {
                return value;
            }
        } catch (error) {
            return 'dark';
        }
        return 'dark';
    }

    function setTheme(theme) {
        const nextTheme = theme === 'light' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', nextTheme);
        document.documentElement.style.colorScheme = nextTheme;

        try {
            localStorage.setItem(storageKey, nextTheme);
        } catch (error) {
            // Ignore storage failures and keep the theme applied for this session.
        }

        document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
            button.dataset.theme = nextTheme;
            button.textContent = nextTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
            button.setAttribute(
                'aria-label',
                nextTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
            );
        });
    }

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || getStoredTheme();
        setTheme(currentTheme === 'dark' ? 'light' : 'dark');
    }

    document.addEventListener('DOMContentLoaded', () => {
        setTheme(getStoredTheme());

        document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
            button.addEventListener('click', toggleTheme);
        });
    });

    window.ThemeController = {
        getTheme: getStoredTheme,
        setTheme,
        toggleTheme,
    };
})();
