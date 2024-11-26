
import streamlit as st
import time
from binance.client import Client
import plotly.graph_objects as go
import talib
import numpy
import config
import datetime
import os
import subprocess

# Configuração do cliente Binance
TRADE_SYMBOL = 'PEPEBRL'
RSI_PERIOD = 10
RSI_OVERBOUGHT = 72
RSI_OVERSOLD = 28
MIN_NOTIONAL = 12  # Valor mínimo (em BRL)
client = Client(config.API_KEY, config.API_SECRET, tld='com')

# Função para buscar dados de velas (candlesticks)
def get_candlestick_data(symbol, interval='1m', limit=50):
    try:
        candles = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        data = []
        for candle in candles:
            data.append({
                'time': datetime.datetime.fromtimestamp(candle[0] / 1000),
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4])
            })
        return data
    except Exception as e:
        st.error(f"Erro ao buscar dados de velas: {e}")
        return []

# Função para analisar sinais de compra/venda usando RSI
def analyze_signals_with_rsi(candles):
    close_prices = [c['close'] for c in candles]
    if len(close_prices) < RSI_PERIOD:
        return None, None

    # Calcular RSI usando talib
    np_closing_prices = numpy.array(close_prices)
    rsi = talib.RSI(np_closing_prices, RSI_PERIOD)
    last_rsi = rsi[-1]

    signal = None
    if last_rsi > RSI_OVERBOUGHT:
        signal = f" - Sobrecomprado: Considere vender!"
    elif last_rsi < RSI_OVERSOLD:
        signal = f" - Sobrevendido: Considere comprar!"
    else:
        signal = f" - Neutro: Aguardando melhores condições."

    return signal, close_prices[-1]

# Função para calcular a quantidade baseada no preço atual e minNotional
def calculate_quantity(price, min_notional=MIN_NOTIONAL):
    quantity = min_notional / price
    return round(quantity, 0)

# Função para realizar compra
def buy(symbol, quantity):
    try:
        order = client.order_market_buy(symbol=symbol, quantity=quantity)
        return f"Ordem de compra executada: {order}"
    except Exception as e:
        return f"Erro ao executar ordem de compra: {e}"

# Função para realizar venda
def sell(symbol, quantity):
    try:
        order = client.order_market_sell(symbol=symbol, quantity=quantity)
        return f"Ordem de venda executada: {order}"
    except Exception as e:
        return f"Erro ao executar ordem de venda: {e}"

# Configuração do Streamlit
st.title("Dashboard de Trading - PEPEBRL")
st.subheader("Gráfico de Velas com RSI e Sinais de Compra/Venda")

# Configurações de intervalo e limite
interval = '1m'
limit = 50

# Marcadores de espaço dinâmicos
placeholder_graph = st.empty()
placeholder_signal = st.empty()

# Sidebar fixa para ações
st.sidebar.header("Saldo da Conta")
try:
    balances = client.get_account()['balances']
    for balance in balances:
        free_balance = float(balance['free'])
        if free_balance > 0:
            st.sidebar.write(f"{balance['asset']}: {free_balance:.6f}")
except Exception as e:
    st.sidebar.error(f"Erro ao buscar saldo: {e}")

# Ações de trading fixas na sidebar
st.sidebar.header("Ações de Trading")
buy_action = st.sidebar.button("Comprar", key="buy_button")
sell_action = st.sidebar.button("Vender", key="sell_button")

# Botão para análise automática
if st.sidebar.button("Operação Automática", key="analyze_button"):
    # Iniciar o bot em um novo terminal
    try:
        if os.name == 'nt':  # Windows
            subprocess.Popen(['start', 'cmd', '/k', 'python bot.py'], shell=True)
        else:  # Linux ou MacOS
            subprocess.Popen(['gnome-terminal', '--', 'python3', 'bot.py'])
        st.sidebar.success("Análise automática iniciada em um novo terminal!")
    except Exception as e:
        st.sidebar.error(f"Erro ao iniciar análise automática: {e}")

# Loop principal para atualização automática
while True:
    # Obter dados de velas
    candles = get_candlestick_data(TRADE_SYMBOL, interval=interval, limit=limit)

    # Analisar sinais com RSI
    signal, last_price = analyze_signals_with_rsi(candles)

    # Renderizar gráfico
    if candles:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=[c['time'] for c in candles],
            open=[c['open'] for c in candles],
            high=[c['high'] for c in candles],
            low=[c['low'] for c in candles],
            close=[c['close'] for c in candles]
        ))
        formatted_price = f"{last_price:.12f}"
        fig.update_layout(
            title=f"Gráfico de Velas - {TRADE_SYMBOL} (RSI baseado em {RSI_PERIOD} períodos) - Preço Atual: R${formatted_price}",
            xaxis_title="Tempo",
            yaxis_title="Preço",
            template="plotly_dark"
        )
        # Atualize o gráfico dinamicamente
        placeholder_graph.plotly_chart(fig)

    # Exibir sinal de compra/venda com RSI
    if signal:
        placeholder_signal.subheader(f"Sinal: {signal}")

    # Ações de compra/venda fora do loop para evitar duplicação de keys
    if buy_action:
        quantity = calculate_quantity(last_price)
        result = buy(TRADE_SYMBOL, quantity)
        st.sidebar.success(result)
    if sell_action:
        quantity = calculate_quantity(last_price)
        result = sell(TRADE_SYMBOL, quantity)
        st.sidebar.success(result)

    # Atualizar a cada minuto
    time.sleep(60)
