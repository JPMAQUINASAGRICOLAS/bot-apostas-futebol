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

# Analisa todo horário (recomendado)
HORARIOS_ENVIO = list(range(24))

# Ligas confiáveis
LIGAS_PERMITIDAS = [
    39,   # Premier League
    140,  # La Liga
    78,   # Bundesliga
    135,  # Serie A
    61,   # Ligue 1
    71,   # Brasileirão
    253,  # MLS
    307,  # Saudi League
    2     # Champions League
]

stats_cache = {}

# ========================================
# TELEGRAM
# ========================================

def enviar_telegram(msg):

    try:

        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"

        payload = {
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }

        requests.post(url, json=payload, timeout=10)

    except Exception as e:

        print("Erro Telegram:", e)


# ========================================
# BUSCAR TODAS ODDS DO DIA
# ========================================

def buscar_odds_dia():

    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")

    try:

        r = session.get(URL_ODDS, params={"date": hoje}, timeout=20)

        data = r.json()["response"]

        odds_dict = {}

        for item in data:

            fixture_id = item["fixture"]["id"]

            odds = {
                "over15": 0,
                "btts": 0,
                "dnb": 0
            }

            bookmakers = item["bookmakers"]

            for book in bookmakers:

                for bet in book["bets"]:

                    if bet["name"] == "Goals Over/Under":

                        for v in bet["values"]:

                            if v["value"] == "Over 1.5":
                                odds["over15"] = float(v["odd"])

                    elif bet["name"] == "Both Teams Score":

                        for v in bet["values"]:

                            if v["value"] == "Yes":
                                odds["btts"] = float(v["odd"])

                    elif bet["name"] == "Draw No Bet":

                        values = bet["values"]

                        odds["dnb"] = max(
                            float(values[0]["odd"]),
                            float(values[1]["odd"])
                        )

            odds_dict[fixture_id] = odds

        print(f"✅ Odds carregadas: {len(odds_dict)} jogos")

        return odds_dict

    except Exception as e:

        print("Erro odds:", e)
        return {}


# ========================================
# BUSCAR JOGOS
# ========================================

def buscar_jogos():

    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")

    odds_dict = buscar_odds_dia()

    try:

        r = session.get(URL_FIXTURES, params={"date": hoje}, timeout=20)

        data = r.json()["response"]

        jogos = []

        for jogo in data:

            liga_id = jogo["league"]["id"]

            status = jogo["fixture"]["status"]["short"]

            fixture_id = jogo["fixture"]["id"]

            if liga_id not in LIGAS_PERMITIDAS:
                continue

            if status != "NS":
                continue

            if fixture_id not in odds_dict:
                continue

            jogos.append({

                "fixture_id": fixture_id,

                "home": jogo["teams"]["home"]["name"],
                "away": jogo["teams"]["away"]["name"],

                "home_id": jogo["teams"]["home"]["id"],
                "away_id": jogo["teams"]["away"]["id"],

                "liga": jogo["league"]["name"],
                "liga_id": liga_id,

                "odds": odds_dict[fixture_id]

            })

        print(f"✅ Jogos encontrados hoje: {len(jogos)}")

        for j in jogos:
            print(j["home"], "x", j["away"], "-", j["liga"])

        return jogos

    except Exception as e:

        print("Erro buscar jogos:", e)
        return []


# ========================================
# BUSCAR STATS COM CACHE
# ========================================

def get_stats(team_id, league_id):

    chave = f"{team_id}-{league_id}"

    if chave in stats_cache:
        return stats_cache[chave]

    try:

        params = {
            "team": team_id,
            "league": league_id,
            "season": datetime.datetime.now().year
        }

        r = session.get(URL_TEAMS, params=params, timeout=20)

        data = r.json()["response"]

        jogos = data["fixtures"]["played"]["total"]

        if jogos == 0:
            return None

        stats = {

            "scored": data["goals"]["for"]["total"]["total"] / jogos,

            "conceded": data["goals"]["against"]["total"]["total"] / jogos,

            "over15": float(data["fixtures"]["over"]["1.5"]["percentage"].replace("%","")),

            "btts": float(data["fixtures"]["both_teams_score"]["percentage"].replace("%","")),

            "strength": (
                data["goals"]["for"]["total"]["total"]
                -
                data["goals"]["against"]["total"]["total"]
            ) / jogos
        }

        stats_cache[chave] = stats

        return stats

    except:

        return None


# ========================================
# FILTRO PROFISSIONAL
# ========================================

def professional_match_filter(jogo):

    home = get_stats(jogo["home_id"], jogo["liga_id"])
    away = get_stats(jogo["away_id"], jogo["liga_id"])

    if not home or not away:
        return None

    odds = jogo["odds"]

    goal_expectancy = (
        home["scored"] +
        home["conceded"] +
        away["scored"] +
        away["conceded"]
    ) / 4

    confidence = 0

    if goal_expectancy >= 2.6:
        confidence += 2
        tipo = "ABERTO"
    elif goal_expectancy >= 2.2:
        confidence += 1
        tipo = "MEDIO"
    else:
        tipo = "FECHADO"

    over_strength = (home["over15"] + away["over15"]) / 2

    btts_strength = (home["btts"] + away["btts"]) / 2

    strength_diff = away["strength"] - home["strength"]

    pick = None

    if over_strength >= 65 and odds["over15"] >= 1.30:
        pick = "Over 1.5 gols"
        confidence += 2

    elif btts_strength >= 55 and odds["btts"] >= 1.55:
        pick = "Ambas marcam"
        confidence += 2

    elif abs(strength_diff) >= 0.25 and odds["dnb"] >= 1.30:

        if strength_diff > 0:
            pick = f"{jogo['away']} DNB"
        else:
            pick = f"{jogo['home']} DNB"

        confidence += 1

    if home["scored"] >= 1.5:
        confidence += 1

    if away["scored"] >= 1.5:
        confidence += 1

    if confidence < 4:
        return None

    return {

        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
        "palpite": pick,
        "tipo": tipo,
        "confianca": confidence
    }


# ========================================
# GERAR PALPITES
# ========================================

def gerar_palpites():

    enviar_telegram("🤖 Analisando jogos...")

    jogos = buscar_jogos()

    enviar_telegram(f"📊 Jogos encontrados hoje: {len(jogos)}")

    palpites = []

    for jogo in jogos:

        resultado = professional_match_filter(jogo)

        if resultado:
            palpites.append(resultado)

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
        return "❌ Nenhuma aposta encontrada hoje"

    msg = "🎯 <b>TOP PALPITES DO DIA</b>\n\n"

    for p in palpites:

        msg += (
            f"<b>{p['jogo']}</b>\n"
            f"Liga: {p['liga']}\n"
            f"Mercado: {p['palpite']}\n"
            f"Tipo: {p['tipo']}\n"
            f"Confiança: {p['confianca']}/10\n\n"
        )

    msg += "🧠 Bot Profissional"

    return msg


# ========================================
# LOOP PRINCIPAL
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

    time.sleep(60)
