/* Tiger Marketing CRM - JavaScript */

// Mobile sidebar toggle
function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('open');
}

// Close sidebar on mobile when clicking outside
document.addEventListener('click', function(e) {
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.querySelector('.mobile-toggle');
    if (sidebar && sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggle) {
        sidebar.classList.remove('open');
    }
});

// Auto-dismiss flash messages after 4 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(function(flash) {
        setTimeout(function() {
            flash.style.opacity = '0';
            flash.style.transition = 'opacity 0.3s';
            setTimeout(function() { flash.remove(); }, 300);
        }, 4000);
    });
});

// Delete confirmation
function confirmDelete(btn) {
    const row = btn.closest('tr') || btn.closest('.action-links');
    const confirmEl = row.querySelector('.confirm-delete');
    if (confirmEl) {
        btn.style.display = 'none';
        confirmEl.classList.add('show');
    }
}

function cancelDelete(btn) {
    const row = btn.closest('tr') || btn.closest('.action-links');
    const confirmEl = row.querySelector('.confirm-delete');
    const deleteBtn = row.querySelector('.delete-trigger');
    if (confirmEl) {
        confirmEl.classList.remove('show');
        if (deleteBtn) deleteBtn.style.display = '';
    }
}

// Format currency
function formatMoney(amount) {
    if (!amount && amount !== 0) return '-';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

// Format date nicely
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// Search with debounce
let searchTimeout;
function debounceSearch(input, formId) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(function() {
        document.getElementById(formId).submit();
    }, 500);
}

// Quick filter change
function filterChange(select) {
    select.closest('form').submit();
}
