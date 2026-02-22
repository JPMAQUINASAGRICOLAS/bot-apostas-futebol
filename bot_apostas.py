import requests
import datetime
import pytz

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
        print("STATUS TELEGRAM:", r.status_code)
        print("RESPOSTA:", r.text)
    except Exception as e:
        print("ERRO TELEGRAM:", e)

# ==========================================
# BUSCAR JOGOS DO DIA
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
        r = requests.get(url, headers=headers, params=params, timeout=15)

        print("STATUS API:", r.status_code)

        if r.status_code != 200:
            print("ERRO API:", r.text)
            return []

        data = r.json()
        return data.get("matches", [])

    except Exception as e:
        print("ERRO BUSCAR JOGOS:", e)
        return []

# ==========================================
# GERAR PALPITES SIMPLES
# ==========================================

def gerar_palpites():

    jogos = buscar_jogos()

    if not jogos:
        return None

    agora = datetime.datetime.now(FUSO).strftime("%H:%M")

    msg = f"🎯 PALPITES DO DIA ({agora})\n\n"

    contador = 0

    for jogo in jogos:

        if jogo["status"] in ["SCHEDULED", "TIMED"]:

            home = jogo["homeTeam"]["name"]
            away = jogo["awayTeam"]["name"]
            liga = jogo["competition"]["name"]

            msg += (
                f"⚽ {home} x {away}\n"
                f"🏆 {liga}\n"
                f"🔥 Palpite: Over 1.5 gols\n\n"
            )

            contador += 1

        if contador >= 5:
            break

    if contador == 0:
        return None

    return msg

# ==========================================
# EXECUTAR
# ==========================================

if __name__ == "__main__":

    print("BOT ONLINE")

    mensagem = gerar_palpites()

    if mensagem:
        enviar_telegram(mensagem)
    else:
        enviar_telegram("❌ Nenhum jogo encontrado hoje.")
