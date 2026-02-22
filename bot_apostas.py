import requests
import datetime
import pytz
import time
import sys

# ========================================
# CONFIGURAÇÕES
# ========================================
API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

HEADERS = {"X-Auth-Token": API_TOKEN, "User-Agent": "Mozilla/5.0"}
FUSO = pytz.timezone("America/Sao_Paulo")
HORARIOS_ENVIO = ["00:00", "08:00", "15:00"]  # horários de envio

# ========================================
# FUNÇÕES
# ========================================
def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"📨 Status do Telegram: {r.status_code}")
        return r.status_code
    except Exception as e:
        print(f"⚠️ Erro Telegram: {e}")
        return None

def buscar_jogos_reais():
    url = "https://api.football-data.org/v4/matches"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"⚠️ Status API: {r.status_code}")
            return []

        data = r.json()
        jogos_brutos = data.get("matches", [])
        hoje = datetime.datetime.now(FUSO).date()

        lista_final = []
        for m in jogos_brutos:
            dt_jogo = datetime.datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).astimezone(FUSO).date()
            if dt_jogo == hoje and m["status"] in ["SCHEDULED", "TIMED"]:
                lista_final.append({
                    "home": m["homeTeam"]["shortName"] or m["homeTeam"]["name"],
                    "away": m["awayTeam"]["shortName"] or m["awayTeam"]["name"],
                    "liga": m["competition"]["name"],
                    "status": m["status"]
                })
        print(f"🌐 Jogos encontrados hoje: {len(lista_final)}")
        return lista_final
    except Exception as e:
        print(f"⚠️ Erro ao buscar jogos: {e}")
        return []

def analisar_jogo(jogo):
    """
    Analisa o jogo e retorna o palpite mais provável e confiança.
    Pode incluir:
    - Vitória de um time
    - Over/Under gols
    - Handicap
    """
    # Estatísticas fictícias para exemplo, podem ser integradas a odds reais
    stats = {
        "home_strength": 1.8,
        "away_strength": 1.5,
        "home_goals": 1.5,
        "away_goals": 1.2
    }

    pick = ""
    confianca = 0

    # Se o time da casa é bem mais forte
    if stats["home_strength"] - stats["away_strength"] >= 0.4:
        pick = f"{jogo['home']} vitória ou +1,5 gols"
        confianca = 9
    # Se os times são equilibrados e jogo tende a ter gols
    elif (stats["home_goals"] + stats["away_goals"]) >= 2.5:
        pick = "Over 1.5 gols"
        confianca = 8
    # Se o jogo é clássico ou equilibrado
    else:
        pick = f"DNB {jogo['home']}"
        confianca = 7

    return {
        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
        "palpite": pick,
        "confianca": confianca
    }

def selecionar_top_jogos(jogos, top_n=5):
    """
    Seleciona os top_n jogos do dia.
    Aqui você pode melhorar com critérios reais (odds, histórico, etc.)
    """
    analisados = [analisar_jogo(j) for j in jogos]
    # Ordena pela confiança
    analisados.sort(key=lambda x: x["confianca"], reverse=True)
    return analisados[:min(len(analisados), top_n)]

def executar():
    agora = datetime.datetime.now(FUSO)
    hora_atual = agora.strftime('%H:%M')
    print(f"[{hora_atual}] 🚀 BOT INICIANDO...")

    if hora_atual not in HORARIOS_ENVIO:
        print(f"⏳ Horário {hora_atual} não programado. Encerrando.")
        return

    enviar_telegram(f"🚀 BOT ONLINE - Analisando jogos das {hora_atual}...")

    jogos = buscar_jogos_reais()
    if not jogos:
        enviar_telegram(f"⚠️ Nenhum jogo disponível hoje ({hora_atual}).")
        print("⚠️ Nenhum jogo encontrado.")
        return

    top_jogos = selecionar_top_jogos(jogos, top_n=5)

    msg = f"🎯 PALPITES EXTREMOS - {hora_atual}\n\n"
    for p in top_jogos:
        msg += (
            f"⚽ {p['jogo']}\n"
            f"🏆 {p['liga']}\n"
            f"🎯 Palpite: {p['palpite']}\n"
            f"🔥 Confiança: {p['confianca']}/10\n\n"
        )
    msg += "🧠 Análise extrema via Football-Data API"

    enviar_telegram(msg)
    print("✅ BOT FINALIZADO")

# ========================================
# EXECUÇÃO
# ========================================
if __name__ == "__main__":
    executar()
    time.sleep(5)
    sys.exit(0)
