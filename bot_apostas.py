import requests
from datetime import datetime, timezone
import time
import json
import os

# ================= CONFIG =================

API_KEY = "00d029285824c51ddb3978a54485b996"
BASE_URL = "https://v3.football.api-sports.io"

TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

HEADERS = {
    "x-apisports-key": API_KEY
}

ARQUIVO_JOGOS_ENVIADOS = "jogos_enviados.json"

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

    if not os.path.exists(ARQUIVO_JOGOS_ENVIADOS):
        return []

    with open(ARQUIVO_JOGOS_ENVIADOS, "r") as f:
        return json.load(f)


def salvar_enviados(lista):

    with open(ARQUIVO_JOGOS_ENVIADOS, "w") as f:
        json.dump(lista, f)

# ================= API =================

def jogos_do_dia():

    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    url = f"{BASE_URL}/fixtures"

    params = {
        "date": hoje
    }

    r = requests.get(url, headers=HEADERS, params=params)

    if r.status_code != 200:
        print("Erro API:", r.status_code)
        return []

    dados = r.json().get("response", [])

    print(f"📊 Jogos encontrados hoje: {len(dados)}")

    return dados


def ultimos_jogos(time_id):

    url = f"{BASE_URL}/fixtures"

    params = {
        "team": time_id,
        "last": 5
    }

    r = requests.get(url, headers=HEADERS, params=params)

    if r.status_code != 200:
        return []

    return r.json().get("response", [])

# ================= ANALISE =================

def analisar_time(jogos, time_id):

    v = 0
    d = 0
    e = 0

    gols_marcados = 0
    gols_sofridos = 0

    for j in jogos:

        home_id = j["teams"]["home"]["id"]
        away_id = j["teams"]["away"]["id"]

        gols_home = j["goals"]["home"] or 0
        gols_away = j["goals"]["away"] or 0

        if time_id == home_id:

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

    media_marcados = gols_marcados / total
    media_sofridos = gols_sofridos / total

    return {
        "v": v,
        "d": d,
        "e": e,
        "media_marcados": media_marcados,
        "media_sofridos": media_sofridos
    }

# ================= SCORE =================

def calcular_score(casa, fora):

    score = 0
    sinais = []

    # favorito casa
    if casa["v"] >= 3 and fora["d"] >= 3:

        score += 40
        sinais.append("Casa vence")

    # over gols
    media_total = casa["media_marcados"] + fora["media_marcados"]

    if media_total >= 2.5:

        score += 30
        sinais.append("Over 1.5 gols")

    # defesa forte casa
    if casa["media_sofridos"] <= 1:

        score += 20

    # bom ataque fora
    if fora["media_marcados"] >= 1.2:

        score += 10

    return score, sinais

# ================= BOT =================

def main():

    print("🤖 BOT PROFISSIONAL INICIADO")

    enviar_telegram("🤖 Bot profissional ONLINE e analisando jogos!")

    enviados = carregar_enviados()

    while True:

        try:

            jogos = jogos_do_dia()

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

                ult_casa = ultimos_jogos(casa["id"])
                ult_fora = ultimos_jogos(fora["id"])

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

            print(f"🔥 Jogos qualificados: {len(melhores)}")

            melhores.sort(key=lambda x: x["score"], reverse=True)

            for jogo in melhores[:5]:

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

            print("⏱ Nova análise em 10 minutos")

            time.sleep(600)

        except Exception as e:

            print("Erro:", e)

            time.sleep(60)

# ================= START =================

if __name__ == "__main__":
    main()
