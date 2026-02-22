import requests
import datetime
import pytz
import time

# ==========================================
# CONFIGURAÇÕES
# ==========================================

API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

FUSO = pytz.timezone("America/Sao_Paulo")

# ==========================================
# TELEGRAM
# ==========================================

def enviar_telegram(msg):

    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": msg
    }

    try:
        r = requests.post(url, data=payload, timeout=15)
        print("Telegram:", r.status_code, r.text)
    except Exception as e:
        print("Erro Telegram:", e)

# ==========================================
# BUSCAR JOGOS
# ==========================================

def buscar_jogos():

    url = "https://api.football-data.org/v4/matches"

    headers = {
        "X-Auth-Token": API_TOKEN
    }

    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")

    params = {
        "dateFrom": hoje,
        "dateTo": hoje
    }

    try:
        r = requests.get(url, headers=headers, params=params)

        print("API:", r.status_code)

        if r.status_code != 200:
            print(r.text)
            return []

        return r.json()["matches"]

    except Exception as e:
        print("Erro API:", e)
        return []

# ==========================================
# GERAR MSG
# ==========================================

def gerar_msg():

    jogos = buscar_jogos()

    agora = datetime.datetime.now(FUSO).strftime("%H:%M")

    if not jogos:
        return f"❌ Nenhum jogo encontrado ({agora})"

    msg = f"🎯 PALPITES ({agora})\n\n"

    count = 0

    for j in jogos:

        if j["status"] in ["SCHEDULED", "TIMED"]:

            msg += f"{j['homeTeam']['name']} x {j['awayTeam']['name']}\n"
            msg += f"{j['competition']['name']}\n"
            msg += f"Palpite: Over 1.5 gols\n\n"

            count += 1

        if count == 5:
            break

    return msg

# ==========================================
# LOOP INFINITO
# ==========================================

print("BOT INICIADO")

enviar_telegram("🤖 BOT ONLINE")

while True:

    try:

        print("Buscando jogos...")

        msg = gerar_msg()

        enviar_telegram(msg)

        print("Aguardando 1 hora...")

        time.sleep(3600)

    except Exception as e:

        print("Erro geral:", e)

        time.sleep(60)
