import requests
import time
from datetime import datetime, timedelta

# =========================
# CONFIGURAÇÕES
# =========================

API_KEY = "1a185fa6bcccfcada90c54b747eb1172"
TELEGRAM_TOKEN = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

URL_API = "https://v3.football.api-sports.io/fixtures"
URL_TELEGRAM = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

HEADERS = {
    "x-apisports-key": API_KEY
}

# =========================
# ENVIAR TELEGRAM
# =========================

def enviar_telegram(msg):
    try:
        data = {
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }

        requests.post(URL_TELEGRAM, data=data)
        print("📩 Enviado Telegram com sucesso")

    except Exception as e:
        print("Erro Telegram:", e)

# =========================
# BUSCAR JOGOS DO DIA
# =========================

def buscar_jogos():
    hoje = datetime.now().strftime("%Y-%m-%d")

    params = {
        "date": hoje,
        "timezone": "America/Sao_Paulo"
    }

    response = requests.get(URL_API, headers=HEADERS, params=params)

    if response.status_code != 200:
        print("Erro API")
        return []

    data = response.json()
    jogos = data.get("response", [])

    print(f"📊 Jogos encontrados hoje: {len(jogos)}")

    return jogos

# =========================
# ANALISAR E GERAR PALPITE
# =========================

def analisar_jogos(jogos):

    melhores = []

    for jogo in jogos:

        try:

            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            gols_home = jogo["goals"]["home"]
            gols_away = jogo["goals"]["away"]

            # lógica simples elite
            if gols_home is None:
                gols_home = 0

            if gols_away is None:
                gols_away = 0

            total = gols_home + gols_away

            # definir palpite
            if total >= 3:
                palpite = "Over 2.5 gols"
                confianca = 80

            elif gols_home > gols_away:
                palpite = f"{home} vence"
                confianca = 75

            elif gols_away > gols_home:
                palpite = f"{away} vence"
                confianca = 75

            else:
                palpite = "Over 1.5 gols"
                confianca = 70

            hora = jogo["fixture"]["date"][11:16]

            melhores.append({
                "home": home,
                "away": away,
                "hora": hora,
                "palpite": palpite,
                "confianca": confianca
            })

        except:
            continue

    # ordenar por confiança
    melhores.sort(key=lambda x: x["confianca"], reverse=True)

    return melhores[:5]

# =========================
# MONTAR MENSAGEM
# =========================

def montar_msg(jogos):

    if not jogos:
        return "❌ Nenhum jogo qualificado hoje"

    msg = "🔥 <b>TOP 5 PALPITES DO DIA</b>\n\n"

    for j in jogos:

        msg += (
            f"⚽ {j['home']} vs {j['away']}\n"
            f"🕒 {j['hora']}\n"
            f"🎯 {j['palpite']}\n"
            f"📊 Confiança: {j['confianca']}%\n\n"
        )

    return msg

# =========================
# EXECUÇÃO PRINCIPAL
# =========================

def executar():

    print("🚀 BOT INICIADO")

    enviar_telegram("🤖 BOT INICIADO")

    while True:

        print("🤖 ANALISANDO JOGOS DO DIA...")

        jogos = buscar_jogos()

        melhores = analisar_jogos(jogos)

        msg = montar_msg(melhores)

        enviar_telegram(msg)

        print("✅ Enviado. Aguardando 24h")

        time.sleep(86400)  # 24 horas


# =========================

executar()
