(function() {
    const publicPages = ['/', '/register/'];

    if (!publicPages.includes(window.location.pathname)) {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/';
        }
    }
})();