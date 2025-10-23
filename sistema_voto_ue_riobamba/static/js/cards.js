// Función simple para voltear tarjetas
function flipCard(element) {
    console.log('Volteando tarjeta');
    element.classList.toggle('active');
}

// Función para volver al frente
function flipBack(element, event) {
    console.log('Volviendo al frente');
    event.stopPropagation();
    const card = element.closest('.flip-card');
    card.classList.remove('active');
    return false;
}
