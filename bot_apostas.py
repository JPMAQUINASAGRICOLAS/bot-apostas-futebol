import requests
import time
import datetime
import pytz
import os

# ==============================
# CONFIGURAÇÕES
# ==============================

TELEGRAM_TOKEN = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
TELEGRAM_CHAT_ID = "6056076499"
API_KEY = "1a185fa6bcccfcada90c54b747eb1172"

URL_FIXTURES = "https://v3.football.api-sports.io/fixtures"
URL_TEAMS = "https://v3.football.api-sports.io/teams/statistics"

HEADERS = {
    "x-apisports-key": API_KEY
}

FUSO = pytz.timezone("America/Sao_Paulo")

# ligas principais apenas
LIGAS_PERMITIDAS = [
    39,   # Premier League
    140,  # La Liga
    78,   # Bundesliga
    135,  # Serie A
    61,   # Ligue 1
    71,   # Brasileirão Série A
    253,  # MLS
    307,  # Saudi League
    2,    # Champions League
]

# ==============================
# TELEGRAM
# ==============================

def enviar_telegram(msg):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }

    requests.post(url, json=payload)

# ==============================
# BUSCAR JOGOS DO DIA
# ==============================

def buscar_jogos():

    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")

    params = {
        "date": hoje
    }

    response = requests.get(URL_FIXTURES, headers=HEADERS, params=params)

    data = response.json()

    jogos = []

    for jogo in data["response"]:

        liga_id = jogo["league"]["id"]

        if liga_id not in LIGAS_PERMITIDAS:
            continue

        jogos.append({
            "home": jogo["teams"]["home"]["name"],
            "away": jogo["teams"]["away"]["name"],
            "home_id": jogo["teams"]["home"]["id"],
            "away_id": jogo["teams"]["away"]["id"],
            "liga": jogo["league"]["name"],
            "liga_id": liga_id
        })

    return jogos

# ==============================
# BUSCAR ESTATÍSTICAS
# ==============================

def stats_time(team_id, liga_id):

    params = {
        "team": team_id,
        "league": liga_id,
        "season": 2024
    }

    r = requests.get(URL_TEAMS, headers=HEADERS, params=params)

    data = r.json()

    gols_feitos = data["response"]["goals"]["for"]["total"]["total"]
    gols_sofridos = data["response"]["goals"]["against"]["total"]["total"]
    jogos = data["response"]["fixtures"]["played"]["total"]

    media_feitos = gols_feitos / jogos if jogos > 0 else 0
    media_sofridos = gols_sofridos / jogos if jogos > 0 else 0

    return media_feitos, media_sofridos

# ==============================
# ANALISE INTELIGENTE
# ==============================

def analisar_jogo(jogo):

    home_for, home_against = stats_time(jogo["home_id"], jogo["liga_id"])
    away_for, away_against = stats_time(jogo["away_id"], jogo["liga_id"])

    media_total = (
        home_for + home_against +
        away_for + away_against
    ) / 2

    diferenca = abs(home_for - away_for)

    melhor = None
    confianca = 0

    # Over / Under
    if media_total >= 3.2:
        melhor = "Over 2.5 gols"
        confianca = 85 + min(media_total * 2, 10)

    elif media_total <= 2:
        melhor = "Under 3.5 gols"
        confianca = 82 + min((2 - media_total) * 5, 10)

    # ambas marcam
    elif home_for >= 1.3 and away_for >= 1.3:
        melhor = "Ambas marcam SIM"
        confianca = 80 + min(home_for + away_for, 10)

    # vitória seca
    elif diferenca >= 1.2:
        if home_for > away_for:
            melhor = f"Vitória {jogo['home']}"
        else:
            melhor = f"Vitória {jogo['away']}"

        confianca = 83 + min(diferenca * 5, 10)

    else:
        melhor = "Over 1.5 gols"
        confianca = 78

    return {
        "jogo": f"{jogo['home']} x {jogo['away']}",
        "palpite": melhor,
        "liga": jogo["liga"],
        "confianca": int(confianca)
    }

# ==============================
# GERAR TOP 5
# ==============================

def gerar_palpites():

    enviar_telegram("🤖 Analisando jogos das principais ligas...")

    jogos = buscar_jogos()

    palpites = []

    for jogo in jogos:

        try:
            analise = analisar_jogo(jogo)
            palpites.append(analise)

        except:
            continue

    palpites.sort(key=lambda x: x["confianca"], reverse=True)

    return palpites[:5]

# ==============================
# MONTAR MENSAGEM
# ==============================

def montar_msg(palpites):

    msg = "🎯 <b>TOP 5 PALPITES DO DIA</b>\n\n"

    for p in palpites:

        msg += (
            f"<b>{p['jogo']}</b>\n"
            f"Liga: {p['liga']}\n"
            f"Palpite: {p['palpite']}\n"
            f"Confiança: {p['confianca']}%\n\n"
        )

    msg += "🧠 Análise baseada em estatísticas reais"

    return msg

# ==============================
# LOOP PRINCIPAL
# ==============================

print("🚀 BOT ELITE INICIADO")

ultimo_envio = None

while True:

    agora = datetime.datetime.now(FUSO)

    if True:

        if ultimo_envio != agora.date():

            print("📊 Gerando palpites...")

            palpites = gerar_palpites()

            msg = montar_msg(palpites)

            enviar_telegram(msg)

            ultimo_envio = agora.date()

            print("✅ Palpites enviados com sucesso")

    time.sleep(30)

