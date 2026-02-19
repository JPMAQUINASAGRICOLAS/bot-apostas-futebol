import requests
import time
import datetime
import pytz

# ========================================
# CONFIGURAÇÕES
# ========================================

API_KEY = "1a185fa6bcccfcada90c54b747eb1172"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

URL_FIXTURES = "https://v3.football.api-sports.io/fixtures"
URL_TEAMS = "https://v3.football.api-sports.io/teams/statistics"
URL_ODDS = "https://v3.football.api-sports.io/odds"

HEADERS = {
    "x-apisports-key": API_KEY
}

session = requests.Session()
session.headers.update(HEADERS)

FUSO = pytz.timezone("America/Sao_Paulo")

HORARIOS_ENVIO = [9, 12, 15]

LIGAS_PERMITIDAS = [39,140,78,135,61,71,253,307,2]

stats_cache = {}

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
        requests.post(url, json=payload, timeout=10)
    except:
        pass


# ========================================
# BUSCAR ODDS REAIS
# ========================================

def get_odds(fixture_id):

    try:

        params = {"fixture": fixture_id}

        r = session.get(URL_ODDS, params=params, timeout=10)

        data = r.json()["response"]

        if not data:
            return None

        bookmakers = data[0]["bookmakers"]

        odds = {
            "over15": 0,
            "btts": 0,
            "dnb": 0
        }

        for book in bookmakers:

            for bet in book["bets"]:

                name = bet["name"]

                if name == "Goals Over/Under":

                    for value in bet["values"]:

                        if value["value"] == "Over 1.5":
                            odds["over15"] = float(value["odd"])


                if name == "Both Teams Score":

                    for value in bet["values"]:

                        if value["value"] == "Yes":
                            odds["btts"] = float(value["odd"])


                if name == "Draw No Bet":

                    values = bet["values"]

                    odds["dnb"] = max(
                        float(values[0]["odd"]),
                        float(values[1]["odd"])
                    )

        return odds

    except:

        return None


# ========================================
# BUSCAR JOGOS
# ========================================

def buscar_jogos():

    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")

    params = {"date": hoje}

    r = session.get(URL_FIXTURES, params=params, timeout=15)

    data = r.json()["response"]

    jogos = []

    for jogo in data:

        liga_id = jogo["league"]["id"]

        status = jogo["fixture"]["status"]["short"]

        if liga_id not in LIGAS_PERMITIDAS:
            continue

        if status != "NS":
            continue

        fixture_id = jogo["fixture"]["id"]

        odds = get_odds(fixture_id)

        if odds is None:
            continue

        jogos.append({

            "fixture_id": fixture_id,

            "home": jogo["teams"]["home"]["name"],
            "away": jogo["teams"]["away"]["name"],

            "home_id": jogo["teams"]["home"]["id"],
            "away_id": jogo["teams"]["away"]["id"],

            "liga": jogo["league"]["name"],
            "liga_id": liga_id,

            "odds": odds,

            "competition_ok": True
        })

    return jogos


# ========================================
# BUSCAR STATS
# ========================================

def get_stats(team_id, league_id):

    chave = f"{team_id}-{league_id}"

    if chave in stats_cache:
        return stats_cache[chave]

    params = {

        "team": team_id,
        "league": league_id,
        "season": datetime.datetime.now().year
    }

    r = session.get(URL_TEAMS, params=params, timeout=15)

    data = r.json()["response"]

    jogos = data["fixtures"]["played"]["total"]

    if jogos == 0:
        return None

    stats = {

        "scored":
        data["goals"]["for"]["total"]["total"] / jogos,

        "conceded":
        data["goals"]["against"]["total"]["total"] / jogos,

        "over15":
        float(data["fixtures"]["over"]["1.5"]["percentage"].replace("%","")),

        "btts":
        float(data["fixtures"]["both_teams_score"]["percentage"].replace("%","")),

        "strength":
        (
            data["goals"]["for"]["total"]["total"] -
            data["goals"]["against"]["total"]["total"]
        ) / jogos
    }

    stats_cache[chave] = stats

    return stats


# ========================================
# FILTRO PROFISSIONAL
# ========================================

def professional_match_filter(jogo):

    home_stats = get_stats(jogo["home_id"], jogo["liga_id"])
    away_stats = get_stats(jogo["away_id"], jogo["liga_id"])

    if not home_stats or not away_stats:
        return None


    odds = jogo["odds"]


    goal_expectancy = (

        home_stats["scored"] +
        home_stats["conceded"] +
        away_stats["scored"] +
        away_stats["conceded"]

    ) / 4


    if goal_expectancy >= 2.7:
        game_type = "ABERTO"

    elif goal_expectancy >= 2.2:
        game_type = "MEDIO"

    else:
        game_type = "FECHADO"


    allow_over15 = (

        home_stats["over15"] >= 70 and
        away_stats["over15"] >= 70 and
        odds["over15"] >= 1.35
    )


    allow_btts = (

        home_stats["btts"] >= 60 and
        away_stats["btts"] >= 60 and
        odds["btts"] >= 1.60 and
        game_type != "FECHADO"
    )


    strength_diff = (
        away_stats["strength"] -
        home_stats["strength"]
    )


    allow_dnb = (

        abs(strength_diff) >= 0.12 and
        odds["dnb"] >= 1.25
    )


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


    confidence = 0

    if game_type == "ABERTO":
        confidence += 2

    if allow_over15:
        confidence += 2

    if allow_btts:
        confidence += 2

    if abs(strength_diff) >= 0.12:
        confidence += 1

    if odds["over15"] >= 1.40:
        confidence += 2


    if confidence < 5:
        return None


    return {

        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
        "palpite": pick,
        "tipo": game_type,
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

            resultado = professional_match_filter(jogo)

            if resultado:
                palpites.append(resultado)

        except:
            pass


    palpites.sort(
        key=lambda x: x["confianca"],
        reverse=True
    )

    return palpites[:5]


# ========================================
# MONTAR MSG
# ========================================

def montar_msg(palpites):

    if not palpites:
        return "❌ Nenhuma aposta encontrada hoje"


    msg = "🎯 <b>TOP PALPITES DO DIA</b>\n\n"

    for p in palpites:

        msg += (
            f"<b>{p['jogo']}</b>\n"
            f"Liga: {p['liga']}\n"
            f"Mercado: {p['palpite']}\n"
            f"Tipo: {p['tipo']}\n"
            f"Confiança: {p['confianca']}/9\n\n"
        )

    msg += "🧠 Bot Profissional"

    return msg


# ========================================
# LOOP PRINCIPAL
# ========================================

print("BOT ONLINE")

enviados = {}

enviar_telegram("✅ BOT ONLINE")

while True:

    agora = datetime.datetime.now(FUSO)

    chave = f"{agora.date()}-{agora.hour}"

    if agora.hour in HORARIOS_ENVIO and chave not in enviados:

        palpites = gerar_palpites()

        msg = montar_msg(palpites)

        enviar_telegram(msg)

        enviados[chave] = True

        print("ENVIADO")

    time.sleep(30)
