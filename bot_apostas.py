import requests
import time
import datetime
import pytz
import sys

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

        print("Telegram status:", r.status_code)

        if r.status_code != 200:
            print("Erro Telegram:", r.text)

        return r.status_code

    except Exception as e:
        print("Erro Telegram:", e)
        return None


# ========================================
# BUSCAR JOGOS DE HOJE
# ========================================
def buscar_jogos_reais():

    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")

    url = (
        "https://api.football-data.org/v4/matches"
        f"?dateFrom={hoje}&dateTo={hoje}"
    )

    try:

        r = requests.get(url, headers=HEADERS, timeout=20)

        print("Status API:", r.status_code)

        if r.status_code != 200:
            print(r.text)
            return []

        data = r.json()

        jogos = data.get("matches", [])

        lista = []

        for m in jogos:

            if m["status"] in ["TIMED", "SCHEDULED"]:

                home = m["homeTeam"]["name"]
                away = m["awayTeam"]["name"]
                liga = m["competition"]["name"]

                lista.append({
                    "home": home,
                    "away": away,
                    "liga": liga
                })

        print("Jogos encontrados:", len(lista))

        return lista

    except Exception as e:

        print("Erro API:", e)

        return []


# ========================================
# ANALISAR JOGO
# ========================================
def filtrar_jogo(jogo):

    stats = {
        "scored": 1.8,
        "conceded": 1.2
    }

    expectativa = stats["scored"] + stats["conceded"]

    if expectativa >= 2.6:

        pick = "Over 1.5 gols"
        confianca = 8

    else:

        pick = f"DNB {jogo['home']}"
        confianca = 6

    return {
        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
        "palpite": pick,
        "confianca": confianca
    }


# ========================================
# EXECUÇÃO
# ========================================
def executar():

    agora = datetime.datetime.now(FUSO)

    hora = agora.strftime("%H:%M")

    print("Iniciando bot...")

    enviar_telegram(
        f"🚀 <b>BOT ONLINE</b>\n"
        f"🕒 Hora: {hora}\n"
        f"🔎 Buscando jogos..."
    )

    jogos = buscar_jogos_reais()

    if not jogos:

        enviar_telegram(
            "⚠️ Nenhum jogo encontrado hoje."
        )

        return

    palpites = []

    for jogo in jogos:

        resultado = filtrar_jogo(jogo)

        if resultado:

            palpites.append(resultado)

    msg = (
        f"🎯 <b>PALPITES DO DIA</b>\n"
        f"📅 {agora.strftime('%d/%m/%Y')}\n\n"
    )

    for p in palpites[:5]:

        msg += (
            f"⚽ <b>{p['jogo']}</b>\n"
            f"🏆 {p['liga']}\n"
            f"🔥 {p['palpite']}\n"
            f"⭐ Confiança: {p['confianca']}/9\n\n"
        )

    enviar_telegram(msg)

    print("Finalizado.")


# ========================================
# START
# ========================================
if __name__ == "__main__":

    executar()

    time.sleep(5)

    sys.exit(0)
