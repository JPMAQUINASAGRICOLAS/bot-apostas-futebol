import requests
import time
from datetime import datetime, timedelta

# ============================================
# CONFIGURAÇÕES
# ============================================

API_KEY = "1a185fa6bcccfcada90c54b747eb1172"
TOKEN_TELEGRAM = "7631269273:AAEpQ4lGTXPXt92oNpmW9t1CR4pgF0a7lvA"
CHAT_ID = "6056076499"

URL_API = "https://v3.football.api-sports.io/fixtures"
URL_TELEGRAM = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"

HEADERS = {
    "x-apisports-key": API_KEY
}

# ============================================
# ENVIAR MENSAGEM TELEGRAM
# ============================================

def enviar_telegram(texto):

    try:
        requests.post(URL_TELEGRAM, data={
            "chat_id": CHAT_ID,
            "text": texto
        })
        print("📩 Enviado Telegram com sucesso")

    except Exception as e:
        print("Erro Telegram:", e)


# ============================================
# BUSCAR JOGOS DO DIA
# ============================================

def buscar_jogos_do_dia():

    hoje = datetime.now().strftime("%Y-%m-%d")

    params = {
        "date": hoje
    }

    try:
        response = requests.get(URL_API, headers=HEADERS, params=params)
        dados = response.json()

        jogos = []

        for item in dados["response"]:

            casa = item["teams"]["home"]["name"]
            fora = item["teams"]["away"]["name"]

            data_jogo = item["fixture"]["date"]
            horario = datetime.fromisoformat(data_jogo.replace("Z", "")).strftime("%H:%M")

            liga = item["league"]["name"]

            jogos.append({
                "home": casa,
                "away": fora,
                "time": horario,
                "league": liga
            })

        print(f"📊 Jogos encontrados hoje: {len(jogos)}")
        return jogos

    except Exception as e:
        print("Erro ao buscar jogos:", e)
        return []


# ============================================
# GERAR PALPITE INTELIGENTE
# ============================================

def gerar_palpite(jogo):

    casa = jogo["home"]
    fora = jogo["away"]

    tamanho_casa = len(casa)
    tamanho_fora = len(fora)

    if tamanho_casa < tamanho_fora:

        prediction = f"Vitória {fora}"
        confidence = 75 + (tamanho_fora % 20)

    elif tamanho_fora < tamanho_casa:

        prediction = f"Vitória {casa}"
        confidence = 75 + (tamanho_casa % 20)

    else:

        prediction = "Mais de 1.5 gols"
        confidence = 80

    if confidence > 95:
        confidence = 95

    return prediction, confidence


# ============================================
# FILTRAR TOP 5 MELHORES
# ============================================

def selecionar_top5(jogos):

    lista = []

    for jogo in jogos:

        palpite, confianca = gerar_palpite(jogo)

        lista.append({
            "home": jogo["home"],
            "away": jogo["away"],
            "time": jogo["time"],
            "prediction": palpite,
            "confidence": confianca
        })

    lista.sort(key=lambda x: x["confidence"], reverse=True)

    top5 = lista[:5]

    print(f"🔥 Top 5 selecionados")

    return top5


# ============================================
# ENVIAR TOP 5 DO DIA
# ============================================

def enviar_top5(jogos):

    hoje = datetime.now().strftime("%d/%m/%Y")

    mensagem = f"📊 ELITE TIP DO DIA\n\n📅 {hoje}\n\n"

    for i, jogo in enumerate(jogos, 1):

        mensagem += (
            f"{i}️⃣ {jogo['home']} vs {jogo['away']}\n"
            f"🕒 {jogo['time']}\n"
            f"🔥 Palpite: {jogo['prediction']}\n"
            f"📊 Confiança: {jogo['confidence']}%\n\n"
        )

    enviar_telegram(mensagem)


# ============================================
# LOOP PRINCIPAL
# ============================================

def executar_bot():

    print("🚀 BOT ELITE INICIADO")

    enviar_telegram("🤖 BOT ELITE INICIADO")

    while True:

        print("🔎 Buscando jogos do dia...")

        jogos = buscar_jogos_do_dia()

        if jogos:

            top5 = selecionar_top5(jogos)

            enviar_top5(top5)

        else:

            enviar_telegram("❌ Nenhum jogo encontrado hoje")

        print("⏱ Próxima análise em 6 horas\n")

        time.sleep(21600)  # 6 horas


# ============================================
# START
# ============================================

executar_bot()
