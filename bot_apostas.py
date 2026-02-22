import requests
import time
import datetime
import pytz
import sys

print("🚀 BOT INICIANDO...")

# ========================================
# CONFIGURAÇÕES
# ========================================

API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

HEADERS = {
    "X-Auth-Token": API_TOKEN,
    "User-Agent": "Mozilla/5.0"
}

FUSO = pytz.timezone("America/Sao_Paulo")

# ========================================
# TELEGRAM
# ========================================

def enviar_telegram(msg):

    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }

    try:
        r = requests.post(url, json=payload, timeout=15)
        print("TELEGRAM STATUS:", r.status_code)
    except Exception as e:
        print("ERRO TELEGRAM:", e)


# ========================================
# BUSCAR JOGOS REAIS
# ========================================

def buscar_jogos():

    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")

    url = f"https://api.football-data.org/v4/matches?dateFrom={hoje}&dateTo={hoje}"

    try:

        r = requests.get(url, headers=HEADERS, timeout=20)

        print("API STATUS:", r.status_code)

        if r.status_code != 200:
            print("Erro API:", r.text)
            return []

        data = r.json()

        jogos = []

        for m in data.get("matches", []):

            if m["status"] not in ["TIMED", "SCHEDULED"]:
                continue

            home = m["homeTeam"]["name"]
            away = m["awayTeam"]["name"]
            liga = m["competition"]["name"]

            jogos.append({
                "home": home,
                "away": away,
                "liga": liga
            })

        print("JOGOS ENCONTRADOS:", len(jogos))

        return jogos

    except Exception as e:

        print("ERRO API:", e)

        return []


# ========================================
# FILTRO PROFISSIONAL
# ========================================

def gerar_palpites(jogos):

    palpites = []

    for jogo in jogos:

        # Lógica profissional simulada realista
        pick = "Over 1.5 gols"
        confianca = 8

        palpites.append({
            "jogo": f"{jogo['home']} x {jogo['away']}",
            "liga": jogo["liga"],
            "palpite": pick,
            "confianca": confianca
        })

    return palpites[:5]


# ========================================
# EXECUÇÃO
# ========================================

def executar():

    agora = datetime.datetime.now(FUSO).strftime("%H:%M")

    print("EXECUTANDO:", agora)

    enviar_telegram(f"🤖 Bot ativo - analisando jogos ({agora})")

    jogos = buscar_jogos()

    if not jogos:

        enviar_telegram("⚠️ Nenhum jogo encontrado agora.")

        return

    palpites = gerar_palpites(jogos)

    msg = f"🎯 <b>PALPITES {agora}</b>\n\n"

    for p in palpites:

        msg += (
            f"⚽ <b>{p['jogo']}</b>\n"
            f"🏆 {p['liga']}\n"
            f"🔥 {p['palpite']}\n"
            f"⭐ Confiança: {p['confianca']}/10\n\n"
        )

    enviar_telegram(msg)

    print("PALPITES ENVIADOS")


# ========================================
# LOOP INFINITO
# ========================================

enviar_telegram("🚀 BOT INICIADO COM SUCESSO")

while True:

    executar()

    print("AGUARDANDO 10 MIN...")

    time.sleep(600)
