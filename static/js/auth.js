/**
 * CleanTrack AI - Authentication (Login & Register) Script
 */

document.addEventListener('DOMContentLoaded', () => {
  const loginTab = document.getElementById('loginTab');
  const registerTab = document.getElementById('registerTab');
  const loginFormSection = document.getElementById('loginFormSection');
  const registerFormSection = document.getElementById('registerFormSection');
  const authTitle = document.getElementById('authTitle');

  // Check URL parameters for tab switch (e.g. /login?tab=register)
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('tab') === 'register') {
    switchTab('register');
  }

  function switchTab(tab) {
    if (tab === 'register') {
      loginTab.classList.remove('active');
      registerTab.classList.add('active');
      loginFormSection.style.display = 'none';
      registerFormSection.style.display = 'block';
      authTitle.textContent = 'Create CleanTrack AI Account';
    } else {
      registerTab.classList.remove('active');
      loginTab.classList.add('active');
      registerFormSection.style.display = 'none';
      loginFormSection.style.display = 'block';
      authTitle.textContent = 'Welcome Back to CleanTrack AI';
    }
  }

  if (loginTab && registerTab) {
    loginTab.addEventListener('click', () => switchTab('login'));
    registerTab.addEventListener('click', () => switchTab('register'));
  }

  // Switch links inside forms
  const toRegisterLink = document.getElementById('toRegisterLink');
  const toLoginLink = document.getElementById('toLoginLink');
  if (toRegisterLink) toRegisterLink.addEventListener('click', (e) => { e.preventDefault(); switchTab('register'); });
  if (toLoginLink) toLoginLink.addEventListener('click', (e) => { e.preventDefault(); switchTab('login'); });

  // Password Visibility Toggles
  document.querySelectorAll('.toggle-pw').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (input) {
        if (input.type === 'password') {
          input.type = 'text';
          btn.classList.replace('fa-eye', 'fa-eye-slash');
        } else {
          input.type = 'password';
          btn.classList.replace('fa-eye-slash', 'fa-eye');
        }
      }
    });
  });

  // Role Radio Card highlighting in Registration
  document.querySelectorAll('input[name="regRole"]').forEach(radio => {
    radio.addEventListener('change', () => {
      document.querySelectorAll('.role-radio-card').forEach(card => card.classList.remove('selected'));
      radio.closest('.role-radio-card').classList.add('selected');
    });
  });

  // Demo Credentials Fillers
  window.fillDemo = function(role) {
    switchTab('login');
    const emailInput = document.getElementById('loginEmail');
    const pwInput = document.getElementById('loginPassword');
    if (role === 'citizen') {
      emailInput.value = 'citizen@cleantrack.ai';
      pwInput.value = 'Citizen123!';
      showToast('Citizen demo credentials loaded.', 'info', 2500);
    } else if (role === 'admin') {
      emailInput.value = 'admin@cleantrack.ai';
      pwInput.value = 'Admin123!';
      showToast('Administrator demo credentials loaded.', 'info', 2500);
    }
  };

  // Login Form Submission
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('loginEmail').value.trim();
      const password = document.getElementById('loginPassword').value;
      const remember = document.getElementById('rememberMe').checked;
      const submitBtn = document.getElementById('loginSubmitBtn');

      if (!email || !password) {
        showToast('Please enter your email and password.', 'error');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Signing in...';

      try {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, remember })
        });

        const data = await response.json();

        if (response.ok && data.success) {
          showToast(data.message, 'success');
          setTimeout(() => {
            window.location.href = data.redirect;
          }, 800);
        } else {
          showToast(data.error || 'Login failed. Please check credentials.', 'error');
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i class="fa-solid fa-right-to-bracket"></i> Sign In';
        }
      } catch (err) {
        showToast('Network error during login. Please try again.', 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-right-to-bracket"></i> Sign In';
      }
    });
  }

  // Registration Form Submission
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fullName = document.getElementById('regName').value.trim();
      const email = document.getElementById('regEmail').value.trim().toLowerCase();
      const phone = document.getElementById('regPhone').value.trim();
      const password = document.getElementById('regPassword').value;
      const confirmPassword = document.getElementById('regConfirmPassword').value;
      const roleElem = document.querySelector('input[name="regRole"]:checked');
      const role = roleElem ? roleElem.value : 'citizen';
      const submitBtn = document.getElementById('registerSubmitBtn');

      // Validations
      if (!fullName) {
        showToast('Please enter your full name.', 'error');
        return;
      }
      if (!email || !email.includes('@') || !email.includes('.')) {
        showToast('Please enter a valid email address.', 'error');
        return;
      }
      if (password.length < 6) {
        showToast('Password must be at least 6 characters.', 'error');
        return;
      }
      if (password !== confirmPassword) {
        showToast('Passwords do not match.', 'error');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating Account...';

      try {
        const response = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            full_name: fullName,
            email: email,
            phone: phone,
            password: password,
            confirm_password: confirmPassword,
            role: role
          })
        });

        const data = await response.json();

        if (response.ok && data.success) {
          showToast('Account registered successfully! Redirecting...', 'success');
          setTimeout(() => {
            window.location.href = data.redirect;
          }, 900);
        } else {
          showToast(data.error || 'Registration failed.', 'error');
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i class="fa-solid fa-user-plus"></i> Register Account';
        }
      } catch (err) {
        showToast('Network error during registration.', 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-user-plus"></i> Register Account';
      }
    });
  }
});
