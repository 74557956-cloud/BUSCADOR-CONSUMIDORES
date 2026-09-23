from flask import Flask, render_template, request, jsonify
import requests
import re

app = Flask(__name__)

# --- URL DE TU FLUJO DE POWER AUTOMATE ---
URL_POWER_AUTOMATE = "https://default6d25241940fe4964bb31e8aaa96d97.66.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/19/workflows/1a93dde9c2ad4800a49d650c0db1a489/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=UcYS9k4cVM32rVXvMxyaqRr1kefY4UmJI81c6fwhTHE"

# URL base para abrir los archivos PDF de los planos en SharePoint
URL_BASE_PLANOS = "https://unacemcompe.sharepoint.com/sites/UNACEM_PE_INSPDMEGC/Documentos%20compartidos/BUSCADOR%20CONSUMIDORES/PLANOS/"

def limpiar_codigo(texto):
    """Elimina espacios, guiones, puntos y comas para comparaciones flexibles."""
    if not texto:
        return ""
    return re.sub(r'[\s\.\-,]+', '', str(texto)).upper()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    query = request.form.get('query', '').strip()
    query_limpia = limpiar_codigo(query)

    if not query_limpia:
        return jsonify({'exito': False, 'mensaje': 'Por favor ingresa o dicta un código.'})

    try:
        # Petición GET al flujo de Power Automate en tiempo real
        respuesta = requests.get(URL_POWER_AUTOMATE, timeout=15)

        if respuesta.status_code == 200:
            datos_json = respuesta.json()

            # Extraer las listas devueltas por Power Automate
            lista_cons = datos_json.get('consumidores', [])
            lista_eq = datos_json.get('equipos', [])

            # 1. BÚSQUEDA PARCIAL/SUBSTRING (Soporta buscar desde 5 caracteres en adelante)
            matches_cons = [
                item for item in lista_cons 
                if query_limpia in limpiar_codigo(item.get('CÓDIGO DE UBICACIÓN') or item.get('CODIGO DE UBICACION'))
            ]

            matches_eq = [
                item for item in lista_eq 
                if query_limpia in limpiar_codigo(item.get('CÓDIGO DE UBICACIÓN') or item.get('CODIGO DE UBICACION'))
            ]

            # Collect unique real location codes found
            codigos_encontrados = set()
            for m in matches_cons + matches_eq:
                cod = m.get('CÓDIGO DE UBICACIÓN') or m.get('CODIGO DE UBICACION')
                if cod:
                    codigos_encontrados.add(cod)

            if codigos_encontrados:
                resultados = []

                for cod_real in codigos_encontrados:
                    cod_limpio = limpiar_codigo(cod_real)

                    # Emparejar datos de Consumidores
                    m_cons = next(
                        (i for i in lista_cons if limpiar_codigo(i.get('CÓDIGO DE UBICACIÓN') or i.get('CODIGO DE UBICACION')) == cod_limpio), 
                        None
                    )
                    
                    # Emparejar datos de Equipos
                    m_eq = next(
                        (i for i in lista_eq if limpiar_codigo(i.get('CÓDIGO DE UBICACIÓN') or i.get('CODIGO DE UBICACION')) == cod_limpio), 
                        None
                    )

                    # Extraer campos de Consumidores
                    desc = 'N/A'
                    se = 'N/A'
                    if m_cons:
                        desc = m_cons.get('DESCRIPCION') or m_cons.get('DESCRIPCIÓN', 'N/A')
                        se = m_cons.get('S_x002e_E_') or m_cons.get('S.E') or m_cons.get('S_x002e_E', 'N/A')

                    # Extraer campos de Equipos
                    planta = 'N/A'
                    plano_info = ''
                    if m_eq:
                        planta = m_eq.get('UBICACIÓN EN PLANTA') or m_eq.get('UBICACION EN PLANTA', 'N/A')
                        plano_info = str(m_eq.get('PLANO', '')).strip()

                    # Construcción del enlace dinámico al PDF
                    if plano_info.startswith("http://") or plano_info.startswith("https://"):
                        link_pdf = plano_info
                    else:
                        nombre_archivo = plano_info if plano_info and plano_info.lower() not in ['nan', 'none'] else f"{cod_real}.pdf"
                        if not nombre_archivo.lower().endswith('.pdf'):
                            nombre_archivo += '.pdf'
                        link_pdf = f"{URL_BASE_PLANOS}{nombre_archivo}"

                    resultados.append({
                        'codigo': cod_real,
                        'descripcion': desc,
                        'se': se,
                        'planta': planta,
                        'url_pdf': link_pdf
                    })

                # Si solo hay 1 resultado, devuelve la estructura tradicional además de 'resultados'
                primer_res = resultados[0]
                return jsonify({
                    'exito': True,
                    'codigo': primer_res['codigo'],
                    'descripcion': primer_res['descripcion'],
                    'se': primer_res['se'],
                    'planta': primer_res['planta'],
                    'url_pdf': primer_res['url_pdf'],
                    'resultados': resultados
                })
            else:
                return jsonify({'exito': False, 'mensaje': f'No se encontraron coincidencias para: {query}'})
        else:
            return jsonify({'exito': False, 'mensaje': f'Error de respuesta en Power Automate (Código {respuesta.status_code})'})

    except Exception as e:
        return jsonify({'exito': False, 'mensaje': f'Error de conexión con la nube: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)