import requests
import time
import datetime
import pytz

# ========================================
# CONFIGURAÇÕES
# ========================================

API_TOKEN = "1a185fa6bcccfcada90c54b747eb1172"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

BASE_URL = "https://api.football-data.org"
HEADERS = {"X-Auth-Token": API_TOKEN}

session = requests.Session()
session.headers.update(HEADERS)

FUSO = pytz.timezone("America/Sao_Paulo")
LIGAS_PERMITIDAS = ['PL', 'PD', 'BL1', 'SA', 'FL1', 'BSA', 'ELC', 'PPL']

stats_cache = {}

# ========================================
# BUSCAR JOGOS (FOOTBALL-DATA.ORG)
# ========================================

def buscar_jogos():
    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/matches"
    params = {"dateFrom": hoje, "dateTo": hoje}

    try:
        r = session.get(url, params=params, timeout=15)
        data = r.json()
        jogos = []

        for match in data.get("matches", []):
            liga_code = match["competition"]["code"]
            if liga_code not in LIGAS_PERMITIDAS: continue
            if match["status"] not in ["TIMED", "SCHEDULED"]: continue

            jogos.append({
                "fixture_id": match["id"],
                "home": match["homeTeam"]["shortName"] or match["homeTeam"]["name"],
                "away": match["awayTeam"]["shortName"] or match["awayTeam"]["name"],
                "home_id": match["homeTeam"]["id"],
                "away_id": match["awayTeam"]["id"],
                "liga": match["competition"]["name"],
                "liga_id": liga_code,
                "odds": {"over15": 1.45, "btts": 1.75, "dnb": 1.50} # Odds estimadas (API Free limita odds)
            })
        return jogos
    except Exception as e:
        print(f"❌ Erro API: {e}")
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
        table = r.json()["standings"][0]["table"]

        for team in table:
            if team["team"]["id"] == team_id:
                pj = team["playedGames"]
                if pj == 0: return None
                res = {
                    "scored": team["goalsFor"] / pj,
                    "conceded": team["goalsAgainst"] / pj,
                    "over15": 75.0, # Média estimada
                    "btts": 55.0,
                    "strength": (team["goalsFor"] - team["goalsAgainst"]) / pj
                }
                stats_cache[chave] = res
                return res
    except: return None
    return None

# ========================================
# FILTRO COM LOG DE AUDITORIA
# ========================================

def professional_match_filter(jogo):
    nome_jogo = f"{jogo['home']} x {jogo['away']}"
    print(f"\n🔍 Analisando: {nome_jogo}")

    h = get_stats(jogo["home_id"], jogo["liga_id"])
    a = get_stats(jogo["away_id"], jogo["liga_id"])

    if not h or not a:
        print(f"   ⚠️ Abortado: Sem dados estatísticos suficientes.")
        return None

    # Cálculo de Expectativa
    goal_exp = (h["scored"] + h["conceded"] + a["scored"] + a["conceded"]) / 4
    game_type = "ABERTO" if goal_exp >= 2.6 else "MEDIO" if goal_exp >= 2.1 else "FECHADO"
    
    # Lógica de Critérios
    allow_over15 = h["over15"] >= 70 and a["over15"] >= 70
    allow_btts = h["btts"] >= 55 and a["btts"] >= 55 and game_type != "FECHADO"
    diff = a["strength"] - h["strength"]

    # LOG DE STATUS
    print(f"   📊 Exp. Gols: {goal_exp:.2f} ({game_type})")
    print(f"   📊 Força Relativa (Diff): {diff:.2f}")

    pick = None
    if allow_over15: pick = "Over 1.5 gols"
    elif allow_btts: pick = "Ambas marcam"
    elif abs(diff) >= 0.15:
        pick = f"{jogo['away'] if diff > 0 else jogo['home']} DNB"

    if not pick:
        print(f"   ❌ Reprovado: Não atingiu critérios de mercado.")
        return None

    # Cálculo Confiança
    conf = 4
    if game_type == "ABERTO": conf += 2
    if abs(diff) > 0.20: conf += 2
    if goal_exp > 3.0: conf += 1

    if conf < 5:
        print(f"   ❌ Reprovado: Confiança baixa ({conf}/9)")
        return None

    print(f"   ✅ APROVADO: {pick} (Confiança {conf}/9)")
    return {
        "jogo": nome_jogo,
        "liga": jogo["liga"],
        "palpite": pick,
        "tipo": game_type,
        "confianca": conf
    }

# ========================================
# FUNÇÕES DE APOIO E EXECUÇÃO
# ========================================

def enviar_telegram(msg):
    url = f"https://api.telegram.org{TOKEN_TELEGRAM}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except: pass

def montar_msg(palpites):
    if not palpites: return "❌ Nenhum palpite encontrado com os critérios atuais."
    msg = "🎯 <b>TOP PALPITES DO DIA</b>\n\n"
    for p in palpites:
        msg += f"⚽ <b>{p['jogo']}</b>\n🏆 {p['liga']}\n💎 {p['palpite']}\n📈 Confiança: {p['confianca']}/9\n\n"
    return msg + "🧠 Bot Football-Data"

def executar():
    print(f"\n🚀 Iniciando Varredura: {datetime.datetime.now().strftime('%H:%M:%S')}")
    enviar_telegram("🤖 Iniciando análise diária...")
    
    jogos = buscar_jogos()
    print(f"📋 {len(jogos)} jogos pré-filtrados nas ligas permitidas.")
    
    palpites = []
    for j in jogos:
        res = professional_match_filter(j)
        if res: palpites.append(res)
        time.sleep(1.5) # Evitar Rate Limit da API Free

    palpites.sort(key=lambda x: x["confianca"], reverse=True)
    msg = montar_msg(palpites[:5])
    enviar_telegram(msg)
    print("\n✅ Relatório enviado ao Telegram.")

if __name__ == "__main__":
    executar()
