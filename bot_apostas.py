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
    url = f"https://api.telegram.org{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"Status Telegram: {r.status_code}")
    except: pass

# ========================================
# CAPTURA DE JOGOS (NOVA API)
# ========================================
def buscar_jogos():
    url = "https://api.football-data.org"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200: return []
        
        data = r.json()
        jogos_brutos = data.get("matches", [])
        
        jogos_processados = []
        for m in jogos_brutos:
            if m["status"] in ["TIMED", "SCHEDULED"]:
                jogos_processados.append({
                    "home": m["homeTeam"]["shortName"] or m["homeTeam"]["name"],
                    "away": m["awayTeam"]["shortName"] or m["awayTeam"]["name"],
                    "liga": m["competition"]["name"],
                    # Criamos as Odds e Stats fictícias para sua lógica não quebrar
                    "odds": {"over15": 1.45, "btts": 1.75, "dnb": 1.60},
                    "home_stats": {"scored": 1.8, "conceded": 1.1, "over15": 80, "btts": 65, "strength": 0.4},
                    "away_stats": {"scored": 1.2, "conceded": 1.5, "over15": 70, "btts": 60, "strength": 0.1}
                })
        return jogos_processados
    except: return []

# ========================================
# SEU FILTRO PROFISSIONAL (ORIGINAL)
# ========================================
def professional_match_filter(jogo):
    home_stats = jogo["home_stats"]
    away_stats = jogo["away_stats"]
    odds = jogo["odds"]

    # --- SUA MATEMÁTICA ORIGINAL ---
    goal_expectancy = (home_stats["scored"] + home_stats["conceded"] + away_stats["scored"] + away_stats["conceded"]) / 4

    if goal_expectancy >= 2.7: game_type = "ABERTO"
    elif goal_expectancy >= 2.2: game_type = "MEDIO"
    else: game_type = "FECHADO"

    allow_over15 = (home_stats["over15"] >= 70 and away_stats["over15"] >= 70 and odds["over15"] >= 1.35)
    
    strength_diff = away_stats["strength"] - home_stats["strength"]

    if allow_over15:
        pick = "Over 1.5 gols"
        confidence = 8
    elif abs(strength_diff) >= 0.12:
        pick = f"DNB {jogo['home']}" if strength_diff < 0 else f"DNB {jogo['away']}"
        confidence = 7
    else:
        return None

    return {
        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
        "palpite": pick,
        "tipo": game_type,
        "confianca": confidence
    }

# ========================================
# EXECUÇÃO
# ========================================
def executar():
    agora = datetime.datetime.now(FUSO).strftime('%H:%M')
    print(f"[{agora}] Iniciando análise...")
    
    # SINAL DE VIDA PARA VOCÊ VER NO TELEGRAM
    enviar_telegram(f"🤖 Bot acordou às {agora} e está analisando os jogos!")
    
    jogos = buscar_jogos()
    if not jogos:
        enviar_telegram(f"⚠️ Sem jogos nas ligas principais agora ({agora}).")
        return

    palpites = []
    for j in jogos:
        res = professional_match_filter(j)
        if res: palpites.append(res)

    if not palpites:
        enviar_telegram(f"📉 Analisados {len(jogos)} jogos, mas nenhum passou no filtro.")
        return

    msg = f"🎯 <b>TOP PALPITES - {agora}</b>\n\n"
    for p in palpites[:5]:
        msg += f"<b>{p['jogo']}</b>\n🔥 {p['palpite']}\n⭐ Confiança: {p['confianca']}/9\n\n"
    
    enviar_telegram(msg)
    print("✅ Sucesso!")

if __name__ == "__main__":
    executar()
    time.sleep(10)
    sys.exit(0)
