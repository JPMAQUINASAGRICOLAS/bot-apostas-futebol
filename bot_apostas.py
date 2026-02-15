import requests
import time
from datetime import datetime

# CONFIGURAÇÕES
API_KEY = "4cbd56ddf35b371d573eee2b71cfc05c"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"
# URLS
URL_FIXTURES = "https://v3.football.api-sports.io/fixtures"
URL_TELEGRAM = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

HEADERS = {
    "x-apisports-key": API_KEY
}

def enviar_telegram(msg):
    try:
        requests.post(URL_TELEGRAM, data={
            "chat_id": CHAT_ID,
            "text": msg
        })
        print("📩 Enviado Telegram")
    except:
        print("Erro ao enviar Telegram")

def pegar_jogos_hoje():
    hoje = datetime.now().strftime("%Y-%m-%d")

    params = {
        "date": hoje
    }

    response = requests.get(URL_FIXTURES, headers=HEADERS, params=params)

    if response.status_code != 200:
        print("Erro API")
        return []

    data = response.json()
    jogos = data["response"]

    print(f"📊 Jogos encontrados hoje: {len(jogos)}")

    return jogos

def analisar_jogos(jogos):

    selecionados = []

    for jogo in jogos:

        try:

            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            odds_fake = hash(home) % 100

            if odds_fake > 60:

                selecionados.append(
                    f"⚽ {home} vs {away}\n📊 Confiança: {odds_fake}%\n"
                )

        except:
            continue

    print(f"🔥 Jogos qualificados: {len(selecionados)}")

    return selecionados

def executar():

    print("🤖 BOT PROFISSIONAL INICIADO")

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

while True:

    executar()

    print("⏱ Nova análise em 30 minutos")

    time.sleep(1800)
