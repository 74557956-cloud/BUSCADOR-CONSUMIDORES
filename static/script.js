function limpiarTextoDictado(texto) {
    let t = texto.toLowerCase();

    // Mapeo amplio de números en palabras a dígitos
    const mapaNumeros = {
        "cero": "0", "uno": "1", "dos": "2", "tres": "3", "cuatro": "4",
        "cinco": "5", "seis": "6", "siete": "7", "ocho": "8", "nueve": "9", "diez": "10"
    };

    for (const palabra in mapaNumeros) {
        const re = new RegExp(`\\b${palabra}\\b`, "g");
        t = t.replace(re, mapaNumeros[palabra]);
    }

    // Remueve explícitamente palabras basura del dictado y todos los caracteres no alfanuméricos
    return t.replace(/guion|guión|raya|menos|espacio/g, "")
            .replace(/[^a-zA-Z0-9]/g, "") // Elimina comas, puntos, espacios y guiones
            .toUpperCase();
}

let recognition;

function buscarPorVoz() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert("Tu navegador no soporta búsqueda por voz. Por favor usa Google Chrome o Microsoft Edge.");
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = "es-PE";
    recognition.continuous = false;

    const btnMic = document.getElementById("btnMic");
    const estado = document.getElementById("estadoVoz");

    recognition.onstart = function() {
        btnMic.classList.add("grabando");
        estado.textContent = "Escuchando... dicta las primeras letras o código completo.";
    };

    recognition.onresult = function(event) {
        const textoOriginal = event.results[0][0].transcript;
        const textoLimpio = limpiarTextoDictado(textoOriginal);
        
        document.getElementById("inputTexto").value = textoLimpio;
        enviarConsultaBackend(textoLimpio);
    };

    recognition.onerror = function() {
        estado.textContent = "No se logró entender la voz. Intenta nuevamente.";
        btnMic.classList.remove("grabando");
    };

    recognition.onend = function() {
        btnMic.classList.remove("grabando");
        setTimeout(() => { estado.textContent = ""; }, 3000);
    };

    recognition.start();
}

function realizarBusqueda(event) {
    event.preventDefault();
    const texto = document.getElementById("inputTexto").value;
    const textoLimpio = limpiarTextoDictado(texto);
    enviarConsultaBackend(textoLimpio);
}

function enviarConsultaBackend(codigo) {
    const formData = new FormData();
    formData.append("query", codigo);

    fetch("/buscar", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        const tbody = document.getElementById("tablaCuerpo");
        if (data.exito) {
            let filasHTML = "";
            
            // Si devuelve múltiples coincidencias (por búsqueda parcial de 5 caracteres)
            const resultados = data.resultados || [data];

            resultados.forEach(item => {
                filasHTML += `
                    <tr>
                        <td><b>${item.codigo}</b></td>
                        <td>${item.descripcion}</td>
                        <td>${item.se}</td>
                        <td>${item.planta}</td>
                        <td><a href="${item.url_pdf}" target="_blank" class="btn-pdf-link">📄 Ver Plano PDF</a></td>
                    </tr>
                `;
            });

            tbody.innerHTML = filasHTML;
        } else {
            tbody.innerHTML = `<tr><td colspan="5" class="placeholder-row">${data.mensaje}</td></tr>`;
        }
    });
}

function limpiarBusqueda() {
    document.getElementById("inputTexto").value = "";
    document.getElementById("tablaCuerpo").innerHTML = `
        <tr><td colspan="5" class="placeholder-row">Ingresa un código o presiona el micrófono para realizar una consulta.</td></tr>
    `;
}