from src.exchange.external_client_handlers.client_requests import get_market_movers


class MarketMoversManager: # Instead of saving to the db, market movers will stay in RAM.

    movers = None
    last_updated = None
    stocks = None


    @classmethod
    def update_market_movers(cls):
        cls.movers = get_market_movers()
        cls.last_updated = cls.movers.get('last_updated', '')
        cls.stocks = cls.movers.get('stocks', '')

    @classmethod
    def get_market_movers(cls):
        return cls.movers
