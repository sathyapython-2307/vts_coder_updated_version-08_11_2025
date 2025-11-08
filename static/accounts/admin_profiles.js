document.addEventListener('DOMContentLoaded', function() {
    // Handle profile card clicks
    document.querySelectorAll('.profile-card').forEach(card => {
        card.addEventListener('click', function() {
            const studentId = this.dataset.studentId;
            window.location.href = `/accounts/student/${studentId}/projects/`;
        });
    });

    // Sidebar toggle logic
    const sidebar = document.getElementById('adminSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const openBtn = document.getElementById('openSidebarBtn');
    const closeBtn = document.getElementById('closeSidebarBtn');

    function openSidebar() {
        sidebar.style.transform = 'translateX(0)';
        overlay.style.display = 'block';
    }

    function closeSidebar() {
        sidebar.style.transform = 'translateX(-110vw)';
        overlay.style.display = 'none';
    }

    if (openBtn && closeBtn && overlay) {
        openBtn.onclick = openSidebar;
        closeBtn.onclick = closeSidebar;
        overlay.onclick = closeSidebar;
    }

    // Hide sidebar by default on mobile
    if (window.innerWidth < 992) {
        closeSidebar();
    }

    window.addEventListener('resize', function() {
        if (window.innerWidth < 992) {
            closeSidebar();
        } else {
            sidebar.style.transform = 'translateX(0)';
            overlay.style.display = 'none';
        }
    });
});