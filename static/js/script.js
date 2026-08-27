/* ==================================================
   ShopAnalytica — Main JavaScript
   ==================================================
   Utility functions and interactive behavior for
   the e-commerce platform frontend.
   ================================================== */

// --------------------------------------------------
// Auto-dismiss flash alerts after 5 seconds
// --------------------------------------------------
document.addEventListener('DOMContentLoaded', function () {

    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(function (el) {
        new bootstrap.Tooltip(el);
    });

});


// --------------------------------------------------
// Format currency in Indian Rupees
// --------------------------------------------------
function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}


// --------------------------------------------------
// Show loading spinner on a button
// --------------------------------------------------
function showButtonLoading(button, text) {
    button.disabled = true;
    button.dataset.originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>' + (text || 'Loading...');
}

function hideButtonLoading(button) {
    button.disabled = false;
    button.innerHTML = button.dataset.originalText || button.innerHTML;
}


// --------------------------------------------------
// Debounce utility for search inputs
// --------------------------------------------------
function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}


// --------------------------------------------------
// Confirm action dialog
// --------------------------------------------------
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}


// --------------------------------------------------
// Show toast notification
// --------------------------------------------------
function showToast(message, type) {
    type = type || 'success';

    const iconMap = {
        success: 'bi-check-circle-fill',
        danger: 'bi-x-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        info: 'bi-info-circle-fill'
    };

    const colorMap = {
        success: '#10B981',
        danger: '#EF4444',
        warning: '#F59E0B',
        info: '#3B82F6'
    };

    const toast = document.createElement('div');
    toast.className = 'position-fixed bottom-0 end-0 p-3';
    toast.style.zIndex = '9999';
    toast.innerHTML =
        '<div class="toast show align-items-center border-0 shadow-lg" role="alert" ' +
        'style="background:#fff; border-left: 4px solid ' + colorMap[type] + ' !important; border-radius: 0.75rem;">' +
        '<div class="d-flex">' +
        '<div class="toast-body d-flex align-items-center gap-2">' +
        '<i class="bi ' + iconMap[type] + '" style="color:' + colorMap[type] + '; font-size: 1.2rem;"></i> ' +
        '<span>' + message + '</span>' +
        '</div>' +
        '<button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>' +
        '</div>' +
        '</div>';

    document.body.appendChild(toast);

    setTimeout(function () {
        toast.remove();
    }, 4000);
}


// --------------------------------------------------
// Quantity stepper (for cart)
// --------------------------------------------------
function updateQuantity(inputId, change) {
    var input = document.getElementById(inputId);
    if (!input) return;

    var currentVal = parseInt(input.value) || 1;
    var newVal = currentVal + change;
    var maxVal = parseInt(input.getAttribute('max')) || 999;

    if (newVal >= 1 && newVal <= maxVal) {
        input.value = newVal;
        // Trigger change event for form submission
        input.dispatchEvent(new Event('change'));
    }
}
