import time
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pylab as pl
from IPython import display
from collections import deque
from binance.client import Client
from BinanceKeys import BinanceKeySecretPair

plt.ion()
fig=plt.figure()


api_key = BinanceKeySecretPair['api_key']
api_secret = BinanceKeySecretPair['api_secret']
client = Client(api_key, api_secret)


def get_symbol_to_index(tickers):
    map_symbol_to_index = {}
    for i in range(0, len(tickers)):
        map_symbol_to_index[tickers[i]['symbol']] = i
    return map_symbol_to_index


def get_potential_arbitrages(symbols, tickers):
    triangles = []

    seen_currencies = set()
    starting_currency = 'LTC'
    queue = deque([starting_currency])

    while len(queue) > 0:
        current_currency = queue.popleft()
        seen_currencies.add(current_currency)
        out_currencies = []

        for ticker in tickers:
            if ticker['symbol'].startswith(current_currency):
                out_currency = ticker['symbol'][len(current_currency):]
                out_currencies.append(out_currency)
                if out_currency not in seen_currencies:
                    queue.append(out_currency)

        for i in range(0, len(out_currencies)):
            for j in range(i+1, len(out_currencies)):
                forward_edge = out_currencies[i]+out_currencies[j]
                backward_edge = out_currencies[j]+out_currencies[i]

                if forward_edge in symbols:
                    triangle = [current_currency+out_currencies[j], current_currency+out_currencies[i], forward_edge]
                elif backward_edge in symbols:
                    triangle = [current_currency+out_currencies[i], current_currency+out_currencies[j], backward_edge]

                triangles.append(triangle)

    return triangles


def find_best_arbitrages(triangles, index_map, tickers):
    transaction_fee = 0.1
    max_return_list = np.array([])
    time_list = np.array([])

    iteration = 0
    while True:
        tickers = client.get_orderbook_tickers()

        max_return_rate =  -1000

        for triangle in triangles:
            rate1 = float(tickers[index_map[triangle[0]]]['askPrice'])
            rate2 = float(tickers[index_map[triangle[1]]]['bidPrice'])*float(tickers[index_map[triangle[2]]]['bidPrice'])
            if round(rate1, 7) == 0:
                continue

            return_rate = (rate2-rate1)/(rate1)*100.0 - transaction_fee*2

            if return_rate > max_return_rate:
                max_return_rate = return_rate
                print("Maximum: " + str(max_return_rate) + "% arbitrage from " + triangle[1] + "->" + triangle[2])

        max_return_list = np.append(max_return_list, max_return_rate)
        time_list = np.append(time_list, iteration)
        iteration += 1
        plt.plot(time_list, max_return_list,'b-*')
        plt.xlabel("Time (Seconds)", fontweight="bold")
        plt.ylabel("Net Return (%)", fontweight="bold")
        plt.title("Triangular Arbitrage Live Return Rate", fontweight="bold")
        plt.show()
        plt.grid()
        plt.pause(0.0001)
        time.sleep(1)
        plt.grid()


conversions = client.get_orderbook_tickers()
conversion_to_index = get_symbol_to_index(conversions)
symbol_list = conversion_to_index.keys()
arb_triangles = get_potential_arbitrages(symbol_list, conversions)
find_best_arbitrages(arb_triangles, conversion_to_index, conversions)
