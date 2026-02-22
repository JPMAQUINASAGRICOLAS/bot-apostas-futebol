import requests
import datetime
import pytz
import time

# =========================
# CONFIGURAÇÃO
# =========================
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"
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
# JOGOS DE TESTE
# =========================
def gerar_jogos_teste():
    # 5 jogos fictícios para testar o bot
    jogos = [
        {"home": "Milan", "away": "Inter", "liga": "Serie A"},
        {"home": "Barcelona", "away": "Atletico Bilbao", "liga": "La Liga"},
        {"home": "Liverpool", "away": "Manchester City", "liga": "Premier League"},
        {"home": "Paris SG", "away": "Olympique Lyon", "liga": "Ligue 1"},
        {"home": "Ajax", "away": "PSV", "liga": "Eredivisie"}
    ]
    return jogos

# =========================
# FUNÇÃO DE ANÁLISE
# =========================
def analisar_jogo(jogo):
    """
    Gera o melhor palpite possível para um jogo
    """
    # Estatísticas fictícias para simular análise
    import random
    palpite = ""
    confianca = random.randint(6, 9)  # Confiança de 6 a 9

    # Lógica simples: escolher um tipo de aposta com base na liga e nomes
    if "Milan" in jogo["home"] or "Barcelona" in jogo["home"] or "Liverpool" in jogo["home"]:
        palpite = f"{jogo['home']} vitória ou +1,5 gols"
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
    enviar_telegram(f"🚀 <b>Bot Teste Imediato Iniciado!</b> ({hora_msg})")

    jogos = gerar_jogos_teste()
    palpites = []

    for j in jogos:
        res = analisar_jogo(j)
        palpites.append(res)

    # Montagem da mensagem
    msg = f"🎯 <b>PALPITES DE TESTE - {hora_msg}</b>\n\n"
    for p in palpites:
        msg += (
            f"⚽ <b>{p['jogo']}</b>\n"
            f"🏆 {p['liga']}\n"
            f"🎯 Palpite: {p['palpite']}\n"
            f"🔥 Confiança: {p['confianca']}/10\n\n"
        )

    msg += "🧠 <i>Teste com jogos fictícios</i>"
    enviar_telegram(msg)
    print("✅ Teste finalizado!")

if __name__ == "__main__":
    executar()
    time.sleep(5)
