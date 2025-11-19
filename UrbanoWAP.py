import requests
from bs4 import BeautifulSoup
import time
import schedule
import urllib.parse
import os

# ================== CONFIGURA ESTO ==================
CODIGO_ENVIO = "N242290614420"
SHI_CODIGO = "001039"
URL_API = f"https://apis.urbano.com.ar/cespecifica/?shi_codigo={SHI_CODIGO}&cli_codigo={CODIGO_ENVIO}"

# Estas variables las inyectará GitHub Actions
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY")
TU_NUMERO_WHATSAPP = "+5491123905645"
INTERVALO_MINUTOS = int(os.getenv("INTERVALO_MINUTOS", "10"))  # 10 por defecto
# ====================================================

estado_anterior = None

# INTENTAMOS VARIAS FORMAS HASTA QUE UNA FUNCIONE
def crear_sesion():
    session = requests.Session()
    
    # 1) Headers ultra reales
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    })

    # 2) Si tenés proxy que bloquea, lo desactivamos solo para este dominio
    proxies = {
        "http": None,
        "https": None,            # <--- ESTO SALTA EL PROXY PROBLEMÁTICO
    }

    # 3) Si igual falla, probamos con verify=False (solo para este sitio)
    return session, proxies

session, proxies = crear_sesion()

def obtener_estado():
    try:
        # Primera intento normal
        r = session.get(URL_API, proxies=proxies, timeout=20)
        if r.status_code == 200:
            return parsear_html(r.text)
        
        # Si da 403, intentamos sin verificar certificado (funciona en muchos proxies squid)
        r = session.get(URL_API, proxies=proxies, verify=False, timeout=20)
        if r.status_code == 200:
            return parsear_html(r.text)
            
    except Exception as e:
        return f"Error de conexión: {str(e)[:100]}"

def parsear_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    estado = soup.find("h2")
    texto = estado.get_text(strip=True) if estado else "Sin estado"
    
    movimientos = []
    for fila in soup.select("table tr")[1:4]:
        cols = fila.find_all("td")
        if len(cols) >= 3:
            movimientos.append(f"{cols[0].text.strip()} {cols[1].text.strip()} → {cols[2].text.strip()}")
    
    ultimos = "\n".join(movimientos) if movimientos else "Sin movimientos"
    return f"{texto}\n\nÚltimos:\n{ultimos}"

def enviar_whatsapp(mensaje):
    msg = urllib.parse.quote(mensaje)
    url = f"https://api.callmebot.com/whatsapp.php?phone={TU_NUMERO_WHATSAPP}&text={msg}&apikey={CALLMEBOT_API_KEY}"
    try:
        requests.get(url, timeout=10)
        print("✅ WhatsApp enviado")
    except:
        print("❌ Falló WhatsApp")

def chequear():
    global estado_anterior
    print(f"\n[{time.strftime('%d/%m %H:%M')}] Chequeando...")
    actual = obtener_estado()

    if "Error" in actual or "403" in actual:
        print("⚠️  Falló esta vez →", actual)
        return

    if estado_anterior is None:
        enviar_whatsapp(f"✅ Monitor Urbano OK (incluso con proxy)\nEnvío: {CODIGO_ENVIO}\n\nEstado:\n{actual}")
        print("Primer estado capturado")
    elif actual != estado_anterior:
        enviar_whatsapp(f"🚨 CAMBIO DE ESTADO\nEnvío: {CODIGO_ENVIO}\n\nAntes:\n{estado_anterior}\n\nAhora:\n{actual}")
        print("¡CAMBIO!")
    else:
        print("Sin cambios")

    estado_anterior = actual

# Ignorar warnings de certificado si usamos verify=False
requests.packages.urllib3.disable_warnings()

chequear()
schedule.every(INTERVALO_MINUTOS).minutes.do(chequear)
print(f"🚀 Monitor corriendo cada {INTERVALO_MINUTOS} min")
while True:
    schedule.run_pending()
    time.sleep(30)