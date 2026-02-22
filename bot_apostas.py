import time
import requests
import datetime
import pytz

print("🚀 BOT INICIANDO...")

# =============================
# SUAS CONFIGURAÇÕES
# =============================

TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"
API_TOKEN = "63f7daeeecc84264992bd70d5d911610"

HEADERS = {
    "X-Auth-Token": API_TOKEN
}

FUSO = pytz.timezone("America/Sao_Paulo")

# =============================
# TELEGRAM
# =============================

def enviar_telegram(msg):

    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=20
        )

        print("📨 Telegram status:", response.status_code)

    except Exception as e:
        print("❌ Erro Telegram:", e)


# =============================
# BUSCAR JOGOS
# =============================

def buscar_jogos():

    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")

    url = f"https://api.football-data.org/v4/matches?dateFrom={hoje}&dateTo={hoje}"

    try:

        r = requests.get(url, headers=HEADERS, timeout=20)

        print("🌐 API status:", r.status_code)

        if r.status_code != 200:
            print(r.text)
            return []

        data = r.json()

        jogos = []

        for m in data.get("matches", []):

            if m["status"] in ["TIMED", "SCHEDULED"]:

                jogos.append({
                    "home": m["homeTeam"]["name"],
                    "away": m["awayTeam"]["name"],
                    "liga": m["competition"]["name"]
                })

        print("⚽ Jogos encontrados:", len(jogos))

        return jogos

    except Exception as e:

        print("❌ Erro API:", e)

        return []


# =============================
# GERAR PALPITES
# =============================

def gerar_palpites(jogos):

    palpites = []

    for j in jogos[:5]:

        palpites.append({
            "texto":
            f"⚽ {j['home']} x {j['away']}\n"
            f"🏆 {j['liga']}\n"
            f"🎯 Palpite: Over 1.5 gols\n"
            f"🔥 Confiança: 8/10\n"
        })

    return palpites


# =============================
# EXECUÇÃO
# =============================

def executar():

    agora = datetime.datetime.now(FUSO).strftime("%H:%M")

    print("⏰ Executando:", agora)

    jogos = buscar_jogos()

    if not jogos:

        enviar_telegram("⚠️ Nenhum jogo encontrado hoje.")

        return

    palpites = gerar_palpites(jogos)

    msg = f"🎯 PALPITES DO DIA ({agora})\n\n"

    for p in palpites:

        msg += p["texto"] + "\n"

    enviar_telegram(msg)


# =============================
# LOOP INFINITO
# =============================

print("✅ BOT ONLINE")

enviar_telegram("✅ Bot iniciado com sucesso.")

while True:

    executar()

    print("⏳ Aguardando 10 minutos...")

    time.sleep(600)
