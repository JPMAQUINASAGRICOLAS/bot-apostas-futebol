import requests
import time
from datetime import datetime

API_KEY = "1a185fa6bcccfcada90c54b747eb1172"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

URL_FIXTURES = "https://v3.football.api-sports.io/fixtures"
URL_TELEGRAM = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"

HEADERS = {
    "x-apisports-key": API_KEY
}

ultimo_envio = None


def enviar(msg):

    try:

        requests.post(URL_TELEGRAM, data={
            "chat_id": CHAT_ID,
            "text": msg
        })

        print("📩 Enviado Telegram")

    except Exception as e:

        print("Erro:", e)


def pegar_jogos():

    hoje = datetime.now().strftime("%Y-%m-%d")

    params = {
        "date": hoje,
        "timezone": "America/Sao_Paulo"
    }

    response = requests.get(URL_FIXTURES, headers=HEADERS, params=params)

    if response.status_code != 200:

        return []

    return response.json()["response"]


def analisar(jogos):

    lista = []

    for jogo in jogos:

        try:

            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            score = abs(hash(home + away)) % 100

            if score > 75:

                if score > 90:
                    palpite = "🔥 Over 2.5 gols"
                elif score > 82:
                    palpite = f"🏆 Vitória {home}"
                else:
                    palpite = "⚽ Ambas marcam"

                lista.append({
                    "texto": f"{home} x {away}\n{palpite}\nConfiança: {score}%",
                    "score": score
                })

        except:
            pass

    lista.sort(key=lambda x: x["score"], reverse=True)

    return lista[:5]


def executar():

    print("🤖 Executando análise")

    jogos = pegar_jogos()

    if not jogos:

        enviar("❌ Nenhum jogo hoje")
        return

    melhores = analisar(jogos)

    if not melhores:

        enviar("❌ Nenhum palpite hoje")
        return

    msg = "🎯 TOP 5 PALPITES DO DIA\n\n"

    for j in melhores:

        msg += j["texto"] + "\n\n"

    enviar(msg)


print("🚀 BOT INICIADO")

enviar("✅ BOT ONLINE")

while True:

    agora = datetime.now()

    if agora.hour == 8 and agora.minute == 0:

        if ultimo_envio != agora.date():

            executar()

            ultimo_envio = agora.date()

            print("✅ Enviado hoje")

    time.sleep(30)
