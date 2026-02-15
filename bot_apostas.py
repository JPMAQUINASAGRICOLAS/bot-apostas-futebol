import requests
import time
from datetime import datetime

# CONFIGURAÇÕES
API_KEY = "4cbd56ddf35b371d573eee2b71cfc05c"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

# URLS
URL_FIXTURES = "https://v3.football.api-sports.io/fixtures"
URL_TELEGRAM = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"

HEADERS = {
    "x-apisports-key": API_KEY
}


# ENVIAR MENSAGEM TELEGRAM
def enviar_telegram(msg):
    try:
        response = requests.post(URL_TELEGRAM, data={
            "chat_id": CHAT_ID,
            "text": msg
        })

        if response.status_code == 200:
            print("📩 Enviado Telegram com sucesso")
        else:
            print("Erro Telegram:", response.text)

    except Exception as e:
        print("Erro ao enviar Telegram:", e)


# PEGAR JOGOS DO DIA
def pegar_jogos_hoje():

    hoje = datetime.utcnow().strftime("%Y-%m-%d")

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

            print("Erro API:", response.text)
            return []

        data = response.json()

        jogos = data.get("response", [])

        print(f"📊 Jogos encontrados hoje: {len(jogos)}")

        return jogos

    except Exception as e:

        print("Erro conexão API:", e)
        return []


# ANALISAR JOGOS
def analisar_jogos(jogos):

    selecionados = []

    for jogo in jogos:

        try:

            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            league = jogo["league"]["name"]
            horario = jogo["fixture"]["date"][11:16]

            # SIMULAÇÃO DE CONFIANÇA (depois podemos melhorar)
            confianca = abs(hash(home + away)) % 100

            if confianca >= 65:

                msg = (
                    f"⚽ {home} vs {away}\n"
                    f"🏆 {league}\n"
                    f"🕒 {horario}\n"
                    f"📊 Confiança: {confianca}%\n"
                )

                selecionados.append(msg)

        except:
            continue

    print(f"🔥 Jogos qualificados: {len(selecionados)}")

    return selecionados


# EXECUTAR BOT
def executar():

    print("\n🤖 ANALISANDO JOGOS...")

    jogos = pegar_jogos_hoje()

    if not jogos:

        enviar_telegram("❌ Nenhum jogo encontrado hoje")
        return

    analise = analisar_jogos(jogos)

    if not analise:

        enviar_telegram("❌ Nenhum jogo qualificado hoje")
        return

    mensagem = "🔥 TOP JOGOS DO DIA\n\n"

    for jogo in analise[:10]:

        mensagem += jogo + "\n"

    enviar_telegram(mensagem)


# LOOP PRINCIPAL
print("🚀 BOT INICIADO COM SUCESSO")

enviar_telegram("🤖 Bot iniciado e analisando jogos 24h")

while True:

    executar()

    print("⏱ Nova análise em 30 minutos")

    time.sleep(1800)
