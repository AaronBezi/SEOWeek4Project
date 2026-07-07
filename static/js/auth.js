function navigateTo(viewId) {
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById(viewId + '-view').classList.add('active');
    document.getElementById('myDropdown').classList.remove('show');
}

function toggleDropdown() {
    document.getElementById('myDropdown').classList.toggle('show');
}

window.onclick = function (event) {
    if (!event.target.matches('.menu-trigger') && !event.target.matches('.three-dots')) {
        document.querySelectorAll('.dropdown-content').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
};
