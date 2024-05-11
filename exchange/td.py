from twelvedata import TDClient


td = TDClient(apikey = "375f5ab7748a4ddb807d4c810bae5cf2")


def get_price():

    aapl_price = td.price(symbol="AAPL").as_json()
    
    print(f"{float(aapl_price['price']):.1f}")
    
    
get_price()