import requests
import time
import datetime
import pytz

# ========================================
# CONFIGURAÇÕES
# ========================================

API_KEY = "SUA_API_AQUI"
TOKEN_TELEGRAM = "SEU_TOKEN_AQUI"
CHAT_ID = "SEU_CHAT_ID_AQUI"

URL_FIXTURES = "https://v3.football.api-sports.io/fixtures"
URL_TEAMS = "https://v3.football.api-sports.io/teams/statistics"
URL_ODDS = "https://v3.football.api-sports.io/odds"

HEADERS = {"x-apisports-key": API_KEY}

session = requests.Session()
session.headers.update(HEADERS)

FUSO = pytz.timezone("America/Sao_Paulo")

HORARIOS_ENVIO = [0, 8, 12, 15]

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
# BUSCAR ODDS
# ========================================

def get_odds(fixture_id):
    try:
        r = session.get(URL_ODDS, params={"fixture": fixture_id}, timeout=10)
        data = r.json().get("response", [])
        if not data:
            return None

        bookmakers = data[0]["bookmakers"]

        odds = {"over15": 0, "btts": 0, "dnb": 0}

        for book in bookmakers:
            for bet in book["bets"]:
                if bet["name"] == "Goals Over/Under":
                    for v in bet["values"]:
                        if v["value"] == "Over 1.5":
                            odds["over15"] = float(v["odd"])

                if bet["name"] == "Both Teams To Score":
                    for v in bet["values"]:
                        if v["value"] == "Yes":
                            odds["btts"] = float(v["odd"])

                if bet["name"] == "Draw No Bet":
                    values = bet["values"]
                    odds["dnb"] = max(float(values[0]["odd"]), float(values[1]["odd"]))

        return odds
    except:
        return None

# ========================================
# BUSCAR JOGOS
# ========================================

def buscar_jogos():
    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")
    r = session.get(URL_FIXTURES, params={"date": hoje}, timeout=15)
    data = r.json().get("response", [])

    jogos = []

    for jogo in data:
        status = jogo["fixture"]["status"]["short"]

        if status not in ["NS", "TBD"]:
            continue

        fixture_id = jogo["fixture"]["id"]
        odds = get_odds(fixture_id)

        if not odds:
            continue

        jogos.append({
            "fixture_id": fixture_id,
            "home": jogo["teams"]["home"]["name"],
            "away": jogo["teams"]["away"]["name"],
            "home_id": jogo["teams"]["home"]["id"],
            "away_id": jogo["teams"]["away"]["id"],
            "liga": jogo["league"]["name"],
            "liga_id": jogo["league"]["id"],
            "odds": odds
        })

    print(f"✅ Jogos encontrados hoje: {len(jogos)}")
    return jogos

# ========================================
# STATS
# ========================================

def get_stats(team_id, league_id):
    chave = f"{team_id}-{league_id}"
    if chave in stats_cache:
        return stats_cache[chave]

    season = datetime.datetime.now().year
    r = session.get(URL_TEAMS, params={
        "team": team_id,
        "league": league_id,
        "season": season
    }, timeout=15)

    data = r.json().get("response", {})

    try:
        jogos = data["fixtures"]["played"]["total"]
        if jogos == 0:
            return None

        stats = {
            "scored": data["goals"]["for"]["total"]["total"] / jogos,
            "conceded": data["goals"]["against"]["total"]["total"] / jogos,
            "over15": float(data["fixtures"]["over"]["1.5"]["percentage"].replace("%","")),
            "btts": float(data["fixtures"]["both_teams_score"]["percentage"].replace("%","")),
            "strength": (
                data["goals"]["for"]["total"]["total"] -
                data["goals"]["against"]["total"]["total"]
            ) / jogos
        }

        stats_cache[chave] = stats
        return stats
    except:
        return None

# ========================================
# FILTRO
# ========================================

def analisar_jogo(jogo):
    home = get_stats(jogo["home_id"], jogo["liga_id"])
    away = get_stats(jogo["away_id"], jogo["liga_id"])

    if not home or not away:
        return None

    odds = jogo["odds"]
    confidence = 0

    goal_expectancy = (home["scored"] + away["scored"] +
                       home["conceded"] + away["conceded"]) / 4

    if goal_expectancy >= 2.3:
        confidence += 1

    if (home["over15"] + away["over15"]) / 2 >= 60 and odds["over15"] >= 1.30:
        confidence += 2
        pick = "Over 1.5 gols"

    elif (home["btts"] + away["btts"]) / 2 >= 55 and odds["btts"] >= 1.55:
        confidence += 2
        pick = "Ambas marcam"

    else:
        return None

    if confidence < 3:
        return None

    return {
        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
        "palpite": pick,
        "conf": confidence
    }

# ========================================
# GERAR PALPITES
# ========================================

def gerar_palpites():
    jogos = buscar_jogos()
    palpites = []

    for j in jogos:
        resultado = analisar_jogo(j)
        if resultado:
            palpites.append(resultado)

    return sorted(palpites, key=lambda x: x["conf"], reverse=True)[:5]

# ========================================
# MENSAGEM
# ========================================

def montar_msg(palpites):
    if not palpites:
        return "❌ Nenhuma aposta encontrada hoje"

    msg = "🎯 <b>TOP PALPITES DO DIA</b>\n\n"
    for p in palpites:
        msg += f"<b>{p['jogo']}</b>\nLiga: {p['liga']}\nMercado: {p['palpite']}\nConfiança: {p['conf']}/5\n\n"

    return msg

# ========================================
# LOOP
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
        print("ENVIADO")

    time.sleep(30)
