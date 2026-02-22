import requests
import time
import datetime
import pytz

# ========================================
# CONFIGURAÇÕES DEFINITIVAS
# ========================================
API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

BASE_URL = "https://api.football-data.org"
HEADERS = {"X-Auth-Token": API_TOKEN}
FUSO = pytz.timezone("America/Sao_Paulo")

# Ligas confirmadas no plano FREE v4
LIGAS_FREE = ['PL', 'PD', 'BL1', 'SA', 'FL1', 'CL']

session = requests.Session()
session.headers.update(HEADERS)

def buscar_jogos_estavel():
    hoje = datetime.datetime.now(FUSO).strftime("%Y-%m-%d")
    # Tenta buscar todas as ligas permitidas de uma vez
    url = f"{BASE_URL}/matches"
    params = {
        "dateFrom": hoje,
        "dateTo": hoje,
        "competitions": ",".join(LIGAS_FREE)
    }

    try:
        print(f"📡 Solicitando jogos do dia ({hoje})...")
        r = session.get(url, params=params, timeout=15)
        
        if r.status_code != 200:
            print(f"❌ Erro API ({r.status_code}): {r.text[:100]}")
            return []

        data = r.json()
        jogos_encontrados = []
        
        for match in data.get("matches", []):
            # Apenas jogos que ainda não começaram
            if match["status"] in ["TIMED", "SCHEDULED"]:
                jogos_encontrados.append({
                    "id": match["id"],
                    "home": match["homeTeam"]["shortName"] or match["homeTeam"]["name"],
                    "away": match["awayTeam"]["shortName"] or match["awayTeam"]["name"],
                    "home_id": match["homeTeam"]["id"],
                    "away_id": match["awayTeam"]["id"],
                    "liga_id": match["competition"]["code"],
                    "liga_nome": match["competition"]["name"]
                })
        
        return jogos_encontrados

    except Exception as e:
        print(f"❌ Falha na conexão: {e}")
        return []

def get_stats(team_id, league_id):
    """Busca estatísticas baseadas na tabela de classificação (Standings)"""
    try:
        url = f"{BASE_URL}/competitions/{league_id}/standings"
        r = session.get(url, timeout=10)
        
        if r.status_code != 200:
            return None
            
        data = r.json()
        # Procura na tabela 'TOTAL'
        table = data["standings"][0]["table"]
        
        for team in table:
            if team["team"]["id"] == team_id:
                pj = team["playedGames"]
                if pj < 3: return None # Ignora se o campeonato estiver no comecinho
                
                return {
                    "gp": team["goalsFor"] / pj,
                    "gc": team["goalsAgainst"] / pj,
                    "posicao": team["position"]
                }
    except:
        return None
    return None

def executar():
    agora = datetime.datetime.now(FUSO).strftime("%H:%M:%S")
    print(f"\n🚀 VARREDURA INICIADA: {agora}")
    
    jogos = buscar_jogos_estavel()
    print(f"📋 {len(jogos)} jogos pré-filtrados para análise técnica.")
    
    palpites = []
    
    for j in jogos:
        print(f"🔍 Analisando: {j['home']} x {j['away']} ({j['liga_id']})")
        
        # Respeita o limite de 10 req/min da API Free (6 segundos entre chamadas)
        time.sleep(6) 
        h = get_stats(j["home_id"], j["liga_id"])
        
        time.sleep(6)
        a = get_stats(j["away_id"], j["liga_id"])
        
        if h and a:
            # Cálculo de Expectativa de Gols (Média Simples)
            exp_confronto = (h["gp"] + h["gc"] + a["gp"] + a["gc"]) / 4
            
            # Filtro: Se a média do jogo for alta, gera o palpite
            if exp_confronto >= 2.5:
                res = f"⚽ <b>{j['home']} x {j['away']}</b>\n🏆 {j['liga_nome']}\n💎 Palpite: Over 1.5 Gols\n📈 Exp. Gols: {exp_confronto:.2f}"
                palpites.append(res)
                print(f"   ✅ APROVADO (Exp: {exp_confronto:.2f})")
            else:
                print(f"   ❌ Reprovado (Exp: {exp_confronto:.2f})")
        else:
            print("   ⚠️ Dados insuficientes para este jogo.")

    # Envio para o Telegram
    if palpites:
        msg_final = "🎯 <b>PALPITES DO DIA</b>\n\n" + "\n\n".join(palpites)
        try:
            requests.post(f"https://api.telegram.org{TOKEN_TELEGRAM}/sendMessage", 
                          json={"chat_id": CHAT_ID, "text": msg_final, "parse_mode": "HTML"},
                          timeout=10)
            print("✅ Relatório enviado ao Telegram!")
        except:
            print("❌ Erro ao enviar para o Telegram.")
    else:
        print("ℹ️ Nenhum palpite gerado nos critérios de hoje.")

if __name__ == "__main__":
    executar()
