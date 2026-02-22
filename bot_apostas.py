import requests
import datetime
import pytz
import time
import sys

# ========================================
# CONFIGURAÇÃO
# ========================================
API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

HEADERS = {"X-Auth-Token": API_TOKEN, "User-Agent": "Mozilla/5.0"}
FUSO = pytz.timezone("America/Sao_Paulo")

# Horários de envio (00:00, 08:00, 15:00)
HORARIOS_ENVIO = ["00:00", "08:00", "15:00"]

# ========================================
# FUNÇÃO TELEGRAM
# ========================================
def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"📨 Status do Telegram: {r.status_code}")
        return r.status_code
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")
        return None

# ========================================
# BUSCAR JOGOS REAIS
# ========================================
def buscar_jogos_hoje():
    url = "https://api.football-data.org/v4/matches"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"❌ Erro API: {r.status_code}")
            return []
        data = r.json()
        jogos_brutos = data.get("matches", [])

        # Filtra jogos de hoje e que ainda não começaram
        hoje = datetime.datetime.now(FUSO).date()
        jogos_hoje = []
        for j in jogos_brutos:
            data_jogo = datetime.datetime.fromisoformat(j["utcDate"].replace("Z", "+00:00")).astimezone(FUSO)
            if data_jogo.date() == hoje and j["status"] in ["SCHEDULED", "TIMED"]:
                jogos_hoje.append({
                    "home": j["homeTeam"]["name"],
                    "away": j["awayTeam"]["name"],
                    "liga": j["competition"]["name"],
                    "date": data_jogo
                })
        print(f"🌐 Total de jogos recebidos da API: {len(jogos_brutos)}")
        print(f"⚽ Jogos filtrados para hoje: {len(jogos_hoje)}")
        for j in jogos_hoje:
            print(f"- {j['home']} x {j['away']} | Liga: {j['liga']} | {j['date'].strftime('%H:%M')}")
        return jogos_hoje
    except Exception as e:
        print(f"❌ Erro ao buscar jogos: {e}")
        return []

# ========================================
# FILTRAR E GERAR PALPITE
# ========================================
def gerar_palpite(jogo):
    # Aqui você pode aumentar a lógica de análise: histórico, over/under, favoritos
    # Versão extrema: simples mas com confiabilidade baseada em over 1.5 se esperado > 2.5 gols
    stats = {"scored": 1.8, "conceded": 1.2}  # Estatística base
    expectativa = stats["scored"] + stats["conceded"]

    if expectativa >= 2.6:
        palpite = "Over 1.5 gols"
        confianca = 8
    else:
        palpite = f"DNB {jogo['home']}"  # Draw no bet para o time da casa
        confianca = 7

    return {
        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
        "palpite": palpite,
        "confianca": confianca
    }

# ========================================
# EXECUTAR BOT
# ========================================
def executar():
    agora = datetime.datetime.now(FUSO)
    hora_msg = agora.strftime("%H:%M")
    print(f"[{hora_msg}] 🚀 BOT INICIANDO...")

    enviar_telegram(f"🚀 BOT INICIANDO... Analisando jogos das {hora_msg}")

    jogos = buscar_jogos_hoje()
    if not jogos:
        enviar_telegram(f"⚠️ Nenhum jogo hoje para análise ({hora_msg})")
        print("⚠️ Nenhum jogo hoje.")
        return

    # Seleciona até 5 melhores jogos
    jogos_selecionados = jogos[:5]

    palpites = []
    for j in jogos_selecionados:
        res = gerar_palpite(j)
        palpites.append(res)

    if not palpites:
        enviar_telegram(f"⚠️ Jogos filtrados, mas nenhum palpite confiável encontrado ({hora_msg})")
        print("⚠️ Nenhum palpite confiável.")
        return

    # Monta mensagem
    msg = f"🎯 PALPITES ATUALIZADOS ({hora_msg})\n\n"
    for p in palpites:
        msg += (
            f"⚽ {p['jogo']}\n"
            f"🏆 {p['liga']}\n"
            f"🎯 Palpite: {p['palpite']}\n"
            f"🔥 Confiança: {p['confianca']}/10\n\n"
        )
    enviar_telegram(msg)
    print("✅ BOT FINALIZADO")

# ========================================
# RODA AGORA
# ========================================
if __name__ == "__main__":
    executar()
    # espera para logs aparecerem no Railway
    time.sleep(10)
    sys.exit(0)
