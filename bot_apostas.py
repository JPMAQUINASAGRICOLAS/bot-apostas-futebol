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
# FUNÇÃO TELEGRAM
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
# BUSCAR JOGOS DO DIA
# ========================================
def buscar_jogos_reais():
    url = "https://api.football-data.org/v4/matches"
    hoje = datetime.datetime.now(FUSO).date().isoformat()
    params = {"dateFrom": hoje, "dateTo": hoje}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if r.status_code != 200:
            print(f"Erro API: {r.status_code}")
            return []
        data = r.json()
        jogos_brutos = data.get("matches", [])
        jogos_filtrados = [
            j for j in jogos_brutos
            if j["status"] in ["SCHEDULED", "TIMED"]  # Jogos ainda não iniciados
        ]
        return jogos_filtrados
    except Exception as e:
        print(f"Erro na captura: {e}")
        return []

# ========================================
# CALCULA PALPITE
# ========================================
def analisar_jogo(jogo):
    """
    Analisa um jogo e retorna o melhor palpite:
    - Vitória casa / visitante
    - DNB
    - Over/Under
    """
    # Dados fictícios para simular análise de força
    # Em produção, você pode integrar odds reais ou rankings
    odds_casa = 1.8  # chance estimada do time da casa
    odds_fora = 2.5  # chance estimada do visitante
    odds_empate = 3.2
    
    home = jogo["homeTeam"]["name"]
    away = jogo["awayTeam"]["name"]
    liga = jogo["competition"]["name"]

    # Simples lógica baseada em odds
    if odds_casa < odds_fora and odds_casa < odds_empate:
        pick = f"Vitória {home}"
        confianca = 9
    elif odds_fora < odds_casa and odds_fora < odds_empate:
        pick = f"Vitória {away}"
        confianca = 9
    elif abs(odds_casa - odds_fora) < 0.3:  # times equilibrados
        pick = "Over 1.5 gols"
        confianca = 7
    else:
        pick = "DNB " + home
        confianca = 8

    return {
        "jogo": f"{home} x {away}",
        "liga": liga,
        "palpite": pick,
        "confianca": confianca
    }

# ========================================
# EXECUÇÃO PRINCIPAL
# ========================================
def executar():
    agora = datetime.datetime.now(FUSO)
    hora_msg = agora.strftime('%H:%M')
    print(f"[{hora_msg}] 🚀 BOT INICIANDO...")

    enviar_telegram(f"🚀 <b>Bot Extreme Online!</b> Analisando jogos do dia ({hora_msg})...")

    jogos = buscar_jogos_reais()
    print(f"🌐 Total de jogos recebidos da API: {len(jogos)}")
    
    if not jogos:
        enviar_telegram(f"⚠️ Nenhum jogo agendado para hoje ({hora_msg}).")
        return

    palpites = [analisar_jogo(j) for j in jogos]

    # Ordena por confiança e seleciona top 5
    palpites.sort(key=lambda x: x["confianca"], reverse=True)
    top_palpites = palpites[:5]

    msg = f"🎯 <b>TOP PALPITES - {hora_msg}</b>\n\n"
    for p in top_palpites:
        msg += (
            f"⚽ <b>{p['jogo']}</b>\n"
            f"🏆 {p['liga']}\n"
            f"🎯 Palpite: {p['palpite']}\n"
            f"🔥 Confiança: {p['confianca']}/10\n\n"
        )
    msg += "🧠 <i>Análise Extreme Betting Bot</i>"
    
    enviar_telegram(msg)
    print("✅ BOT FINALIZADO")

if __name__ == "__main__":
    executar()
