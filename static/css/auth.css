/* Authentication Pages Styling */

.auth-body {
  background: linear-gradient(135deg, rgba(var(--color-teal-500-rgb), 0.1) 0%, rgba(var(--color-brown-600-rgb), 0.05) 100%);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-24);
}

.auth-container {
  width: 100%;
  max-width: 440px;
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.auth-card {
  background-color: var(--color-surface);
  border: 1px solid var(--color-card-border);
  border-radius: var(--radius-lg);
  padding: var(--space-48) var(--space-32);
  box-shadow: var(--shadow-lg);
}

.auth-header {
  text-align: center;
  margin-bottom: var(--space-32);
}

.auth-header h1 {
  font-size: var(--font-size-3xl);
  font-weight: 600;
  margin-bottom: var(--space-8);
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-hover));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.auth-subtitle {
  color: var(--color-text-secondary);
  font-size: var(--font-size-md);
}

/* Alerts */
.alert {
  padding: var(--space-12) var(--space-16);
  border-radius: var(--radius-base);
  margin-bottom: var(--space-20);
  font-size: var(--font-size-sm);
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.alert--error {
  background-color: rgba(var(--color-error-rgb), 0.1);
  color: var(--color-error);
  border: 1px solid rgba(var(--color-error-rgb), 0.2);
}

.alert--success {
  background-color: rgba(var(--color-success-rgb), 0.1);
  color: var(--color-success);
  border: 1px solid rgba(var(--color-success-rgb), 0.2);
}

.alert--info {
  background-color: rgba(var(--color-info-rgb), 0.1);
  color: var(--color-info);
  border: 1px solid rgba(var(--color-info-rgb), 0.2);
}

/* Form Styles */
.form-group {
  margin-bottom: var(--space-20);
}

.form-checkbox {
  display: flex;
  align-items: center;
  gap: var(--space-8);
}

.form-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.form-checkbox label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  margin: 0;
}

.form-hint {
  display: block;
  margin-top: var(--space-4);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

/* Button Loader */
.btn-loader {
  display: inline-flex;
  align-items: center;
  gap: var(--space-8);
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Divider */
.auth-divider {
  display: flex;
  align-items: center;
  text-align: center;
  margin: var(--space-24) 0;
  position: relative;
}

.auth-divider::before,
.auth-divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--color-border);
}

.auth-divider span {
  padding: 0 var(--space-16);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

/* Features */
.auth-features {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-12);
  margin-top: var(--space-32);
  padding-top: var(--space-24);
  border-top: 1px solid var(--color-border);
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--space-8);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.feature-item svg {
  color: var(--color-success);
  flex-shrink: 0;
}

/* Terms */
.auth-terms {
  margin-top: var(--space-20);
  text-align: center;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* Responsive */
@media (max-width: 480px) {
  .auth-card {
    padding: var(--space-32) var(--space-24);
  }

  .auth-header h1 {
    font-size: var(--font-size-2xl);
  }
}

/* Input Focus Animation */
.form-control:focus {
  animation: inputFocus 0.3s ease-out;
}

@keyframes inputFocus {
  0% {
    box-shadow: 0 0 0 0 var(--color-focus-ring);
  }
  100% {
    box-shadow: 0 0 0 3px var(--color-focus-ring);
  }
}
