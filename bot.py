import websocket
import json
import pprint
import talib
import numpy
import time
from binance.client import Client
from binance.enums import *
import config
import signal  # Biblioteca para capturar sinais, como Ctrl+C

# Configuração do WebSocket e API REST
SOCKET = "wss://stream.binance.com:9443/ws/pepebrl@kline_1m"
RSI_PERIOD = 10          # Período do RSI
RSI_OVERBOUGHT = 72      # Nível de sobrecompra ajustado
RSI_OVERSOLD = 28        # Nível de sobrevenda ajustado
TRADE_SYMBOL = 'PEPEBRL'
MIN_NOTIONAL = 12  # Valor mínimo (em BRL)
closing_prices = []  # Nome mais descritivo para a lista de preços de fechamento
in_position = False
should_exit = False  # Variável para controlar o loop
ws = None  # Variável global para o WebSocket

# Configurar cliente da Binance
client = Client(config.API_KEY, config.API_SECRET, tld='com')

try:
    symbol_info = client.get_symbol_ticker(symbol="PEPEBRL")
    print(symbol_info)
except Exception as e:
    print(f"Erro ao consultar símbolo: {e}")

# Função para calcular a quantidade baseada no preço atual e minNotional
def calculate_quantity(price, min_notional=MIN_NOTIONAL):
    quantity = min_notional / price
    return round(quantity, 0)

# Função para criar ordens
def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print(f"Enviando ordem {side} de {quantity} {symbol}")
        order = client.create_order(
            symbol=symbol,
            side=side,
            type=order_type,
            quantity=quantity
        )
        print("Ordem enviada com sucesso:", order)
        return True
    except Exception as e:
        print(f"Ocorreu um erro ao enviar a ordem: {e}")
        return False

# Eventos do WebSocket
def on_open(ws):
    print('Conexão aberta')

def on_close(ws):
    print('Conexão fechada')

def on_message(ws, message):
    global closing_prices, in_position
    print('Mensagem recebida')
    json_message = json.loads(message)
    pprint.pprint(json_message)

    candle = json_message['k']
    is_candle_closed = candle['x']
    closing_price = float(candle['c'])  # Convertendo para float

    if is_candle_closed:
        print(f"Vela fechada em {closing_price}")
        closing_prices.append(closing_price)
        print("Preços de fechamento:", closing_prices)

        if len(closing_prices) > RSI_PERIOD:
            np_closing_prices = numpy.array(closing_prices)
            rsi = talib.RSI(np_closing_prices, RSI_PERIOD)
            print("RSI calculado:", rsi)
            last_rsi = rsi[-1]
            print(f"Último RSI: {last_rsi}")

            # Lógica de sobrecompra (vender)
            if last_rsi > RSI_OVERBOUGHT:
                if in_position:
                    print("Condição de venda atingida - enviando ordem de venda")
                    quantity = calculate_quantity(closing_price)  # Calcular quantidade baseada no preço atual
                    order_success = order(SIDE_SELL, quantity, TRADE_SYMBOL)
                    if order_success:
                        in_position = False
                else:
                    print("Já estamos fora da posição, nada a fazer")

            # Lógica de sobrevenda (comprar)
            elif last_rsi < RSI_OVERSOLD:
                if in_position:
                    print("RSI em sobrevenda, mas já estamos na posição")
                else:
                    print("Condição de compra atingida - enviando ordem de compra")
                    quantity = calculate_quantity(closing_price)  # Calcular quantidade baseada no preço atual
                    order_success = order(SIDE_BUY, quantity, TRADE_SYMBOL)
                    if order_success:
                        in_position = True

# Função para lidar com sinal de interrupção (Ctrl+C)
def signal_handler(sig, frame):
    global should_exit, ws
    print('Interrupção detectada! Encerrando...')
    should_exit = True
    if ws is not None:
        ws.close()  # Fechar a conexão WebSocket de forma segura

# Registrar o manipulador de sinal para Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

# Configuração e execução do WebSocket com loop de controle
while not should_exit:
    try:
        ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
        ws.run_forever()
    except Exception as e:
        print(f"Erro na conexão WebSocket: {e}. Tentando reconectar...")
        time.sleep(5)

print("Script encerrado.")
