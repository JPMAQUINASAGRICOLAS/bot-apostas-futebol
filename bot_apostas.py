import requests
import datetime
import pytz
import time

# ========================================
# CONFIGURAÇÕES
# ========================================
API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"
HEADERS = {"X-Auth-Token": API_TOKEN, "User-Agent": "Mozilla/5.0"}
FUSO = pytz.timezone("America/Sao_Paulo")

# ========================================
# FUNÇÃO DE ENVIO AO TELEGRAM
# ========================================
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

# ========================================
# BUSCA TODOS OS JOGOS DO DIA
# ========================================
def buscar_jogos_reais():
    hoje = datetime.datetime.now(FUSO).date()
    url = "https://api.football-data.org/v4/matches"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"Erro API: {r.status_code}")
            return []

        data = r.json()
        jogos_brutos = data.get("matches", [])
        print(f"🌐 Total de jogos recebidos da API: {len(jogos_brutos)}")

        lista_final = []
        for m in jogos_brutos:
            # Data e hora do jogo em UTC
            utc_dt = datetime.datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
            jogo_data = utc_dt.astimezone(FUSO).date()

            # Considera apenas jogos do dia
            if jogo_data == hoje and m["status"] in ["SCHEDULED", "TIMED"]:
                lista_final.append({
                    "home": m["homeTeam"]["shortName"] or m["homeTeam"]["name"],
                    "away": m["awayTeam"]["shortName"] or m["awayTeam"]["name"],
                    "liga": m["competition"]["name"],
                    "status": m["status"]
                })
        print(f"⚽ Jogos filtrados (do dia): {len(lista_final)}")
        return lista_final
    except Exception as e:
        print(f"Erro na captura: {e}")
        return []

# ========================================
# FUNÇÃO DE ANÁLISE DE JOGO
# ========================================
def analisar_jogo(jogo):
    # Aqui você pode incrementar a lógica com estatísticas reais
    # Por enquanto, será baseada em heurística simples:
    import random

    # Simula força dos times (pode ser substituído por dados reais)
    home_forca = random.randint(50, 100)
    away_forca = random.randint(50, 100)
    over15_prob = random.randint(60, 95)

    # Escolha do palpite mais confiável
    if home_forca > away_forca + 10:
        palpite = f"{jogo['home']} vence ou +1,5 gols"
        confianca = 9
    elif away_forca > home_forca + 10:
        palpite = f"{jogo['away']} vence ou +1,5 gols"
        confianca = 9
    elif over15_prob >= 75:
        palpite = "Over 1.5 gols"
        confianca = 8
    else:
        palpite = "Empate ou ambos marcam"
        confianca = 7

    return {
        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
        "palpite": palpite,
        "confianca": confianca
    }

# ========================================
# EXECUÇÃO PRINCIPAL
# ========================================
def executar():
    agora = datetime.datetime.now(FUSO).strftime('%H:%M')
    enviar_telegram(f"🚀 <b>Bot Extreme Online!</b> Analisando jogos do dia ({agora})...")

    jogos = buscar_jogos_reais()
    if not jogos:
        enviar_telegram(f"⚠️ Nenhum jogo agendado para hoje ({agora}).")
        return

    # Analisar todos os jogos e selecionar os top 5 por confiança
    palpites = [analisar_jogo(j) for j in jogos]
    palpites.sort(key=lambda x: x["confianca"], reverse=True)
    top_palpites = palpites[:5]

    # Monta mensagem para Telegram
    msg = f"🎯 <b>PALPITES DO DIA - {agora}</b>\n\n"
    for p in top_palpites:
        msg += (
            f"⚽ <b>{p['jogo']}</b>\n"
            f"🏆 {p['liga']}\n"
            f"🎯 Palpite: {p['palpite']}\n"
            f"🔥 Confiança: {p['confianca']}/10\n\n"
        )

    enviar_telegram(msg)
    print("✅ Bot finalizado.")

# ========================================
# RODAR BOT
# ========================================
if __name__ == "__main__":
    executar()
