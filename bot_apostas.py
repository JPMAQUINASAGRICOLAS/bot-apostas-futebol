import requests
import time
from datetime import datetime
import pytz

# =========================
# CONFIG
# =========================

TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"
API_TOKEN = "63f7daeeecc84264992bd70d5d911610"

HEADERS = {"X-Auth-Token": API_KEY}
FUSO = pytz.timezone("America/Sao_Paulo")

HORARIOS_ENVIO = ["00:00", "01:45", "15:00"]
ultimo_envio = None

# =========================
# TELEGRAM
# =========================

def enviar(msg):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

# =========================
# BUSCAR JOGOS DO DIA
# =========================

def buscar_jogos():
    hoje = datetime.now(FUSO).date()
    url = f"https://api.football-data.org/v4/matches?dateFrom={hoje}&dateTo={hoje}"

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return []

    return r.json()["matches"]

# =========================
# ESTATISTICAS TIME
# =========================

def stats_time(team_id):

    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?limit=10"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return None

    jogos = r.json()["matches"]

    gols = 0
    sofridos = 0
    over25 = 0
    btts = 0
    total = 0

    for j in jogos:

        if j["score"]["fullTime"]["home"] is None:
            continue

        home = j["score"]["fullTime"]["home"]
        away = j["score"]["fullTime"]["away"]

        if j["homeTeam"]["id"] == team_id:
            feitos = home
            contra = away
        else:
            feitos = away
            contra = home

        gols += feitos
        sofridos += contra

        if home + away >= 3:
            over25 += 1

        if home > 0 and away > 0:
            btts += 1

        total += 1

    if total == 0:
        return None

    return {
        "media_gols": gols / total,
        "media_sofridos": sofridos / total,
        "taxa_over25": over25 / total,
        "taxa_btts": btts / total
    }

# =========================
# ANALISE EXTREMA
# =========================

def analisar(jogo):

    casa_id = jogo["homeTeam"]["id"]
    fora_id = jogo["awayTeam"]["id"]

    stats_casa = stats_time(casa_id)
    stats_fora = stats_time(fora_id)

    if not stats_casa or not stats_fora:
        return None

    media_total = stats_casa["media_gols"] + stats_fora["media_gols"]
    over_score = (stats_casa["taxa_over25"] + stats_fora["taxa_over25"]) / 2
    btts_score = (stats_casa["taxa_btts"] + stats_fora["taxa_btts"]) / 2

    if over_score >= 0.7 and media_total >= 3:
        return "Over 2.5 gols", 9

    if btts_score >= 0.65:
        return "BTTS (Ambos marcam)", 8

    if media_total >= 2:
        return "Over 1.5 gols", 8

    if stats_casa["media_gols"] > stats_fora["media_gols"]:
        return "Vitória do mandante", 7

    return None

# =========================
# EXECUTAR ANALISE
# =========================

def executar():

    agora = datetime.now(FUSO)
    hora_atual = agora.strftime("%H:%M")

    global ultimo_envio

    if hora_atual not in HORARIOS_ENVIO:
        return

    if ultimo_envio == hora_atual:
        return

    jogos = buscar_jogos()

    if not jogos:
        enviar("⚠️ Nenhum jogo hoje.")
        return

    mensagem = f"🔥 PALPITES EXTREMOS ({hora_atual})\n\n"

    enviados = 0

    for j in jogos:

        resultado = analisar(j)

        if not resultado:
            continue

        mercado, confianca = resultado

        if confianca >= 7:

            mensagem += (
                f"⚽ {j['homeTeam']['name']} x {j['awayTeam']['name']}\n"
                f"🏆 {j['competition']['name']}\n"
                f"🎯 {mercado}\n"
                f"🔥 Confiança: {confianca}/10\n\n"
            )

            enviados += 1

        if enviados >= 5:
            break

    enviar(mensagem)
    ultimo_envio = hora_atual

# =========================
# LOOP
# =========================

print("BOT EXTREMO COM HORARIO INICIADO")

while True:
    executar()
    time.sleep(30)
