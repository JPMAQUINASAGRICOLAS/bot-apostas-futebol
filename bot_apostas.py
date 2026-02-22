import requests
import datetime
import pytz
import time

# ==============================
# CONFIGURAÇÕES
# ==============================
API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"
HEADERS = {"X-Auth-Token": API_TOKEN, "User-Agent": "Mozilla/5.0"}
FUSO = pytz.timezone("America/Sao_Paulo")

# Horários de envio
HORARIOS = ["00:00", "08:00", "16:11"]

# ==============================
# FUNÇÃO DE ENVIO TELEGRAM
# ==============================
def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"📨 Status Telegram: {r.status_code}")
        return r.status_code
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")
        return None

# ==============================
# CAPTURA DE JOGOS DO DIA
# ==============================
def buscar_jogos_reais():
    url = "https://api.football-data.org/v4/matches?dateFrom={today}&dateTo={today}".format(
        today=datetime.datetime.now(FUSO).strftime("%Y-%m-%d")
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"❌ Erro API: {r.status_code}")
            return []

        data = r.json()
        jogos_brutos = data.get("matches", [])
        print(f"🌐 Total de jogos recebidos da API: {len(jogos_brutos)}")

        lista_final = []
        for m in jogos_brutos:
            # Filtra jogos que ainda não começaram ou agendados
            if m["status"] in ["SCHEDULED", "TIMED"]:
                lista_final.append({
                    "home": m["homeTeam"]["shortName"] or m["homeTeam"]["name"],
                    "away": m["awayTeam"]["shortName"] or m["awayTeam"]["name"],
                    "liga": m["competition"]["name"],
                    "home_strength": m.get("homeTeam", {}).get("strength", 1.0),
                    "away_strength": m.get("awayTeam", {}).get("strength", 1.0)
                })
        print(f"⚽ Jogos filtrados (agendados/temporários): {len(lista_final)}")
        return lista_final

    except Exception as e:
        print(f"❌ Erro na captura: {e}")
        return []

# ==============================
# FUNÇÃO DE ANÁLISE AVANÇADA
# ==============================
def analisar_jogo(jogo):
    """
    Retorna o melhor palpite possível:
    - Vitória / Empate / +1,5 gols / -3,5 gols
    Baseado em força do time (home_strength vs away_strength) e histórico simples
    """
    home = jogo["home"]
    away = jogo["away"]

    home_adv = jogo["home_strength"]
    away_adv = jogo["away_strength"]

    # Simples heurística de análise:
    diff = home_adv - away_adv
    pick = ""
    confianca = 0

    if diff > 0.25:
        pick = f"Vitória {home}"
        confianca = 9
    elif diff < -0.25:
        pick = f"Vitória {away}"
        confianca = 9
    elif abs(diff) <= 0.25:
        pick = "+1,5 gols"
        confianca = 8

    return {
        "jogo": f"{home} x {away}",
        "liga": jogo["liga"],
        "palpite": pick,
        "confianca": confianca
    }

# ==============================
# EXECUÇÃO PRINCIPAL
# ==============================
def executar():
    agora = datetime.datetime.now(FUSO)
    hora_msg = agora.strftime('%H:%M')

    if hora_msg not in HORARIOS:
        print(f"⏳ Não é horário de envio: {hora_msg}")
        return

    print(f"[{hora_msg}] 🚀 Bot Extreme Online! Analisando jogos do dia...")

    enviar_telegram(f"🚀 <b>Bot Extreme Online!</b> Analisando jogos do dia ({hora_msg})...")

    jogos = buscar_jogos_reais()

    if not jogos:
        enviar_telegram(f"⚠️ Nenhum jogo agendado para hoje ({hora_msg}).")
        print("⚠️ Nenhum jogo hoje")
        return

    # Analisa os jogos
    palpites = []
    for j in jogos:
        res = analisar_jogo(j)
        if res:
            palpites.append(res)

    # Seleciona até 5 melhores jogos
    palpites = sorted(palpites, key=lambda x: x["confianca"], reverse=True)[:5]

    # Monta a mensagem
    msg = f"🎯 <b>PALPITES EXTREMOS - {hora_msg}</b>\n\n"
    for p in palpites:
        msg += (
            f"⚽ <b>{p['jogo']}</b>\n"
            f"🏆 {p['liga']}\n"
            f"🎯 Palpite: {p['palpite']}\n"
            f"🔥 Confiança: {p['confianca']}/10\n\n"
        )
    msg += "🧠 <i>Análise avançada via Football-Data</i>"

    enviar_telegram(msg)
    print("✅ Bot finalizado!")

# ==============================
# LOOP DE HORÁRIOS
# ==============================
if __name__ == "__main__":
    executar()
