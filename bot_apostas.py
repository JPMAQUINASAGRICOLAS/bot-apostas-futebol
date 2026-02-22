import requests
import time
import datetime
import pytz

# ========================================
# CONFIGURAÇÕES ATUALIZADAS
# ========================================

API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

BASE_URL = "https://api.football-data.org"
HEADERS = {"X-Auth-Token": API_TOKEN}

session = requests.Session()
session.headers.update(HEADERS)

FUSO = pytz.timezone("America/Sao_Paulo")

# Ligas permitidas no plano FREE do football-data.org
LIGAS_PERMITIDAS = ['PL', 'PD', 'BL1', 'SA', 'FL1', 'PPL', 'CL']

stats_cache = {}

# ========================================
# TELEGRAM
# ========================================

def enviar_telegram(msg):
    url = f"https://api.telegram.org{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

# ========================================
# BUSCAR JOGOS (FOOTBALL-DATA.ORG)
# ========================================

def buscar_jogos():
    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/matches"
    params = {"dateFrom": hoje, "dateTo": hoje}

    try:
        r = session.get(url, params=params, timeout=15)
        
        # Proteção contra erros de API (403, 429, etc) que geram erro JSON
        if r.status_code != 200:
            print(f"❌ Erro API ({r.status_code}): Resposta não é JSON válido.")
            return []

        data = r.json()
        jogos = []

        for match in data.get("matches", []):
            liga_code = match["competition"]["code"]
            
            if liga_code not in LIGAS_PERMITIDAS:
                continue

            if match["status"] not in ["TIMED", "SCHEDULED"]:
                continue

            jogos.append({
                "fixture_id": match["id"],
                "home": match["homeTeam"]["shortName"] or match["homeTeam"]["name"],
                "away": match["awayTeam"]["shortName"] or match["awayTeam"]["name"],
                "home_id": match["homeTeam"]["id"],
                "away_id": match["awayTeam"]["id"],
                "liga": match["competition"]["name"],
                "liga_id": liga_code,
                "odds": {"over15": 1.45, "btts": 1.70, "dnb": 1.50}
            })
        return jogos
    except Exception as e:
        print(f"❌ Erro inesperado ao buscar: {e}")
        return []

# ========================================
# BUSCAR STATS (VIA STANDINGS)
# ========================================

def get_stats(team_id, league_id):
    chave = f"{team_id}-{league_id}"
    if chave in stats_cache: return stats_cache[chave]

    try:
        url = f"{BASE_URL}/competitions/{league_id}/standings"
        r = session.get(url, timeout=10)
        
        if r.status_code != 200: return None
        
        data = r.json()
        # Pega a tabela principal (TOTAL)
        table = data["standings"][0]["table"]

        for team in table:
            if team["team"]["id"] == team_id:
                pj = team["playedGames"]
                if pj < 3: return None # Evita times sem histórico na temporada
                
                res = {
                    "scored": team["goalsFor"] / pj,
                    "conceded": team["goalsAgainst"] / pj,
                    "over15": 75.0,
                    "btts": 58.0,
                    "strength": (team["goalsFor"] - team["goalsAgainst"]) / pj
                }
                stats_cache[chave] = res
                return res
    except:
        return None
    return None

# ========================================
# FILTRO PROFISSIONAL COM LOG
# ========================================

def professional_match_filter(jogo):
    nome_jogo = f"{jogo['home']} x {jogo['away']}"
    print(f"\n🔍 Analisando: {nome_jogo}")

    h = get_stats(jogo["home_id"], jogo["liga_id"])
    # Pequeno delay para respeitar o limite de 10 requisições por minuto
    time.sleep(2.5) 
    a = get_stats(jogo["away_id"], jogo["liga_id"])

    if not h or not a:
        print(f"   ⚠️ Sem dados suficientes (Ligas no início ou erro).")
        return None

    goal_exp = (h["scored"] + h["conceded"] + a["scored"] + a["conceded"]) / 4
    diff = a["strength"] - h["strength"]

    print(f"   📊 Exp Gols: {goal_exp:.2f} | Diff Força: {diff:.2f}")

    # Lógica de Palpite
    pick = None
    if goal_exp >= 2.6: pick = "Over 1.5 gols"
    elif abs(diff) >= 0.25: pick = f"{jogo['away'] if diff > 0 else jogo['home']} DNB"
    
    if not pick:
        print(f"   ❌ Reprovado nos critérios técnicos.")
        return None

    # Confiança (Simples)
    conf = 6 if goal_exp > 3.0 or abs(diff) > 0.4 else 5

    print(f"   ✅ APROVADO: {pick} ({conf}/9)")
    return {
        "jogo": nome_jogo, "liga": jogo["liga"], "palpite": pick, "confianca": conf
    }

# ========================================
# EXECUÇÃO PRINCIPAL
# ========================================

def executar():
    agora = datetime.datetime.now(FUSO).strftime("%H:%M:%S")
    print(f"🚀 Iniciando Varredura: {agora}")
    
    jogos = buscar_jogos()
    print(f"📋 {len(jogos)} jogos encontrados nas ligas permitidas.")
    
    palpites = []
    for j in jogos:
        res = professional_match_filter(j)
        if res: palpites.append(res)
        time.sleep(2.5) # Delay crucial para não ser bloqueado pela API

    if palpites:
        msg = "🎯 <b>TOP PALPITES DO DIA</b>\n\n"
        for p in palpites[:5]:
            msg += f"⚽ <b>{p['jogo']}</b>\n🏆 {p['liga']}\n💎 {p['palpite']}\n📈 Confiança: {p['confianca']}/9\n\n"
        enviar_telegram(msg)
    else:
        print("ℹ️ Nenhum palpite atingiu os critérios hoje.")

if __name__ == "__main__":
    executar()
