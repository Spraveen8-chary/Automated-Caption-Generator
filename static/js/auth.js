// Authentication form handling

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    // Login Form
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const btn = document.getElementById('loginBtn');
            const btnText = btn.querySelector('.btn-text');
            const btnLoader = btn.querySelector('.btn-loader');
            
            // Show loader
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline-flex';
            btn.disabled = true;
            
            const formData = new FormData(loginForm);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch(loginForm.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    // Success - redirect
                    showSuccess('Login successful! Redirecting...');
                    setTimeout(() => {
                        if (result.is_admin) {
                            window.location.href = '/admin';
                        } else {
                            window.location.href = '/';
                        }
                    }, 1000);
                } else {
                    // Error
                    showError(result.error || 'Login failed');
                    btnText.style.display = 'inline';
                    btnLoader.style.display = 'none';
                    btn.disabled = false;
                }
            } catch (error) {
                showError('Network error. Please try again.');
                btnText.style.display = 'inline';
                btnLoader.style.display = 'none';
                btn.disabled = false;
            }
        });
    }

    // Register Form
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            // Validate passwords match
            if (password !== confirmPassword) {
                showError('Passwords do not match');
                return;
            }
            
            const btn = document.getElementById('registerBtn');
            const btnText = btn.querySelector('.btn-text');
            const btnLoader = btn.querySelector('.btn-loader');
            
            // Show loader
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline-flex';
            btn.disabled = true;
            
            const formData = new FormData(registerForm);
            const data = Object.fromEntries(formData);
            delete data.confirm_password; // Remove confirm password
            
            try {
                const response = await fetch(registerForm.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    // Success - redirect
                    showSuccess('Account created! Redirecting...');
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1000);
                } else {
                    // Error
                    showError(result.error || 'Registration failed');
                    btnText.style.display = 'inline';
                    btnLoader.style.display = 'none';
                    btn.disabled = false;
                }
            } catch (error) {
                showError('Network error. Please try again.');
                btnText.style.display = 'inline';
                btnLoader.style.display = 'none';
                btn.disabled = false;
            }
        });
    }
});

function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert--error';
    alert.textContent = message;
    
    const form = document.querySelector('form');
    form.insertAdjacentElement('beforebegin', alert);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert--success';
    alert.textContent = message;
    
    const form = document.querySelector('form');
    form.insertAdjacentElement('beforebegin', alert);
}
