import requests
import time
import datetime
import pytz

# ========================================
# CONFIGURAÇÕES
# ========================================
API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

BASE_URL = "https://api.football-data.org"
HEADERS = {"X-Auth-Token": API_TOKEN}
FUSO = pytz.timezone("America/Sao_Paulo")

# Ligas seguras para o plano FREE
LIGAS_FREE = ['PL', 'PD', 'BL1', 'SA', 'FL1', 'PPL']

session = requests.Session()
session.headers.update(HEADERS)

def buscar_jogos_por_liga():
    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")
    jogos_dia = []
    
    for liga in LIGAS_FREE:
        # Busca jogos específicos daquela liga para evitar o erro 404 global
        url = f"{BASE_URL}/competitions/{liga}/matches"
        params = {"dateFrom": hoje, "dateTo": hoje}
        
        try:
            print(f"📡 Checando liga: {liga}...")
            r = session.get(url, params=params, timeout=15)
            
            if r.status_code == 200:
                data = r.json()
                for match in data.get("matches", []):
                    if match["status"] in ["TIMED", "SCHEDULED"]:
                        jogos_dia.append({
                            "id": match["id"],
                            "home": match["homeTeam"]["shortName"] or match["homeTeam"]["name"],
                            "away": match["awayTeam"]["shortName"] or match["awayTeam"]["name"],
                            "home_id": match["homeTeam"]["id"],
                            "away_id": match["awayTeam"]["id"],
                            "liga_id": liga,
                            "liga_nome": match["competition"]["name"]
                        })
            else:
                print(f"⚠️ Liga {liga} retornou status {r.status_code}")
            
            # Pausa obrigatória: 10 requisições por minuto = 1 a cada 6 segundos
            time.sleep(6) 
            
        except Exception as e:
            print(f"❌ Erro na liga {liga}: {e}")
            
    return jogos_dia

def get_stats(team_id, league_id):
    try:
        url = f"{BASE_URL}/competitions/{league_id}/standings"
        r = session.get(url, timeout=10)
        if r.status_code != 200: return None
        
        # Procura o time na tabela 'TOTAL'
        table = r.json()["standings"][0]["table"]
        for team in table:
            if team["team"]["id"] == team_id:
                pj = team["playedGames"]
                if pj < 2: return None
                return {
                    "gp": team["goalsFor"] / pj,
                    "gc": team["goalsAgainst"] / pj,
                    "diff": (team["goalsFor"] - team["goalsAgainst"]) / pj
                }
    except: return None
    return None

def executar():
    print(f"🚀 Iniciando Varredura: {datetime.datetime.now(FUSO).strftime('%H:%M:%S')}")
    
    jogos = buscar_jogos_por_liga()
    print(f"📋 {len(jogos)} jogos encontrados hoje.")
    
    palpites = []
    for j in jogos:
        print(f"🔍 Analisando: {j['home']} x {j['away']}")
        
        h = get_stats(j["home_id"], j["liga_id"])
        time.sleep(6) # Respeitando limite da API
        a = get_stats(j["away_id"], j["liga_id"])
        time.sleep(6)
        
        if h and a:
            exp_gols = (h["gp"] + h["gc"] + a["gp"] + a["gc"]) / 4
            # Critério simples: Média de gols do confronto > 2.5
            if exp_gols >= 2.5:
                res = {
                    "msg": f"⚽ <b>{j['home']} x {j['away']}</b>\n🏆 {j['liga_nome']}\n💎 Over 1.5 Gols\n📈 Exp: {exp_gols:.2f}"
                }
                palpites.append(res)
                print(f"   ✅ Aprovado!")
            else:
                print(f"   ❌ Reprovado (Exp: {exp_gols:.2f})")

    if palpites:
        msg_final = "🎯 <b>PALPITES DO DIA</b>\n\n" + "\n\n".join([p["msg"] for p in palpites])
        requests.post(f"https://api.telegram.org{TOKEN_TELEGRAM}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": msg_final, "parse_mode": "HTML"})
        print("✅ Telegram enviado!")
    else:
        print("ℹ️ Nenhum jogo aprovado.")

if __name__ == "__main__":
    executar()
