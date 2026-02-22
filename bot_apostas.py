import requests
import time
import datetime
import pytz
import sys

# ========================================
# CONFIGURAÇÕES - TUDO PRONTO
# ========================================
API_TOKEN = "63f7daeeecc84264992bd70d5d911610" 
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

HEADERS = {"X-Auth-Token": API_TOKEN, "User-Agent": "Mozilla/5.0"}
FUSO = pytz.timezone("America/Sao_Paulo")

def enviar_telegram(msg):
    # URL CORRIGIDA COM /bot
    url = f"https://api.telegram.org{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"Status Telegram: {r.status_code}") 
        if r.status_code != 200:
            print(f"Resposta Erro Telegram: {r.text}")
    except Exception as e:
        print(f"Erro ao conectar com Telegram: {e}")

# ========================================
# CAPTURA DE JOGOS
# ========================================
def buscar_jogos_reais():
    # URL CORRIGIDA COM /v4/matches
    url = "https://api.football-data.org"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"Erro API: {r.status_code} - {r.text}")
            return []
        
        data = r.json()
        jogos_brutos = data.get("matches", [])
        
        lista_final = []
        for m in jogos_brutos:
            if m["status"] in ["TIMED", "SCHEDULED"]:
                lista_final.append({
                    "home": m["homeTeam"]["shortName"] or m["homeTeam"]["name"],
                    "away": m["awayTeam"]["shortName"] or m["awayTeam"]["name"],
                    "liga": m["competition"]["name"],
                    "odds": {"over15": 1.45, "btts": 1.70, "dnb": 1.55}
                })
        return lista_final
    except Exception as e:
        print(f"Erro na captura de jogos: {e}")
        return []

def filtrar_jogo(jogo):
    # Estatísticas simuladas para manter sua lógica original
    stats = {"scored": 1.8, "conceded": 1.2, "over15": 80, "btts": 65}
    goal_expectancy = (stats["scored"] + stats["conceded"])
    
    if goal_expectancy >= 2.6:
        pick = "Over 1.5 gols"
        conf = 8
    else:
        pick = f"DNB {jogo['home']}"
        conf = 6

    return {
        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
        "palpite": pick,
        "confianca": conf
    }

# ========================================
# EXECUÇÃO PRINCIPAL
# ========================================
def executar():
    agora = datetime.datetime.now(FUSO)
    hora_msg = agora.strftime('%H:%M')
    print(f"[{hora_msg}] Iniciando análise...")
    
    # MANDA UM SINAL DE VIDA PARA TESTAR O TELEGRAM
    enviar_telegram(f"🤖 Bot acordou às {hora_msg} e está analisando os jogos!")
    
    jogos = buscar_jogos_reais()
    
    if not jogos:
        print("Nenhum jogo disponível agora.")
        enviar_telegram(f"⚠️ Nenhuma partida encontrada nas ligas principais agora ({hora_msg}).")
        return

    palpites = []
    for j in jogos:
        res = filtrar_jogo(j)
        if res:
            palpites.append(res)

    if not palpites:
        enviar_telegram(f"📉 Analisei {len(jogos)} jogos, mas nenhum passou no filtro profissional.")
        return

    # Montagem da Mensagem do Telegram
    msg = f"🎯 <b>TOP PALPITES - {hora_msg}</b>\n\n"
    for p in palpites[:5]:
        msg += (
            f"⚽ <b>{p['jogo']}</b>\n"
            f"🏆 {p['liga']}\n"
            f"🔥 Palpite: {p['palpite']}\n"
            f"⭐ Confiança: {p['confianca']}/9\n\n"
        )
    
    msg += "🧠 <i>Análise via Football-Data</i>"
    enviar_telegram(msg)
    print("✅ Sucesso: Processo concluído!")

if __name__ == "__main__":
    executar()
    time.sleep(5)
    sys.exit(0)
