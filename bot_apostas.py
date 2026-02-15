import requests
from datetime import datetime, timezone
import time
import json
import os

# ================= CONFIG =================

API_KEY = "00d029285824c51ddb3978a54485b996"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

ARQUIVO_ENVIADOS = "jogos_enviados.json"

LIGAS_PERMITIDAS = [
    "Brazil",
    "Serie A",
    "Premier League",
    "La Liga",
    "Bundesliga",
    "Ligue 1",
    "Champions League",
    "Europa League"
]

# ================= TELEGRAM =================

def enviar_telegram(msg):

    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": msg
    }

    try:
        requests.post(url, json=payload, timeout=10)
        print("📩 Enviado Telegram")
    except Exception as e:
        print("Erro Telegram:", e)


# ================= CONTROLE =================

def carregar_enviados():

    if not os.path.exists(ARQUIVO_ENVIADOS):
        return []

    with open(ARQUIVO_ENVIADOS, "r") as f:
        return json.load(f)


def salvar_enviados(lista):

    with open(ARQUIVO_ENVIADOS, "w") as f:
        json.dump(lista, f)


# ================= API =================

def buscar_jogos_hoje():

    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    url = f"{BASE_URL}/fixtures"

    params = {
        "date": hoje
    }

    r = requests.get(url, headers=HEADERS, params=params)

    if r.status_code != 200:
        print("Erro API:", r.status_code)
        return []

    return r.json()["response"]


def buscar_ultimos_jogos(team_id):

    url = f"{BASE_URL}/fixtures"

    params = {
        "team": team_id,
        "last": 5
    }

    r = requests.get(url, headers=HEADERS, params=params)

    if r.status_code != 200:
        return []

    return r.json()["response"]


# ================= ANALISE =================

def analisar_time(jogos, team_id):

    v = e = d = 0
    gols_marcados = 0
    gols_sofridos = 0

    for j in jogos:

        home_id = j["teams"]["home"]["id"]
        away_id = j["teams"]["away"]["id"]

        gols_home = j["goals"]["home"] or 0
        gols_away = j["goals"]["away"] or 0

        if team_id == home_id:

            gols_marcados += gols_home
            gols_sofridos += gols_away

            if gols_home > gols_away:
                v += 1
            elif gols_home < gols_away:
                d += 1
            else:
                e += 1

        else:

            gols_marcados += gols_away
            gols_sofridos += gols_home

            if gols_away > gols_home:
                v += 1
            elif gols_away < gols_home:
                d += 1
            else:
                e += 1

    total = len(jogos)

    if total == 0:
        return None

    return {
        "vitorias": v,
        "empates": e,
        "derrotas": d,
        "media_marcados": gols_marcados / total,
        "media_sofridos": gols_sofridos / total
    }


# ================= SCORE =================

def calcular_score(casa, fora):

    score = 0
    sinais = []

    # favorito casa
    if casa["vitorias"] >= 3:
        score += 30
        sinais.append("Casa vence")

    # over gols
    media_total = casa["media_marcados"] + fora["media_marcados"]

    if media_total >= 2.5:
        score += 30
        sinais.append("Over 1.5 gols")

    if media_total >= 3.5:
        score += 20
        sinais.append("Over 2.5 gols")

    # defesa forte
    if casa["media_sofridos"] <= 1:
        score += 20

    return score, sinais


# ================= BOT =================

def analisar_dia():

    enviados = carregar_enviados()

    jogos = buscar_jogos_hoje()

    print(f"📊 Jogos encontrados hoje: {len(jogos)}")

    melhores = []

    for jogo in jogos:

        fixture_id = jogo["fixture"]["id"]

        if fixture_id in enviados:
            continue

        liga = jogo["league"]["name"]

        if not any(l.lower() in liga.lower() for l in LIGAS_PERMITIDAS):
            continue

        casa = jogo["teams"]["home"]
        fora = jogo["teams"]["away"]

        ult_casa = buscar_ultimos_jogos(casa["id"])
        ult_fora = buscar_ultimos_jogos(fora["id"])

        if not ult_casa or not ult_fora:
            continue

        dados_casa = analisar_time(ult_casa, casa["id"])
        dados_fora = analisar_time(ult_fora, fora["id"])

        if not dados_casa or not dados_fora:
            continue

        score, sinais = calcular_score(dados_casa, dados_fora)

        if score < 60:
            continue

        melhores.append({
            "fixture": fixture_id,
            "casa": casa["name"],
            "fora": fora["name"],
            "liga": liga,
            "score": score,
            "sinais": sinais
        })


    melhores.sort(key=lambda x: x["score"], reverse=True)

    print(f"🔥 Jogos qualificados: {len(melhores)}")

    for jogo in melhores[:10]:

        msg = f"""
⚽ {jogo['casa']} x {jogo['fora']}
🏆 {jogo['liga']}
🔥 CONFIANÇA: {jogo['score']}%

🎯 Sinais:
"""

        for s in jogo["sinais"]:
            msg += f"• {s}\n"

        msg += "\n🤖 Bot Profissional"

        enviar_telegram(msg)

        enviados.append(jogo["fixture"])

        salvar_enviados(enviados)

        time.sleep(3)


# ================= START =================

def main():

    print("🤖 BOT PROFISSIONAL INICIADO")

    enviar_telegram("🤖 Bot profissional ONLINE")

    while True:

        try:

            analisar_dia()

            print("⏱ Nova análise em 10 minutos")

            time.sleep(600)

        except Exception as e:

            print("Erro:", e)

            time.sleep(60)


if __name__ == "__main__":
    main()
