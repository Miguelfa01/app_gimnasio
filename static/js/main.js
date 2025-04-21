// JavaScript principal para la aplicación de gestión de gimnasio Acuaryum

document.addEventListener('DOMContentLoaded', function() {
    // Inicialización de tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicialización de popovers de Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Toggle para el sidebar en dispositivos móviles
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.body.classList.toggle('sidebar-collapsed');
        });
    }

    // Función para formatear fechas en el formato local
    window.formatDate = function(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString();
    };

    // Función para formatear moneda
    window.formatCurrency = function(amount) {
        if (amount === null || amount === undefined) return '';
        return new Intl.NumberFormat('es-VE', { 
            style: 'currency', 
            currency: 'VES',
            minimumFractionDigits: 2 
        }).format(amount);
    };

    // Manejo de confirmación para eliminación
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('¿Está seguro que desea eliminar este elemento? Esta acción no se puede deshacer.')) {
                e.preventDefault();
            }
        });
    });

    // Validación de formularios
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

    // Inicialización de datepickers
    const datepickers = document.querySelectorAll('.datepicker');
    datepickers.forEach(input => {
        // Aquí se podría inicializar un datepicker si se usa alguna librería específica
        input.addEventListener('input', function(e) {
            // Validación básica de formato de fecha (YYYY-MM-DD)
            const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
            if (!dateRegex.test(this.value)) {
                this.setCustomValidity('Por favor ingrese una fecha en formato YYYY-MM-DD');
            } else {
                this.setCustomValidity('');
            }
        });
    });

    // Inicialización de selectores con búsqueda
    const selects = document.querySelectorAll('.select2');
    selects.forEach(select => {
        // Aquí se podría inicializar select2 si se usa esa librería
    });

    // Manejo de mensajes flash/alertas
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000); // Auto cerrar alertas después de 5 segundos
    });
});
