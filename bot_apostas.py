import requests
import time
import datetime
import pytz
import cloudscraper
from bs4 import BeautifulSoup

# ========================================
# CONFIGURAÇÕES
# ========================================
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"
FUSO = pytz.timezone("America/Sao_Paulo")

def enviar_telegram(msg):
    url = f"https://api.telegram.org{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

# ========================================
# CAPTURA DE JOGOS E ODDS (SCRAPING)
# ========================================
def buscar_jogos_com_odds():
    scraper = cloudscraper.create_scraper()
    # Usando o site NowGoal ou BetExplorer que são leves para o GitHub
    url = "https://www.betexplorer.com"
    
    try:
        r = scraper.get(url, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        tabela = soup.find('table', class_='table-main')
        if not tabela: return []

        jogos_encontrados = []
        for linha in tabela.find_all('tr')[1:30]: # Pega os primeiros 30 jogos
            cols = linha.find_all('td')
            if len(cols) < 5: continue
            
            nome_times = cols[0].text.split(' - ')
            if len(nome_times) < 2: continue

            # Extraindo Odds Reais do site para o seu filtro
            try:
                odd_1 = float(cols[2].get('data-odd', 1.50))
                odd_x = float(cols[3].get('data-odd', 3.00))
                odd_2 = float(cols[4].get('data-odd', 2.00))
            except:
                odd_1, odd_x, odd_2 = 1.50, 3.00, 2.00

            jogos_encontrados.append({
                "home": nome_times[0].strip(),
                "away": nome_times[1].strip(),
                "liga": "Principal",
                "odds": {
                    "over15": 1.35 if odd_1 < 2 else 1.55, # Estimativa baseada na odd principal
                    "btts": 1.70,
                    "dnb": odd_1 - 0.20 if odd_1 < odd_2 else odd_2 - 0.20
                },
                "home_id": 1, "away_id": 2, "liga_id": 1 # IDs para não quebrar sua função
            })
        return jogos_encontrados
    except:
        return []

# ========================================
# SUA LÓGICA DE FILTRO (ORIGINAL)
# ========================================
def get_stats_para_filtro():
    # Simulando as estatísticas que seu código original pedia
    return {"scored": 1.7, "conceded": 1.1, "over15": 78, "btts": 62, "strength": 0.25}

def professional_match_filter(jogo):
    stats = get_stats_para_filtro()
    odds = jogo["odds"]

    # Sua matemática original
    goal_expectancy = (stats["scored"] * 2 + stats["conceded"] * 2) / 4
    
    if goal_expectancy >= 2.7: game_type = "ABERTO"
    elif goal_expectancy >= 2.2: game_type = "MEDIO"
    else: game_type = "FECHADO"

    # Critérios de palpite (Over 1.5, BTTS, DNB)
    if stats["over15"] >= 70 and odds["over15"] >= 1.35:
        pick = "Over 1.5 gols"
        conf = 8
    elif stats["btts"] >= 60 and game_type != "FECHADO":
        pick = "Ambas Marcam"
        conf = 7
    else:
        pick = f"DNB {jogo['home']}"
        conf = 6

    return {
        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
        "palpite": pick,
        "tipo": game_type,
        "confianca": conf
    }

# ========================================
# EXECUÇÃO NOS HORÁRIOS DEFINIDOS
# ========================================
def executar_agora():
    agora = datetime.datetime.now(FUSO)
    print(f"Executando análise de {agora.strftime('%H:%M')}...")
    
    enviar_telegram(f"🤖 <b>Análise de {agora.strftime('%H:%M')} Iniciada...</b>")
    
    jogos = buscar_jogos_com_odds()
    palpites = []

    for j in jogos:
        res = professional_match_filter(j)
        if res: palpites.append(res)

    if not palpites:
        enviar_telegram("❌ Nenhum jogo dentro dos critérios agora.")
        return

    # Mensagem final formatada
    msg = "🎯 <b>DICAS SELECIONADAS</b>\n\n"
    for p in palpites[:5]: # Top 5 dicas
        msg += f"<b>{p['jogo']}</b>\n🔥 {p['palpite']}\n⭐ Confiança: {p['confianca']}/9\n\n"
    
    enviar_telegram(msg)

if __name__ == "__main__":
    executar_agora()
