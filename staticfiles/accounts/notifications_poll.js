(function(){
    const POLL_INTERVAL = 3000; // 3 seconds - short polling for near-instant updates
    const endpoint = '/accounts/notifications/unread-json/';

    function xhrGetJson(url){
        return fetch(url, {
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).then(r => r.json());
    }

    function updateBadge(count){
        const btn = document.querySelector('.notification-btn');
        if(!btn) return;
        let badge = btn.querySelector('.notification-badge');
        if(count > 0){
            if(!badge){
                badge = document.createElement('span');
                badge.className = 'notification-badge';
                btn.appendChild(badge);
            }
            badge.textContent = count;
        } else {
            if(badge) badge.remove();
        }
    }

    function formatTimeAgo(iso){
        try{
            const then = new Date(iso);
            const diff = Math.floor((Date.now() - then.getTime())/1000);
            if(diff < 60) return `${diff}s`;
            if(diff < 3600) return `${Math.floor(diff/60)}m`;
            if(diff < 86400) return `${Math.floor(diff/3600)}h`;
            return `${Math.floor(diff/86400)}d`;
        }catch(e){return ''}
    }

    function renderNotificationItem(n){
        // Use same structure as notifications.html to avoid style changes
        const div = document.createElement('div');
        div.className = 'list-group-item';
        if(!n.is_read) div.classList.add('list-group-item-light');

        let inner = '';
        if(n.type === 'like'){
            inner = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong>${n.sender}</strong> liked your project 
                    <a href="/accounts/project/${n.project.id}/details/">${n.project.title}</a>
                </div>
                <small class="text-muted">${formatTimeAgo(n.created_at)} ago</small>
            </div>`;
        } else if(n.type === 'hire'){
            const title = n.hiring ? n.hiring.job_title : (n.data && n.data.job_title ? n.data.job_title : 'Job');
            const message = n.hiring ? n.hiring.message : (n.data && n.data.message ? n.data.message : '');
            inner = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong>${n.sender}</strong> wants to hire you
                    <div><small class="text-muted">${title}</small></div>
                    <div>${message}</div>
                </div>
                <small class="text-muted">${formatTimeAgo(n.created_at)} ago</small>
            </div>`;
        } else {
            inner = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong>${n.sender}</strong>
                </div>
                <small class="text-muted">${formatTimeAgo(n.created_at)} ago</small>
            </div>`;
        }
        div.innerHTML = inner;
        return div;
    }

    let lastSeenIds = new Set();

    function poll(){
        xhrGetJson(endpoint).then(data => {
            if(!data || !data.success) return;
            updateBadge(data.unread_count);

            const listGroup = document.querySelector('.list-group');
            if(listGroup && Array.isArray(data.notifications) && data.notifications.length){
                // prepend any notification ids we haven't seen yet
                data.notifications.reverse().forEach(n => {
                    if(!lastSeenIds.has(n.id)){
                        const node = renderNotificationItem(n);
                        listGroup.insertBefore(node, listGroup.firstChild);
                        lastSeenIds.add(n.id);
                    }
                });
            }
        }).catch(err => {
            console.error('Notifications poll error', err);
        }).finally(() => {
            setTimeout(poll, POLL_INTERVAL);
        });
    }

    // Start polling after DOM ready
    if(document.readyState === 'loading'){
        document.addEventListener('DOMContentLoaded', poll);
    } else {
        poll();
    }
})();
