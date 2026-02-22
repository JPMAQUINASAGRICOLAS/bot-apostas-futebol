import requests
import datetime
import pytz
import time
import sys

print("🚀 BOT EXTREMO INICIANDO...")

# ==========================================
# CONFIGURAÇÕES
# ==========================================

API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

HEADERS = {
    "X-Auth-Token": API_TOKEN
}

FUSO = pytz.timezone("America/Sao_Paulo")


# ==========================================
# TELEGRAM
# ==========================================

def enviar_telegram(msg):

    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }

    try:

        r = requests.post(url, json=payload, timeout=15)

        print("📨 Status Telegram:", r.status_code)

    except Exception as e:

        print("Erro Telegram:", e)


# ==========================================
# BUSCAR JOGOS DE HOJE
# ==========================================

def buscar_jogos():

    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")

    url = f"https://api.football-data.org/v4/matches?dateFrom={hoje}&dateTo={hoje}"

    try:

        r = requests.get(url, headers=HEADERS, timeout=20)

        print("🌐 Status API:", r.status_code)

        if r.status_code != 200:

            print(r.text)
            return []

        data = r.json()

        jogos = []

        for m in data.get("matches", []):

            if m["status"] not in ["TIMED", "SCHEDULED"]:
                continue

            jogos.append({

                "home": m["homeTeam"]["name"],
                "away": m["awayTeam"]["name"],
                "liga": m["competition"]["name"]

            })

        print("⚽ Jogos encontrados:", len(jogos))

        return jogos

    except Exception as e:

        print("Erro API:", e)

        return []


# ==========================================
# ANALISE EXTREMA
# ==========================================

def analisar(jogo):

    # modelo extremo simplificado e estável

    prob = 0.78

    if prob >= 0.75:

        return {

            "jogo": f"{jogo['home']} x {jogo['away']}",
            "liga": jogo["liga"],
            "palpite": "Over 1.5 gols",
            "conf": int(prob * 10)

        }

    return None


# ==========================================
# EXECUTAR
# ==========================================

def executar():

    print("⏰ Executando análise...")

    enviar_telegram("🤖 BOT EXTREMO ONLINE")

    jogos = buscar_jogos()

    if not jogos:

        enviar_telegram("⚠️ Nenhum jogo encontrado hoje")
        return


    palpites = []

    for j in jogos:

        res = analisar(j)

        if res:
            palpites.append(res)


    if not palpites:

        enviar_telegram("⚠️ Nenhum palpite encontrado")
        return


    msg = "🎯 <b>PALPITES EXTREMOS</b>\n\n"

    for p in palpites[:10]:

        msg += (

            f"⚽ {p['jogo']}\n"
            f"🏆 {p['liga']}\n"
            f"🎯 {p['palpite']}\n"
            f"🔥 Confiança: {p['conf']}/10\n\n"

        )

    enviar_telegram(msg)


# ==========================================
# LOOP PRINCIPAL
# ==========================================

try:

    executar()

    print("✅ BOT FINALIZADO")

except Exception as e:

    print("ERRO FATAL:", e)

time.sleep(10)

sys.exit(0)
