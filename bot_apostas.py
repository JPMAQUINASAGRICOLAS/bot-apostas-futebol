import time
import requests
import datetime
import pytz

print("🚀 BOT INICIANDO...")

# =============================
# CONFIGURAÇÕES
# =============================

TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"
API_TOKEN = "63f7daeeecc84264992bd70d5d911610"

HEADERS = {
    "X-Auth-Token": API_TOKEN
}

FUSO = pytz.timezone("America/Sao_Paulo")

# =============================
# TELEGRAM
# =============================

def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"

        r = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=15
        )

        print("📨 Status do Telegram:", r.status_code)

    except Exception as e:
        print("❌ Erro Telegram:", e)


# =============================
# BUSCAR JOGOS AGENDADOS
# =============================

def buscar_jogos():

    url = "https://api.football-data.org/v4/matches?status=SCHEDULED"

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)

        print("🌐 Status da API:", r.status_code)

        if r.status_code != 200:
            print("Erro API:", r.text)
            return []

        data = r.json()
        jogos = data.get("matches", [])

        print("⚽ Jogos encontrados:", len(jogos))

        lista = []

        for jogo in jogos[:10]:

            casa = jogo["homeTeam"]["name"]
            fora = jogo["awayTeam"]["name"]
            liga = jogo["competition"]["name"]

            lista.append({
                "casa": casa,
                "fora": fora,
                "liga": liga
            })

        return lista

    except Exception as e:
        print("❌ Erro ao buscar jogos:", e)
        return []


# =============================
# GERAR PALPITES
# =============================

def gerar_palpites(jogos):

    palpites = []

    for j in jogos:

        texto = (
            f"⚽ {j['casa']} x {j['fora']}\n"
            f"🏆 {j['liga']}\n"
            f"🎯 Palpite: Over 1.5 gols\n"
            f"🔥 Confiança: 8/10\n"
        )

        palpites.append(texto)

    return palpites


# =============================
# EXECUÇÃO
# =============================

def executar():

    agora = datetime.datetime.now(FUSO).strftime("%H:%M")

    print("⏰ Executando:", agora)

    jogos = buscar_jogos()

    if not jogos:
        enviar_telegram("⚠️ Nenhum jogo agendado encontrado.")
        return

    palpites = gerar_palpites(jogos)

    mensagem = f"🎯 PALPITES ATUALIZADOS ({agora})\n\n"

    for p in palpites:
        mensagem += p + "\n"

    enviar_telegram(mensagem)


# =============================
# LOOP CONTÍNUO
# =============================

print("✅ BOT ONLINE")

enviar_telegram("🚀 Bot iniciado com sucesso.")

while True:

    executar()

    print("⏳ Aguardando 10 minutos...")

    time.sleep(600)
