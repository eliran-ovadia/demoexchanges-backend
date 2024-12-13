import threading


class MarketMoversManager:  # Instead of saving to the db, market movers will stay in RAM.

    movers = None
    last_updated = None
    stocks = None
    _lock = threading.Lock()

    @classmethod
    def update_market_movers(cls):
        pass
        # with cls._lock:
        #     cls.movers = get_market_movers()
        #     cls.last_updated = cls.movers.get('last_updated', '')
        #     cls.stocks = cls.movers.get('stocks', '')

    @classmethod
    def get_market_movers(cls):
        with cls._lock:
            return cls.movers
