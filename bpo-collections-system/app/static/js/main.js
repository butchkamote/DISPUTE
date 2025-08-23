// Main JavaScript file for BPO Collections System

document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips everywhere
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Enable popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Add animation to newly added elements
    const fadeIn = (element) => {
        element.style.opacity = 0;
        element.style.display = 'block';
        
        let opacity = 0;
        const timer = setInterval(() => {
            if (opacity >= 1) {
                clearInterval(timer);
            }
            element.style.opacity = opacity;
            opacity += 0.1;
        }, 20);
    };
    
    // Table sorting functionality
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', () => {
            const table = header.closest('table');
            const columnIndex = Array.from(header.parentElement.children).indexOf(header);
            const rows = Array.from(table.querySelectorAll('tbody tr'));
            
            // Toggle sort direction
            const isAscending = header.classList.contains('sort-asc');
            
            // Reset all headers
            table.querySelectorAll('th').forEach(th => {
                th.classList.remove('sort-asc', 'sort-desc');
            });
            
            header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
            
            // Sort rows
            rows.sort((a, b) => {
                const cellA = a.children[columnIndex].textContent.trim();
                const cellB = b.children[columnIndex].textContent.trim();
                
                if (!isNaN(cellA) && !isNaN(cellB)) {
                    return isAscending ? cellA - cellB : cellB - cellA;
                } else {
                    return isAscending ? 
                        cellA.localeCompare(cellB) : 
                        cellB.localeCompare(cellA);
                }
            });
            
            // Reorder table rows
            const tbody = table.querySelector('tbody');
            rows.forEach(row => tbody.appendChild(row));
        });
    });
});