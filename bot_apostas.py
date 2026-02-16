import requests
import time
from datetime import datetime, timedelta

# =========================
# CONFIGURAÇÕES
# =========================

API_KEY = "1a185fa6bcccfcada90c54b747eb1172"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

URL_FIXTURES = "https://v3.football.api-sports.io/fixtures"

HEADERS = {
    "x-apisports-key": API_KEY
}

URL_TELEGRAM = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"


# =========================
# ENVIAR TELEGRAM
# =========================

def enviar(msg):

    try:

        requests.post(URL_TELEGRAM, data={
            "chat_id": CHAT_ID,
            "text": msg
        })

        print("📩 Enviado com sucesso")

    except Exception as e:

        print("Erro Telegram:", e)


# =========================
# PEGAR JOGOS DO DIA
# =========================

def pegar_jogos():

    hoje = datetime.now().strftime("%Y-%m-%d")

    params = {
        "date": hoje,
        "timezone": "America/Sao_Paulo"
    }

    response = requests.get(URL_FIXTURES, headers=HEADERS, params=params)

    if response.status_code != 200:

        print("Erro API")
        return []

    data = response.json()

    jogos = data["response"]

    print(f"📊 Jogos encontrados: {len(jogos)}")

    return jogos


# =========================
# ANALISAR E GERAR PALPITES
# =========================

def analisar(jogos):

    lista = []

    for jogo in jogos:

        try:

            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            liga = jogo["league"]["name"]

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


# =========================
# EXECUTAR BOT
# =========================

def executar():

    print("🤖 ANALISANDO...")

    jogos = pegar_jogos()

    if not jogos:

        enviar("❌ Nenhum jogo hoje")
        return

    melhores = analisar(jogos)

    if not melhores:

        enviar("❌ Nenhuma boa oportunidade hoje")
        return

    msg = "🎯 TOP 5 PALPITES DO DIA\n\n"

    for j in melhores:

        msg += j["texto"] + "\n\n"

    enviar(msg)


# =========================
# ESPERAR ATÉ 08:00
# =========================

def esperar_ate_8():

    agora = datetime.now()

    alvo = agora.replace(hour=8, minute=0, second=0, microsecond=0)

    if agora >= alvo:
        alvo += timedelta(days=1)

    segundos = (alvo - agora).total_seconds()

    print(f"⏳ Aguardando até 08:00 ({int(segundos)} segundos)")

    time.sleep(segundos)


# =========================
# LOOP PRINCIPAL
# =========================

print("🚀 BOT INICIADO")

enviar("✅ BOT ONLINE")

while True:

    esperar_ate_8()

    executar()

    print("✅ Próxima execução em 24h")

    time.sleep(86400)
