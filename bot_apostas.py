import requests
import datetime
import pytz
import time

API_TOKEN = "63f7daeeecc84264992bd70d5d911610"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"
HEADERS = {"X-Auth-Token": API_TOKEN, "User-Agent": "Mozilla/5.0"}
FUSO = pytz.timezone("America/Sao_Paulo")

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"📨 Status Telegram: {r.status_code}")
        return r.status_code
    except Exception as e:
        print(f"Erro Telegram: {e}")
        return None

def buscar_jogos_reais():
    url = "https://api.football-data.org/v4/matches"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)  # timeout aumentado
        if r.status_code != 200:
            print(f"Erro API: {r.status_code}")
            return []
        data = r.json()
        jogos_brutos = data.get("matches", [])
        lista_final = []
        for m in jogos_brutos:
            if m["status"] in ["SCHEDULED", "TIMED"]:
                lista_final.append({
                    "home": m["homeTeam"]["shortName"] or m["homeTeam"]["name"],
                    "away": m["awayTeam"]["shortName"] or m["awayTeam"]["name"],
                    "liga": m["competition"]["name"]
                })
        print(f"🌐 Total de jogos recebidos da API: {len(lista_final)}")
        return lista_final
    except Exception as e:
        print(f"Erro na captura: {e}")
        # Retorna um jogo de teste para garantir que o Telegram funcione
        return [
            {"home": "Teste FC", "away": "Mock United", "liga": "Liga Mock"}
        ]

def analisar_jogo(jogo):
    pick = "Over 1.5 gols"
    confianca = 8
    if "Teste FC" in jogo["home"]:
        pick = f"{jogo['home']} vitória ou +1,5 gols"
        confianca = 9
    return {
        "jogo": f"{jogo['home']} x {jogo['away']}",
        "liga": jogo["liga"],
        "palpite": pick,
        "confianca": confianca
    }

def executar():
    agora = datetime.datetime.now(FUSO).strftime("%H:%M")
    enviar_telegram(f"🚀 Bot Extreme Online! Teste iniciado às {agora}...")

    jogos = buscar_jogos_reais()
    if not jogos:
        enviar_telegram(f"⚠️ Nenhum jogo agendado para hoje ({agora}).")
        return

    jogos = jogos[:5]  # pegar até 5 jogos
    palpites = [analisar_jogo(j) for j in jogos]

    msg = f"🎯 PALPITES DE TESTE ({agora})\n\n"
    for p in palpites:
        msg += (
            f"⚽ {p['jogo']}\n"
            f"🏆 {p['liga']}\n"
            f"🎯 Palpite: {p['palpite']}\n"
            f"🔥 Confiança: {p['confianca']}/10\n\n"
        )
    enviar_telegram(msg)
    print("✅ Bot finalizado com sucesso!")

if __name__ == "__main__":
    executar()
    time.sleep(10)
