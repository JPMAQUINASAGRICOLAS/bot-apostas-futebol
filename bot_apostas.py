import requests
import time
from datetime import datetime

# ==========================
# CONFIGURAÇÕES
# ==========================

API_KEY = "1a185fa6bcccfcada90c54b747eb1172"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

URL_FIXTURES = "https://v3.football.api-sports.io/fixtures"
URL_TELEGRAM = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

HEADERS = {
    "x-apisports-key": API_KEY
}

# ==========================
# TELEGRAM
# ==========================

def enviar_telegram(msg):

    try:

        requests.post(
            URL_TELEGRAM,
            data={
                "chat_id": CHAT_ID,
                "text": msg
            }
        )

        print("📩 Mensagem enviada ao Telegram")

    except Exception as e:

        print("Erro Telegram:", e)


# ==========================
# PEGAR JOGOS DO DIA
# ==========================

def pegar_jogos_hoje():

    hoje = datetime.now().strftime("%Y-%m-%d")

    params = {
        "date": hoje,
        "timezone": "America/Sao_Paulo"
    }

    response = requests.get(
        URL_FIXTURES,
        headers=HEADERS,
        params=params
    )

    if response.status_code != 200:

        print("❌ Erro ao conectar API:", response.status_code)
        return []

    data = response.json()

    jogos = data.get("response", [])

    print(f"📊 Jogos encontrados hoje: {len(jogos)}")

    return jogos


# ==========================
# ANALISAR JOGOS
# ==========================

def analisar_jogos(jogos):

    selecionados = []

    for jogo in jogos:

        try:

            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            liga = jogo["league"]["name"]

            status = jogo["fixture"]["status"]["short"]

            if status != "NS":
                continue

            # confiança simulada (até integrar odds reais)
            confianca = abs(hash(home + away)) % 100

            if confianca >= 70:

                texto = (
                    f"⚽ {home} vs {away}\n"
                    f"🏆 {liga}\n"
                    f"📊 Confiança: {confianca}%\n"
                )

                selecionados.append(texto)

        except:

            continue

    print(f"🔥 Jogos qualificados: {len(selecionados)}")

    return selecionados


# ==========================
# EXECUÇÃO PRINCIPAL
# ==========================

def executar():

    print("🤖 BOT INICIADO")

    jogos = pegar_jogos_hoje()

    if not jogos:

        enviar_telegram("❌ Nenhum jogo encontrado hoje")
        return

    analise = analisar_jogos(jogos)

    if not analise:

        enviar_telegram("❌ Nenhum jogo qualificado hoje")
        return

    mensagem = "🔥 TOP JOGOS DO DIA\n\n"

    limite = min(len(analise), 10)

    for i in range(limite):

        mensagem += analise[i] + "\n"

    enviar_telegram(mensagem)


# ==========================
# LOOP 24H
# ==========================

print("🚀 BOT PROFISSIONAL INICIADO")

enviar_telegram("🤖 Bot iniciado e analisando jogos do dia!")

while True:

    executar()

    print("⏱ Nova análise em 30 minutos")

    time.sleep(1800)
