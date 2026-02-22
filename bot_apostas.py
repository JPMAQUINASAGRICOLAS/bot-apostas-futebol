import requests
import datetime
import pytz
import time
import sys

# ========================================
# CONFIGURAÇÕES
# ========================================
API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

HEADERS = {
    "X-Auth-Token": API_TOKEN,
    "User-Agent": "Mozilla/5.0"
}
FUSO = pytz.timezone("America/Sao_Paulo")

# ========================================
# FUNÇÃO PARA ENVIAR MENSAGEM
# ========================================
def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"📨 Status do Telegram: {r.status_code}")
        return r.status_code
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")
        return None

# ========================================
# CAPTURA DE JOGOS
# ========================================
def buscar_jogos_reais():
    agora = datetime.datetime.now(FUSO)
    hoje = agora.strftime("%Y-%m-%d")
    
    url = f"https://api.football-data.org/v4/matches?dateFrom={hoje}&dateTo={hoje}"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"❌ Erro API: {r.status_code}")
            return []

        data = r.json()
        jogos_brutos = data.get("matches", [])

        lista_final = []
        for m in jogos_brutos:
            if m["status"] in ["TIMED", "SCHEDULED"]:
                lista_final.append({
                    "home": m["homeTeam"].get("shortName") or m["homeTeam"]["name"],
                    "away": m["awayTeam"].get("shortName") or m["awayTeam"]["name"],
                    "liga": m["competition"]["name"],
                    "odds": {"over15": 1.45, "btts": 1.70, "dnb": 1.55}  # odds de exemplo
                })
        return lista_final
    except Exception as e:
        print(f"❌ Erro na captura: {e}")
        return []

# ========================================
# FILTRO DE JOGOS (palpite)
# ========================================
def filtrar_jogo(jogo):
    stats = {"scored": 1.8, "conceded": 1.2, "over15": 80, "btts": 65}
    goal_expectancy = stats["scored"] + stats["conceded"]

    if goal_expectancy >= 2.6:
        pick = "Over 1.5 gols"
        conf = 8
    else:
        pick = f"DNB {jogo['home']}"
        conf = 6

    return {
        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
        "palpite": pick,
        "confianca": conf
    }

# ========================================
# EXECUÇÃO PRINCIPAL
# ========================================
def executar():
    agora = datetime.datetime.now(FUSO)
    hora_msg = agora.strftime('%H:%M')
    print(f"[{hora_msg}] Iniciando análise...")

    enviar_telegram(f"🚀 <b>Bot Online!</b> Analisando jogos das {hora_msg}...")

    jogos = buscar_jogos_reais()

    if not jogos:
        print("⚠️ Nenhum jogo encontrado hoje.")
        enviar_telegram(f"⚠️ Nenhum jogo encontrado hoje ({hora_msg}).")
        return

    palpites = [filtrar_jogo(j) for j in jogos]

    msg = f"🎯 <b>PALPITES ATUALIZADOS ({hora_msg})</b>\n\n"
    for p in palpites[:10]:  # envia até 10 palpites
        msg += (
            f"⚽ <b>{p['jogo']}</b>\n"
            f"🏆 {p['liga']}\n"
            f"🎯 Palpite: {p['palpite']}\n"
            f"🔥 Confiança: {p['confianca']}/10\n\n"
        )
    enviar_telegram(msg)
    print("✅ Bot finalizado com sucesso.")

# ========================================
if __name__ == "__main__":
    executar()
    time.sleep(5)
    sys.exit(0)
