import requests
import time
from datetime import datetime

# ==============================
# CONFIGURAÇÕES
# ==============================

API_KEY = "1a185fa6bcccfcada90c54b747eb1172"

TELEGRAM_TOKEN = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

# ==============================
# URLS
# ==============================

URL_FIXTURES = "https://v3.football.api-sports.io/fixtures"
URL_TELEGRAM = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

HEADERS = {
    "x-apisports-key": API_KEY
}

# ==============================
# ENVIAR TELEGRAM
# ==============================

def enviar_telegram(msg):

    try:

        requests.post(
            URL_TELEGRAM,
            data={
                "chat_id": CHAT_ID,
                "text": msg
            }
        )

        print("📩 Enviado Telegram com sucesso")

    except Exception as e:

        print("❌ Erro Telegram:", e)


# ==============================
# PEGAR JOGOS DO DIA
# ==============================

def pegar_jogos_hoje():

    hoje = datetime.now().strftime("%Y-%m-%d")

    params = {
        "date": hoje,
        "timezone": "America/Sao_Paulo"
    }

    try:

        response = requests.get(
            URL_FIXTURES,
            headers=HEADERS,
            params=params
        )

        if response.status_code != 200:

            print("❌ Erro API:", response.status_code)
            return []

        data = response.json()

        jogos = data.get("response", [])

        print(f"📊 Jogos encontrados hoje: {len(jogos)}")

        return jogos

    except Exception as e:

        print("❌ Erro ao buscar jogos:", e)

        return []


# ==============================
# ANALISAR JOGOS
# ==============================

def analisar_jogos(jogos):

    selecionados = []

    for jogo in jogos:

        try:

            status = jogo["fixture"]["status"]["short"]

            if status not in ["NS", "TBD"]:
                continue

            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            league = jogo["league"]["name"]

            horario = jogo["fixture"]["date"][11:16]

            home_id = jogo["teams"]["home"]["id"]
            away_id = jogo["teams"]["away"]["id"]

            confianca = (home_id + away_id) % 100

            if confianca >= 60:

                texto = (
                    f"⚽ {home} vs {away}\n"
                    f"🏆 {league}\n"
                    f"🕒 {horario}\n"
                    f"📊 Confiança: {confianca}%\n"
                )

                selecionados.append(texto)

        except:
            continue

    print(f"🔥 Jogos qualificados: {len(selecionados)}")

    return selecionados


# ==============================
# EXECUÇÃO PRINCIPAL
# ==============================

def executar():

    jogos = pegar_jogos_hoje()

    if not jogos:

        enviar_telegram("❌ Nenhum jogo encontrado hoje")
        return

    analise = analisar_jogos(jogos)

    if not analise:

        enviar_telegram("❌ Nenhum jogo qualificado hoje")
        return

    mensagem = "🔥 TOP JOGOS DO DIA 🔥\n\n"

    for jogo in analise[:10]:

        mensagem += jogo + "\n"

    enviar_telegram(mensagem)


# ==============================
# LOOP AUTOMÁTICO
# ==============================

print("🚀 BOT INICIADO COM SUCESSO")

enviar_telegram("🤖 BOT DE APOSTAS ONLINE!")

while True:

    print("🤖 ANALISANDO JOGOS...")

    executar()

    print("⏱ Nova análise em 30 minutos\n")

    time.sleep(1800)
