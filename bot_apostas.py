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

HORARIOS_ENVIO = [0, 8, 12, 15, 18, 20]

# Ligas permitidas
LIGAS_PERMITIDAS = [
    39,   # Premier League
    140,  # La Liga
    78,   # Bundesliga
    135,  # Serie A
    61,   # Ligue 1
    71,   # Brasileirão
    94,   # Portugal
    253,  # MLS
    307,  # Saudi
    2     # Champions League
]

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
# BUSCAR JOGOS
# ========================================

def buscar_jogos():

    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")

    try:

        r = session.get(
            URL_FIXTURES,
            params={
                "date": hoje,
                "timezone": "America/Sao_Paulo"
            },
            timeout=20
        )

        data = r.json()["response"]

        print(f"TOTAL API retornou: {len(data)} jogos")

        jogos = []

        for jogo in data:

            liga_id = jogo["league"]["id"]
            status = jogo["fixture"]["status"]["short"]

            if status != "NS":
                continue

            if liga_id not in LIGAS_PERMITIDAS:
                continue

            jogos.append({

                "fixture_id": jogo["fixture"]["id"],

                "home": jogo["teams"]["home"]["name"],
                "away": jogo["teams"]["away"]["name"],

                "home_id": jogo["teams"]["home"]["id"],
                "away_id": jogo["teams"]["away"]["id"],

                "liga": jogo["league"]["name"],
                "liga_id": liga_id
            })

        print(f"✅ Jogos válidos encontrados: {len(jogos)}")

        return jogos

    except Exception as e:

        print("Erro buscar jogos:", e)
        return []


# ========================================
# BUSCAR ODDS
# ========================================

def get_odds(fixture_id):

    try:

        r = session.get(
            URL_ODDS,
            params={"fixture": fixture_id},
            timeout=15
        )

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

                if bet["name"] == "Goals Over/Under":

                    for v in bet["values"]:

                        if v["value"] == "Over 1.5":
                            odds["over15"] = float(v["odd"])


                if bet["name"] == "Both Teams Score":

                    for v in bet["values"]:

                        if v["value"] == "Yes":
                            odds["btts"] = float(v["odd"])


                if bet["name"] == "Draw No Bet":

                    odds["dnb"] = max(
                        float(bet["values"][0]["odd"]),
                        float(bet["values"][1]["odd"])
                    )

        return odds

    except:
        return None


# ========================================
# BUSCAR STATS
# ========================================

def get_stats(team_id, league_id):

    chave = f"{team_id}-{league_id}"

    if chave in stats_cache:
        return stats_cache[chave]

    try:

        r = session.get(
            URL_TEAMS,
            params={
                "team": team_id,
                "league": league_id,
                "season": datetime.datetime.now().year
            },
            timeout=15
        )

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
                data["goals"]["for"]["total"]["total"]
                - data["goals"]["against"]["total"]["total"]
            ) / jogos
        }

        stats_cache[chave] = stats

        return stats

    except:
        return None


# ========================================
# ANALISAR JOGO
# ========================================

def analisar_jogo(jogo):

    odds = get_odds(jogo["fixture_id"])

    if not odds:
        return None

    home_stats = get_stats(jogo["home_id"], jogo["liga_id"])
    away_stats = get_stats(jogo["away_id"], jogo["liga_id"])

    if not home_stats or not away_stats:
        return None

    confidence = 0

    goal_expectancy = (
        home_stats["scored"] +
        home_stats["conceded"] +
        away_stats["scored"] +
        away_stats["conceded"]
    ) / 4

    if goal_expectancy >= 2.5:
        confidence += 2

    if (home_stats["over15"] + away_stats["over15"]) / 2 >= 65:
        confidence += 2

    if (home_stats["btts"] + away_stats["btts"]) / 2 >= 55:
        confidence += 2

    if odds["over15"] >= 1.30:
        confidence += 1

    if odds["btts"] >= 1.55:
        confidence += 1

    if confidence < 4:
        return None

    if odds["over15"] >= odds["btts"]:
        pick = "Over 1.5 gols"
    else:
        pick = "Ambas marcam"

    return {

        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
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

        resultado = analisar_jogo(jogo)

        if resultado:
            palpites.append(resultado)

    palpites.sort(
        key=lambda x: x["confianca"],
        reverse=True
    )

    print(f"✅ Palpites encontrados: {len(palpites)}")

    return palpites[:5]


# ========================================
# MONTAR MSG
# ========================================

def montar_msg(palpites):

    if not palpites:
        return "❌ Nenhum palpite encontrado"

    msg = "🎯 <b>TOP PALPITES DO DIA</b>\n\n"

    for p in palpites:

        msg += (
            f"<b>{p['jogo']}</b>\n"
            f"Liga: {p['liga']}\n"
            f"Palpite: {p['palpite']}\n"
            f"Confiança: {p['confianca']}/8\n\n"
        )

    msg += "🧠 Bot Profissional"

    return msg


# ========================================
# INICIAR BOT
# ========================================

print("BOT ONLINE")

enviar_telegram("✅ BOT ONLINE")

enviados = {}

while True:

    agora = datetime.datetime.now(FUSO)

    chave = f"{agora.date()}-{agora.hour}"

    if agora.hour in HORARIOS_ENVIO and chave not in enviados:

        palpites = gerar_palpites()

        msg = montar_msg(palpites)

        enviar_telegram(msg)

        enviados[chave] = True

        print("ENVIADO", chave)

    time.sleep(30)
