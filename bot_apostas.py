import requests
import datetime
import pytz

# ==============================
# CONFIGURAÇÕES
# ==============================
API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"
HEADERS = {"X-Auth-Token": API_TOKEN, "User-Agent": "Mozilla/5.0"}
FUSO = pytz.timezone("America/Sao_Paulo")

def enviar_telegram(msg):
    # URL corrigida com barra antes de sendMessage
    url_tel = f"https://api.telegram.org{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        r = requests.post(url_tel, json=payload, timeout=10)
        return r.status_code
    except:
        return None

def buscar_jogos():
    agora = datetime.datetime.now(FUSO)
    hoje = agora.strftime("%Y-%m-%d")
    amanha = (agora + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    # URL FIXA E CORRIGIDA (v4/matches com filtros)
    url_api = "https://api.football-data.org"
    params = {
        "dateFrom": hoje,
        "dateTo": amanha
    }
    
    try:
        # Passando os parâmetros de data separadamente para evitar erro de URL
        r = requests.get(url_api, headers=HEADERS, params=params, timeout=15)
        
        if r.status_code != 200:
            print(f"❌ Erro API: {r.status_code}")
            return [], []

        data = r.json()
        jogos_brutos = data.get("matches", [])
        
        ao_vivo = []
        agendados = []

        for m in jogos_brutos:
            nome_home = m["homeTeam"].get("shortName") or m["homeTeam"].get("name")
            nome_away = m["awayTeam"].get("shortName") or m["awayTeam"].get("name")
            placar_h = m["score"]["fullTime"].get("home", 0)
            placar_a = m["score"]["fullTime"].get("away", 0)
            
            info = {
                "home": nome_home,
                "away": nome_away,
                "placar": f"{placar_h} - {placar_a}",
                "liga": m["competition"]["name"]
            }
            
            if m["status"] in ["IN_PLAY", "PAUSED"]:
                ao_vivo.append(info)
            else:
                agendados.append(info)
        
        return ao_vivo, agendados
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return [], []

def executar():
    agora_str = datetime.datetime.now(FUSO).strftime('%H:%M')
    print(f"[{agora_str}] 🚀 Iniciando captura...")

    ao_vivo, agendados = buscar_jogos()
    
    if not ao_vivo and not agendados:
        print("⚠️ Sem jogos nas ligas do seu plano hoje.")
        return

    msg = f"⚽ <b>JOGOS DE HOJE ({agora_str})</b>\n\n"
    
    if ao_vivo:
        msg += "🔴 <b>AO VIVO:</b>\n"
        for j in ao_vivo:
            msg += f"• {j['home']} {j['placar']} {j['away']} (🏆 {j['liga']})\n"
        msg += "\n"

    if agendados:
        msg += "📅 <b>AGENDADOS:</b>\n"
        for j in agendados[:10]: # Top 10 jogos
            msg += f"• {j['home']} x {j['away']} (🏆 {j['liga']})\n"

    enviar_telegram(msg)
    print("✅ Sucesso! Mensagem enviada.")

if __name__ == "__main__":
    executar()
