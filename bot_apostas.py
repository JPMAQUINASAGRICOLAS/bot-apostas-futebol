import requests
import time
import datetime
import pytz

# ========================================
# CONFIGURAÇÕES
# ========================================

TELEGRAM_TOKEN = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
TELEGRAM_CHAT_ID = "6056076499"
API_KEY = "1a185fa6bcccfcada90c54b747eb1172"

URL_FIXTURES = "https://v3.football.api-sports.io/fixtures"
URL_TEAMS = "https://v3.football.api-sports.io/teams/statistics"

HEADERS = {
    "x-apisports-key": API_KEY
}

FUSO = pytz.timezone("America/Sao_Paulo")

HORARIOS_ENVIO = [9, 12, 15]

# ligas confiáveis
LIGAS_PERMITIDAS = [
    39,   # Premier League
    140,  # La Liga
    78,   # Bundesliga
    135,  # Serie A
    61,   # Ligue 1
    71,   # Brasileirão
    253,  # MLS
    307,  # Saudi
    2     # Champions
]

# ========================================
# TELEGRAM
# ========================================

def enviar_telegram(msg):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass


# ========================================
# BUSCAR JOGOS
# ========================================

def buscar_jogos():

    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")

    params = {
        "date": hoje
    }

    r = requests.get(URL_FIXTURES, headers=HEADERS, params=params)

    data = r.json()

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


# ========================================
# BUSCAR ESTATÍSTICAS
# ========================================

def get_stats(team_id, league_id):

    params = {
        "team": team_id,
        "league": league_id,
        "season": 2024
    }

    r = requests.get(URL_TEAMS, headers=HEADERS, params=params)

    data = r.json()["response"]

    jogos = data["fixtures"]["played"]["total"]

    if jogos == 0:
        return None

    gols_feitos = data["goals"]["for"]["total"]["total"]
    gols_sofridos = data["goals"]["against"]["total"]["total"]

    media_feitos = gols_feitos / jogos
    media_sofridos = gols_sofridos / jogos

    over15 = float(data["fixtures"]["over"]["1.5"]["percentage"].replace("%", ""))
    btts = float(data["fixtures"]["both_teams_score"]["percentage"].replace("%", ""))

    strength = media_feitos - media_sofridos

    return {

        "scored": media_feitos,
        "conceded": media_sofridos,
        "over15": over15,
        "btts": btts,
        "strength": strength

    }


# ========================================
# ANALISE PROFISSIONAL
# ========================================

def analisar_jogo(jogo):

    home = get_stats(jogo["home_id"], jogo["liga_id"])
    away = get_stats(jogo["away_id"], jogo["liga_id"])

    if home is None or away is None:
        return None


    goal_expectancy = (
        home["scored"] +
        home["conceded"] +
        away["scored"] +
        away["conceded"]
    ) / 4


    # classificar jogo
    if goal_expectancy >= 2.7:
        game_type = "ABERTO"

    elif goal_expectancy >= 2.2:
        game_type = "MEDIO"

    else:
        game_type = "FECHADO"


    # filtros
    allow_over15 = (
        home["over15"] >= 70 and
        away["over15"] >= 70
    )

    allow_btts = (
        home["btts"] >= 60 and
        away["btts"] >= 60 and
        game_type != "FECHADO"
    )

    strength_diff = away["strength"] - home["strength"]

    allow_dnb = abs(strength_diff) >= 0.40


    # decisão
    if allow_over15:

        pick = "Over 1.5 gols"

    elif allow_btts:

        pick = "Ambas marcam"

    elif allow_dnb:

        if strength_diff > 0:
            pick = f"{jogo['away']} DNB"
        else:
            pick = f"{jogo['home']} DNB"

    else:
        return None


    # confiança
    confidence = 0

    if game_type == "ABERTO":
        confidence += 2

    if allow_over15:
        confidence += 2

    if allow_btts:
        confidence += 2

    if allow_dnb:
        confidence += 1

    if goal_expectancy >= 2.5:
        confidence += 2


    if confidence < 5:
        return None


    return {

        "jogo": f"{jogo['home']} x {jogo['away']}",

        "liga": jogo["liga"],

        "tipo": game_type,

        "palpite": pick,

        "confianca": confidence

    }


# ========================================
# GERAR PALPITES
# ========================================

def gerar_palpites():

    enviar_telegram("🤖 Analisando jogos...")

    jogos = buscar_jogos()

    palpites = []

    for jogo in jogos:

        try:

            analise = analisar_jogo(jogo)

            if analise is not None:
                palpites.append(analise)

        except:
            continue


    palpites.sort(
        key=lambda x: x["confianca"],
        reverse=True
    )

    return palpites[:5]


# ========================================
# MENSAGEM
# ========================================

def montar_msg(palpites):

    if not palpites:
        return "❌ Nenhuma aposta de valor encontrada hoje"

    msg = "🎯 <b>TOP PALPITES DO DIA</b>\n\n"

    for p in palpites:

        msg += (
            f"<b>{p['jogo']}</b>\n"
            f"Liga: {p['liga']}\n"
            f"Tipo: {p['tipo']}\n"
            f"Mercado: {p['palpite']}\n"
            f"Confiança: {p['confianca']}/9\n\n"
        )

    msg += "🧠 Sistema Profissional"

    return msg


# ========================================
# LOOP PRINCIPAL
# ========================================

print("🚀 BOT INICIADO")

enviados_hoje = {}

while True:

    agora = datetime.datetime.now(FUSO)

    hora = agora.hour
    data = str(agora.date())

    chave = f"{data}-{hora}"

    if hora in HORARIOS_ENVIO and chave not in enviados_hoje:

        print("📊 Gerando palpites...")

        palpites = gerar_palpites()

        msg = montar_msg(palpites)

        enviar_telegram(msg)

        enviados_hoje[chave] = True

        print("✅ Enviado")

    time.sleep(60)
