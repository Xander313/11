// Función para obtener el token CSRF
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

// Función para eliminar una lista
function eliminarLista(listaId, listaNombre) {
    const csrftoken = getCookie('csrftoken');
    
    $.ajax({
        url: `/elecciones/eliminar_lista/${listaId}/`,
        type: 'POST',
        data: {
            'csrfmiddlewaretoken': csrftoken
        },
        success: function(response) {
            if (response.success) {
                // Mostrar mensaje de éxito
                Swal.fire({
                    title: '¡Eliminada!',
                    text: `La lista "${listaNombre}" ha sido eliminada correctamente.`,
                    icon: 'success',
                    confirmButtonText: 'Aceptar',
                    timer: 3000,
                    timerProgressBar: true
                }).then(() => {
                    // Recargar la página para actualizar la lista
                    window.location.reload();
                });
            } else {
                // Mostrar mensaje de error
                Swal.fire({
                    title: 'Error',
                    text: response.message || 'Ocurrió un error al eliminar la lista.',
                    icon: 'error',
                    confirmButtonText: 'Aceptar'
                });
            }
        },
        error: function(xhr, status, error) {
            console.error('Error al eliminar la lista:', error);
            Swal.fire({
                title: 'Error',
                text: 'Ocurrió un error al intentar eliminar la lista. Por favor, intente nuevamente.',
                icon: 'error',
                confirmButtonText: 'Aceptar'
            });
        }
    });
}

// Inicialización cuando el documento está listo
$(document).ready(function() {
    // Manejar clic en el botón de eliminar
    $(document).on('click', '.btn-eliminar-lista', function(e) {
        e.preventDefault();
        const listaId = $(this).data('lista-id');
        const listaNombre = $(this).closest('.card').find('.card-title').text().trim();
        
        // Mostrar confirmación con SweetAlert2
        Swal.fire({
            title: '¿Estás seguro?',
            html: `¿Deseas eliminar la lista <strong>${listaNombre}</strong>?<br><br>
                  <span class="text-danger">¡Esta acción no se puede deshacer!</span>`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar',
            reverseButtons: true,
            customClass: {
                confirmButton: 'btn btn-danger',
                cancelButton: 'btn btn-secondary mr-2'
            },
            buttonsStyling: false
        }).then((result) => {
            if (result.isConfirmed) {
                eliminarLista(listaId, listaNombre);
            }
        });
    });

    // Inicializar tooltips
    $('[data-toggle-tooltip="tooltip"]').tooltip({
        trigger: 'hover',
        placement: 'top'
    });
});
