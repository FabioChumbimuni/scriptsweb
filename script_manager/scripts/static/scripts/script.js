// scripts/static/scripts/script.js
function ejecutarScript(scriptId) {
    fetch(`/ejecutar/${scriptId}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ scriptId: scriptId })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.mensaje);
    })
    .catch(error => console.error("Error:", error));
}

// Función auxiliar para obtener la cookie CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
