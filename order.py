import time
from binance.client import Client
from binance.enums import *
import config

# Configuração do cliente Binance
TRADE_SYMBOL = 'PEPEBRL'  # Par de negociação
TRADE_QUANTITY = 100000      # Quantidade para comprar/vender

# Inicializar o cliente da Binance
client = Client(config.API_KEY, config.API_SECRET, tld='com')

try:
    symbol_info = client.get_symbol_ticker(symbol="PEPEBRL")
    print(symbol_info)
except Exception as e:
    print(f"Erro ao consultar símbolo: {e}")

symbol_info = client.get_symbol_info('PEPEBRL')
print(symbol_info)

# Função para criar ordens de compra/venda
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

# Testar ordens de venda e compra
def main():
    print("Iniciando teste de compra e venda...")
    
    # Teste de venda
    print("Teste de venda:")
    sell_success = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
    if sell_success:
        print("Venda realizada com sucesso!")
    else:
        print("Erro ao realizar venda.")
    
    # Pausa para evitar problemas de ordem consecutiva
    time.sleep(2)
    
    
    print("Teste de compra:")
    buy_success = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
    if buy_success:
        print("Compra realizada com sucesso!")
    else:
        print("Erro ao realizar compra.")

if __name__ == "__main__":
    main()
