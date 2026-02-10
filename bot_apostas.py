import requests
from datetime import datetime, timezone
import time

# ================= CONFIGURAÇÕES =================

API_KEY = "00d029285824c51ddb3978a54485b996"
BASE_URL = "https://v3.football.api-sports.io"

TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

HEADERS = {"x-apisports-key": API_KEY}

# LIGAS PRINCIPAIS
LIGAS_PERMITIDAS = [
    "Bundesliga",
    "Premier League",
    "Serie A",
    "La Liga",
    "Ligue 1",
    "Super Lig",
    "Premiership",
    "Super League",
    "Superliga",
    "Brasileirao"
]

# ================= TELEGRAM =================

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, json=payload)

# ================= API =================

def jogos_do_dia():
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    r = requests.get(
        f"{BASE_URL}/fixtures",
        headers=HEADERS,
        params={"date": hoje, "status": "NS"}
    )
    if r.status_code != 200:
        print("Erro API:", r.status_code)
        return []
    return r.json().get("response", [])

def ultimos_jogos(time_id):
    r = requests.get(
        f"{BASE_URL}/fixtures",
        headers=HEADERS,
        params={"team": time_id, "last": 5}
    )
    if r.status_code != 200:
        return []
    return r.json().get("response", [])

# ================= ANÁLISE =================

def analisar_time(jogos):
    v = e = d = gf = gs = 0
    for j in jogos:
        home = j["teams"]["home"]["winner"]
        away = j["teams"]["away"]["winner"]

        if home is True or away is True:
            v += 1
        elif home is None:
            e += 1
        else:
            d += 1

        gf += j["goals"]["home"] or 0
        gf += j["goals"]["away"] or 0

    return {
        "v": v,
        "e": e,
        "d": d,
        "gols": gf
    }

def gerar_entradas(dados_casa, dados_fora):
    entradas = []

    # Entrada 1 – Favorito / Dupla Chance
    if dados_casa["v"] >= 3 and dados_fora["d"] >= 3:
        entradas.append(("Casa vence", 85))

    # Entrada 2 – Over 1.5
    if dados_casa["gols"] + dados_fora["gols"] >= 10:
        entradas.append(("Over 1.5 gols", 80))

    # Entrada 3 – Under 3.5
    if dados_casa["gols"] + dados_fora["gols"] <= 8:
        entradas.append(("Under 3.5 gols", 78))

    return entradas[:3]

# ================= BOT =================

def main():
    print("🤖 BOT INICIADO")
    jogos = jogos_do_dia()
    enviados = 0

    for jogo in jogos:
        liga = jogo["league"]["name"]

        if not any(l.lower() in liga.lower() for l in LIGAS_PERMITIDAS):
            continue

        casa = jogo["teams"]["home"]
        fora = jogo["teams"]["away"]

        ult_casa = ultimos_jogos(casa["id"])
        ult_fora = ultimos_jogos(fora["id"])

        if not ult_casa or not ult_fora:
            continue

        dados_casa = analisar_time(ult_casa)
        dados_fora = analisar_time(ult_fora)

        entradas = gerar_entradas(dados_casa, dados_fora)
        if not entradas:
            continue

        msg = f"⚽ {casa['name']} x {fora['name']}\n"
        msg += f"🏆 {liga}\n"
        msg += f"📊 Forma casa: {dados_casa['v']}V\n"
        msg += f"📊 Forma fora: {dados_fora['v']}V\n\n"

        for i, e in enumerate(entradas, start=1):
            msg += f"🎯 Top {i}: {e[0]} ({e[1]}%)\n"

        msg += "\n🔒 Entrada mais segura do jogo"

        enviar_telegram(msg)
        enviados += 1
        time.sleep(2)

        if enviados >= 5:
            break

    print("✅ Análise finalizada")

# ================= EXECUÇÃO =================

if __name__ == "__main__":
    main()
