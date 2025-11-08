document.addEventListener('DOMContentLoaded', function() {
    // Save Profile Button Handler
    const saveBtn = document.querySelector('.save-profile-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            const studentId = this.dataset.studentId;
            const button = this; // Store reference to button
            
            fetch(`/accounts/student/${studentId}/save/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin' // Include cookies
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Toggle button appearance
                    button.classList.toggle('btn-outline-pink');
                    button.classList.toggle('btn-pink');
                    button.innerHTML = data.saved ? 
                        '<i class="fas fa-bookmark me-2"></i>Saved' :
                        '<i class="fas fa-bookmark me-2"></i>Save Profile';
                    
                    // Optional: Show a success message
                    showToast(data.saved ? 'Profile saved!' : 'Profile unsaved');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error saving profile. Please try again.');
            });
        });
    }

    // Share Project Button Handler
    document.querySelectorAll('.share-project-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const projectUrl = this.dataset.projectUrl;
            const fullUrl = window.location.origin + projectUrl;
            
            navigator.clipboard.writeText(fullUrl).then(() => {
                showToast('Project URL copied to clipboard!');
            }).catch(err => {
                console.error('Failed to copy URL:', err);
                showToast('Failed to copy URL');
            });
        });
    });

    // Hire Form Handler
    window.submitHireForm = function() {
        const form = document.getElementById('hireForm');
        const jobTitle = form.querySelector('input[type="text"]').value;
        const message = form.querySelector('textarea').value;
        const studentId = document.querySelector('.save-profile-btn').dataset.studentId;

        if (!jobTitle || !message) {
            showToast('Please fill in all fields');
            return;
        }

        fetch(`/accounts/student/${studentId}/hire/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `job_title=${encodeURIComponent(jobTitle)}&message=${encodeURIComponent(message)}`
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showToast('Hiring request sent successfully!');
                document.getElementById('hireModal').querySelector('.btn-close').click();
                form.reset();
            } else {
                throw new Error(data.error || 'Failed to send hiring request');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error sending hiring request. Please try again.');
        });
    };
});

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Helper function to show toast messages
function showToast(message) {
    // Check if toast container exists, if not create it
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1050;
        `;
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast show';
    toast.style.cssText = `
        background: #333;
        color: white;
        padding: 15px 25px;
        border-radius: 5px;
        margin-bottom: 10px;
        opacity: 0;
        transition: opacity 0.3s ease-in;
    `;
    toast.textContent = message;

    // Add to container
    toastContainer.appendChild(toast);

    // Trigger reflow and add opacity
    setTimeout(() => {
        toast.style.opacity = '1';
    }, 10);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            toastContainer.removeChild(toast);
        }, 300);
    }, 3000);
}