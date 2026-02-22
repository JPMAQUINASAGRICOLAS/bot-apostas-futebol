import requests
import datetime
import pytz
import time

# ==============================
# CONFIGURAÇÕES
# ==============================
API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"
HEADERS = {"X-Auth-Token": API_TOKEN, "User-Agent": "Mozilla/5.0"}
FUSO = pytz.timezone("America/Sao_Paulo")

# ==============================
# FUNÇÃO DE ENVIO TELEGRAM
# ==============================
def enviar_telegram(msg):
    url = f"https://api.telegram.org{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")
        return None

# ==============================
# CAPTURA DE JOGOS DO DIA
# ==============================
def buscar_jogos_reais():
    agora = datetime.datetime.now(FUSO)
    # A API v4 exige que o dateTo seja o dia seguinte para pegar todos os jogos de hoje
    hoje = agora.strftime("%Y-%m-%d")
    amanha = (agora + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Endpoint de partidas
    url = f"https://api.football-data.org{hoje}&dateTo={amanha}"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        
        if r.status_code == 429:
            print("⚠️ Limite de requisições atingido. Aguarde 1 minuto.")
            return []
            
        if r.status_code != 200:
            print(f"❌ Erro API: {r.status_code} - {r.text}")
            return []

        data = r.json()
        jogos_brutos = data.get("matches", [])
        
        lista_final = []
        for m in jogos_brutos:
            # Filtramos apenas jogos agendados ou que estão acontecendo
            if m["status"] in ["SCHEDULED", "TIMED", "LIVE", "IN_PLAY"]:
                lista_final.append({
                    "home": m["homeTeam"]["shortName"] or m["homeTeam"]["name"],
                    "away": m["awayTeam"]["shortName"] or m["awayTeam"]["name"],
                    "liga": m["competition"]["name"],
                    # Usamos as odds ou força se disponíveis, caso contrário, neutro 1.0
                    "home_strength": 1.0, 
                    "away_strength": 1.0
                })
        
        print(f"🌐 Jogos encontrados nas ligas liberadas: {len(lista_final)}")
        return lista_final

    except Exception as e:
        print(f"❌ Erro na captura: {e}")
        return []

# ==============================
# FUNÇÃO DE ANÁLISE (Lógica Adaptada)
# ==============================
def analisar_jogo(jogo):
    # Como o plano free não dá 'strength', simulamos um palpite equilibrado
    # Em um cenário real, aqui você consultaria a tabela de classificação
    return {
        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
        "palpite": "Ambas Marcam ou +1.5 Gols",
        "confianca": 7
    }

# ==============================
# EXECUÇÃO
# ==============================
def executar():
    hora_atual = datetime.datetime.now(FUSO).strftime('%H:%M')
    print(f"[{hora_atual}] 🚀 Iniciando análise...")

    jogos = buscar_jogos_reais()
    
    if not jogos:
        msg_vazia = f"⚠️ <b>Nenhum jogo encontrado</b> para hoje ({hora_atual}) nas ligas disponíveis do plano gratuito."
        enviar_telegram(msg_vazia)
        return

    palpites = []
    for j in jogos:
        res = analisar_jogo(j)
        palpites.append(res)

    # Limita a 10 palpites para não ficar muito longa a mensagem
    palpites = palpites[:10]

    msg = f"🎯 <b>PALPITES DO DIA - {hora_atual}</b>\n\n"
    for p in palpites:
        msg += (
            f"⚽ <b>{p['jogo']}</b>\n"
            f"🏆 {p['liga']}\n"
            f"🎯 Palpite: {p['palpite']}\n"
            f"🔥 Confiança: {p['confianca']}/10\n"
            f"----------------------------\n"
        )
    
    enviar_telegram(msg)
    print("✅ Processo concluído e enviado ao Telegram!")

if __name__ == "__main__":
    executar()
