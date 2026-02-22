import requests
import time
import datetime
import pytz

# ========================================
# SEUS TOKENS
# ========================================
API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

HEADERS = {"X-Auth-Token": API_TOKEN}
FUSO = pytz.timezone("America/Sao_Paulo")

# ========================================
# TELEGRAM
# ========================================
def enviar(msg):

    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }

    try:
        r = requests.post(url, json=payload, timeout=15)
        print("TELEGRAM STATUS:", r.status_code)
        print(r.text)

    except Exception as e:
        print("ERRO TELEGRAM:", e)


# ========================================
# BUSCAR JOGOS DE HOJE
# ========================================
def buscar_jogos():

    hoje = datetime.datetime.now(FUSO).date()

    url = f"https://api.football-data.org/v4/matches?dateFrom={hoje}&dateTo={hoje}"

    try:

        r = requests.get(url, headers=HEADERS, timeout=15)

        print("API STATUS:", r.status_code)

        if r.status_code != 200:
            print(r.text)
            return []

        data = r.json()

        jogos = []

        for m in data["matches"]:

            if m["status"] in ["TIMED", "SCHEDULED"]:

                home = m["homeTeam"]["name"]
                away = m["awayTeam"]["name"]
                liga = m["competition"]["name"]

                jogos.append(f"{home} x {away} ({liga})")

        return jogos

    except Exception as e:

        print("ERRO API:", e)
        return []


# ========================================
# EXECUTAR
# ========================================
def executar():

    agora = datetime.datetime.now(FUSO).strftime("%H:%M")

    print("EXECUTANDO:", agora)

    enviar(f"🚀 Bot online {agora}")

    jogos = buscar_jogos()

    if not jogos:

        enviar("⚠️ Nenhum jogo encontrado hoje")
        return

    msg = "🎯 <b>JOGOS DE HOJE</b>\n\n"

    for jogo in jogos[:10]:
        msg += f"⚽ {jogo}\n"

    enviar(msg)


# ========================================
# LOOP INFINITO (OBRIGATÓRIO NO RAILWAY)
# ========================================
print("BOT INICIADO")

while True:

    executar()

    print("AGUARDANDO 30 MINUTOS...\n")

    time.sleep(1800)
