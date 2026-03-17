/* Animation Styles */

/* Fade In */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.fade-in {
  animation: fadeIn 0.6s ease-out;
}

/* Slide Up */
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slide-up {
  animation: slideUp 0.5s ease-out;
}

/* Pulse */
@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.pulse {
  animation: pulse 2s ease-in-out infinite;
}

.pulse:hover {
  animation: none;
}

/* Shake */
@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  10%, 30%, 50%, 70%, 90% {
    transform: translateX(-5px);
  }
  20%, 40%, 60%, 80% {
    transform: translateX(5px);
  }
}

.shake {
  animation: shake 0.5s ease-out;
}

/* Spinner Large */
.spinner-large {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Navbar */
.navbar {
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-card-border);
  padding: var(--space-16) 0;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
  background-color: rgba(var(--color-surface), 0.95);
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.navbar-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-24);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.navbar-brand h1 {
  font-size: var(--font-size-xl);
  margin: 0;
}

.navbar-menu {
  display: flex;
  align-items: center;
  gap: var(--space-16);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--space-12);
}

.user-name {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: 500;
}

/* Usage Banner */
.usage-banner {
  background: linear-gradient(135deg, rgba(var(--color-success-rgb), 0.1), rgba(var(--color-success-rgb), 0.05));
  border: 1px solid rgba(var(--color-success-rgb), 0.2);
  border-radius: var(--radius-lg);
  padding: var(--space-20);
  margin-bottom: var(--space-32);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-20);
  animation: slideDown 0.5s ease-out;
}

.usage-banner--limit {
  background: linear-gradient(135deg, rgba(var(--color-error-rgb), 0.1), rgba(var(--color-error-rgb), 0.05));
  border-color: rgba(var(--color-error-rgb), 0.2);
}

.usage-info {
  display: flex;
  align-items: center;
  gap: var(--space-16);
  flex: 1;
}

.usage-icon {
  flex-shrink: 0;
}

.usage-icon svg {
  color: var(--color-success);
}

.usage-banner--limit .usage-icon svg {
  color: var(--color-error);
}

.usage-text h3 {
  font-size: var(--font-size-md);
  font-weight: 600;
  margin: 0 0 var(--space-4) 0;
}

.usage-text p {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;
}

.usage-progress {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--space-8);
}

.progress-bar-mini {
  width: 150px;
  height: 6px;
  background-color: var(--color-secondary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-bar-mini__fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary), var(--color-primary-hover));
  border-radius: var(--radius-full);
  transition: width 0.3s ease-out;
}

/* Usage Update in Results */
.usage-update {
  margin-top: var(--space-20);
  padding: var(--space-16);
  background-color: rgba(var(--color-info-rgb), 0.1);
  border: 1px solid rgba(var(--color-info-rgb), 0.2);
  border-radius: var(--radius-base);
}

.usage-update p {
  margin: var(--space-4) 0;
  font-size: var(--font-size-sm);
}

/* Modal Styles */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.3s ease-out;
}

.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
}

.modal-content {
  position: relative;
  background-color: var(--color-surface);
  border-radius: var(--radius-lg);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease-out;
}

.modal-close {
  position: absolute;
  top: var(--space-16);
  right: var(--space-16);
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: var(--space-8);
  border-radius: var(--radius-base);
  transition: background-color var(--duration-normal);
}

.modal-close:hover {
  background-color: var(--color-secondary);
}

.modal-header {
  padding: var(--space-32) var(--space-24) var(--space-16);
  text-align: center;
}

.modal-header h2 {
  font-size: var(--font-size-2xl);
  margin-bottom: var(--space-8);
}

.modal-header p {
  color: var(--color-text-secondary);
  font-size: var(--font-size-md);
}

.modal-body {
  padding: 0 var(--space-24) var(--space-32);
}

/* Pricing Card */
.pricing-card {
  border: 2px solid var(--color-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-24);
  background: linear-gradient(135deg, rgba(var(--color-teal-500-rgb), 0.05), transparent);
}

.pricing-header {
  text-align: center;
  margin-bottom: var(--space-24);
  padding-bottom: var(--space-20);
  border-bottom: 1px solid var(--color-border);
}

.pricing-header h3 {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-12);
}

.pricing-price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: var(--space-4);
}

.price {
  font-size: var(--font-size-4xl);
  font-weight: 600;
  color: var(--color-primary);
}

.period {
  font-size: var(--font-size-md);
  color: var(--color-text-secondary);
}

.pricing-features {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--space-24) 0;
}

.pricing-features li {
  padding: var(--space-8) 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

/* Progress Icon */
.progress-icon {
  display: flex;
  justify-content: center;
  margin-bottom: var(--space-16);
}

.progress-icon svg {
  color: var(--color-primary);
}

/* Language Hint */
.language-hint {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-12);
  font-style: italic;
}

/* Error Text */
.error-text {
  color: var(--color-error);
  font-size: var(--font-size-sm);
  margin-top: var(--space-8);
  font-weight: 500;
}

/* Responsive */
@media (max-width: 768px) {
  .usage-banner {
    flex-direction: column;
    align-items: flex-start;
  }

  .usage-progress {
    width: 100%;
    align-items: stretch;
  }

  .progress-bar-mini {
    width: 100%;
  }

  .navbar-container {
    flex-direction: column;
    gap: var(--space-12);
  }

  .user-info {
    flex-wrap: wrap;
    justify-content: center;
  }
}
