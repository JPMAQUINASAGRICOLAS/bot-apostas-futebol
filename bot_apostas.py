import requests
import datetime
import pytz
import time

# =========================
# CONFIGURAÇÃO
# =========================
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"
FOOTBALL_API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
FUSO = pytz.timezone("America/Sao_Paulo")

# =========================
# FUNÇÃO PARA ENVIAR TELEGRAM
# =========================
def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"Status Telegram: {r.status_code}")
        return r.status_code
    except Exception as e:
        print(f"Erro Telegram: {e}")
        return None

# =========================
# FUNÇÃO PARA PEGAR JOGOS DO DIA
# =========================
def pegar_jogos_do_dia():
    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")
    url = f"https://api.football-data.org/v4/matches?dateFrom={hoje}&dateTo={hoje}"
    headers = {"X-Auth-Token": FOOTBALL_API_TOKEN}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        jogos = []
        for m in data.get("matches", []):
            jogos.append({
                "home": m["homeTeam"]["name"],
                "away": m["awayTeam"]["name"],
                "liga": m["competition"]["name"],
                "status": m["status"]
            })
        return jogos
    except Exception as e:
        print(f"Erro na captura: {e}")
        return []

# =========================
# FUNÇÃO DE ANÁLISE DE JOGOS
# =========================
def analisar_jogo(jogo):
    import random
    confianca = random.randint(7, 9)  # confiança fictícia
    # Estrategia simples de palpite:
    if jogo["home"] in ["Milan", "Barcelona", "Liverpool", "Real Madrid", "PSG"]:
        palpite = f"{jogo['home']} vitória ou +1,5 gols"
    elif jogo["away"] in ["Inter", "Atletico Bilbao", "Man City", "Bayern Munique"]:
        palpite = f"{jogo['away']} vitória ou +1,5 gols"
    else:
        palpite = "Over 1.5 gols"
    return {
        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
        "palpite": palpite,
        "confianca": confianca
    }

# =========================
# EXECUÇÃO PRINCIPAL
# =========================
def executar():
    agora = datetime.datetime.now(FUSO)
    hora_msg = agora.strftime('%H:%M')
    enviar_telegram(f"🚀 <b>Bot Extreme Online!</b> Analisando jogos do dia ({hora_msg})...")

    jogos = pegar_jogos_do_dia()
    if not jogos:
        enviar_telegram("⚠️ Nenhum jogo agendado para hoje.")
        return

    # Selecionar até 5 jogos
    jogos = jogos[:5]

    palpites = []
    for j in jogos:
        palpites.append(analisar_jogo(j))

    # Montar a mensagem
    msg = f"🎯 <b>PALPITES DO DIA - {hora_msg}</b>\n\n"
    for p in palpites:
        msg += (
            f"⚽ <b>{p['jogo']}</b>\n"
            f"🏆 {p['liga']}\n"
            f"🎯 Palpite: {p['palpite']}\n"
            f"🔥 Confiança: {p['confianca']}/10\n\n"
        )
    enviar_telegram(msg)
    print("✅ Bot finalizado!")

if __name__ == "__main__":
    executar()
