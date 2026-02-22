import requests
import datetime
import pytz

# ==============================
# CONFIGURAÇÕES (SEUS DADOS)
# ==============================
API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"
HEADERS = {"X-Auth-Token": API_TOKEN, "User-Agent": "Mozilla/5.0"}
FUSO = pytz.timezone("America/Sao_Paulo")

# ==============================
# FUNÇÃO DE ENVIO TELEGRAM
# ==============================
def enviar_telegram(msg):
    url = f"https://api.telegram.org{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code
    except Exception as e:
        print(f"❌ Erro ao conectar com Telegram: {e}")
        return None

# ==============================
# CAPTURA DE JOGOS (AO VIVO E HOJE)
# ==============================
def buscar_jogos():
    agora = datetime.datetime.now(FUSO)
    hoje = agora.strftime("%Y-%m-%d")
    amanha = (agora + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Endpoint correto para matches na v4
    url = f"https://api.football-data.org{hoje}&dateTo={amanha}"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        
        if r.status_code == 429:
            print("⚠️ Limite de 10 chamadas/min atingido. Aguarde.")
            return []
        
        if r.status_code != 200:
            print(f"❌ Erro na API Football: {r.status_code}")
            return []

        data = r.json()
        jogos_brutos = data.get("matches", [])
        
        ao_vivo = []
        agendados = []

        for m in jogos_brutos:
            info = {
                "home": m["homeTeam"]["shortName"] or m["homeTeam"]["name"],
                "away": m["awayTeam"]["shortName"] or m["awayTeam"]["name"],
                "placar": f"{m['score']['fullTime']['home']} - {m['score']['fullTime']['away']}",
                "liga": m["competition"]["name"],
                "status": m["status"]
            }
            
            # Status de jogo rolando na v4: IN_PLAY ou PAUSED (intervalo)
            if m["status"] in ["IN_PLAY", "PAUSED"]:
                ao_vivo.append(info)
            elif m["status"] in ["SCHEDULED", "TIMED"]:
                agendados.append(info)
        
        return ao_vivo, agendados

    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return [], []

# ==============================
# EXECUÇÃO PRINCIPAL
# ==============================
def executar():
    hora_check = datetime.datetime.now(FUSO).strftime('%H:%M')
    print(f"[{hora_check}] 🔍 Verificando rodada...")

    jogos_live, jogos_hoje = buscar_jogos()
    
    msg = f"⚽ <b>MONITORAMENTO DE JOGOS - {hora_check}</b>\n\n"

    if jogos_live:
        msg += "🔴 <b>AO VIVO AGORA:</b>\n"
        for j in jogos_live:
            msg += f"• {j['home']} {j['placar']} {j['away']}\n(🏆 {j['liga']})\n\n"
    else:
        msg += "⚪ <i>Nenhum jogo rolando agora.</i>\n\n"

    if jogos_hoje:
        msg += "📅 <b>PRÓXIMOS JOGOS DE HOJE:</b>\n"
        # Mostra apenas os próximos 5 para não travar o Telegram
        for j in jogos_hoje[:5]:
            msg += f"• {j['home']} x {j['away']} (🏆 {j['liga']})\n"
    
    # Envia se houver qualquer informação útil
    if jogos_live or jogos_hoje:
        status = enviar_telegram(msg)
        if status == 200:
            print("✅ Relatório enviado ao Telegram.")
        else:
            print(f"❌ Erro ao enviar. Status: {status}")
    else:
        print("Empty: Nenhum jogo das suas ligas hoje.")

if __name__ == "__main__":
    executar()
