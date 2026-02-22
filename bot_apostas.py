import requests
import time
import datetime
import pytz
import sys

# ========================================
# CONFIGURAÇÕES
# ========================================
API_TOKEN = "63f7daeeecc84264992bd70d5d911610" 
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

HEADERS = {"X-Auth-Token": API_TOKEN, "User-Agent": "Mozilla/5.0"}
FUSO = pytz.timezone("America/Sao_Paulo")

# ========================================
# FUNÇÃO PARA ENVIAR MENSAGEM NO TELEGRAM
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
# CAPTURA DE JOGOS REAIS
# ========================================
def buscar_jogos_reais():
    url = "https://api.football-data.org/v4/matches"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"❌ Erro API: {r.status_code} - {r.text}")
            return []

        data = r.json()
        jogos_brutos = data.get("matches", [])

        # 👉 Print para debug: mostra todos os jogos retornados pela API
        print(f"🌐 Total de jogos recebidos da API: {len(jogos_brutos)}")
        for jogo in jogos_brutos:
            print(f"- {jogo['homeTeam']['name']} x {jogo['awayTeam']['name']} | Status: {jogo['status']} | Liga: {jogo['competition']['name']}")

        lista_final = []
        for m in jogos_brutos:
            if m["status"] in ["SCHEDULED", "TIMED"]:
                lista_final.append({
                    "home": m["homeTeam"]["shortName"] or m["homeTeam"]["name"],
                    "away": m["awayTeam"]["shortName"] or m["awayTeam"]["name"],
                    "liga": m["competition"]["name"],
                    "odds": {"over15": 1.45, "btts": 1.70, "dnb": 1.55}
                })
        return lista_final
    except Exception as e:
        print(f"❌ Erro na captura: {e}")
        return []

# ========================================
# FILTRAR JOGO
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
    print(f"[{hora_msg}] 🚀 BOT INICIANDO...")

    enviar_telegram(f"🚀 BOT ONLINE - analisando jogos das {hora_msg}...")

    jogos = buscar_jogos_reais()
    print(f"⚽ Jogos filtrados (SCHEDULED/TIMED): {len(jogos)}")

    if not jogos:
        msg = f"⚠️ Nenhum jogo encontrado hoje ({hora_msg})"
        print(msg)
        enviar_telegram(msg)
        return

    palpites = []
    for j in jogos:
        res = filtrar_jogo(j)
        if res:
            palpites.append(res)

    # Montagem da mensagem para o Telegram
    msg = f"🎯 PALPITES ATUALIZADOS ({hora_msg})\n\n"
    for p in palpites[:10]:
        msg += (
            f"⚽ {p['jogo']}\n"
            f"🏆 {p['liga']}\n"
            f"🎯 Palpite: {p['palpite']}\n"
            f"🔥 Confiança: {p['confianca']}/10\n\n"
        )

    enviar_telegram(msg)
    print("✅ BOT FINALIZADO")

if __name__ == "__main__":
    executar()
    time.sleep(5)
    sys.exit(0)
