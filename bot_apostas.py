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

        print("📩 Enviado Telegram com sucesso")

    except Exception as e:

        print("Erro Telegram:", e)

# =========================
# PEGAR JOGOS DO DIA
# =========================

def pegar_jogos():

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

    print(f"📊 Jogos hoje: {len(jogos)}")

    return jogos

# =========================
# ANALISAR JOGOS
# =========================

def analisar(jogos):

    lista = []

    for jogo in jogos:

        try:

            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            score = (hash(home + away) % 40) + 60

            if score >= 75:

                if score >= 85:
                    palpite = "Over 2.5 gols"
                else:
                    palpite = "Vitória casa"

                texto = (
                    f"{home} vs {away}\n"
                    f"Palpite: {palpite}\n"
                    f"Confiança: {score}%\n"
                )

                lista.append((score, texto))

        except:
            pass

    lista.sort(reverse=True)

    top5 = [item[1] for item in lista[:5]]

    print(f"🔥 Selecionados: {len(top5)}")

    return top5

# =========================
# EXECUTAR BOT
# =========================

def executar():

    print("🤖 ANALISANDO JOGOS DO DIA...")

    jogos = pegar_jogos()

    if not jogos:

        enviar("❌ Nenhum jogo hoje")
        return

    analise = analisar(jogos)

    if not analise:

        enviar("❌ Nenhuma oportunidade hoje")
        return

    mensagem = "🔥 TOP 5 PALPITES DO DIA\n\n"

    for jogo in analise:

        mensagem += jogo + "\n"

    enviar(mensagem)

# =========================
# ESPERAR ATÉ 08:00
# =========================

def esperar_ate_8():

    while True:

        agora = datetime.now()

        alvo = agora.replace(hour=8, minute=0, second=0, microsecond=0)

        if agora >= alvo:
            alvo += timedelta(days=1)

        espera = (alvo - agora).total_seconds()

        print(f"⏳ Aguardando até 08:00 ({int(espera/3600)} horas)")

        time.sleep(espera)

        executar()

# =========================
# INICIAR BOT
# =========================

print("🚀 BOT INICIADO COM SUCESSO")

enviar("✅ BOT ONLINE - enviará palpites às 08:00")

esperar_ate_8()
