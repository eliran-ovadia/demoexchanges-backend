from exchange.schemas import RawQuote


def process_single_quote(raw_quote) -> dict:
    try:
        raw_quote_to_return = RawQuote(
            symbol = raw_quote['symbol'],
            full_name = raw_quote['name'],
            exchange = raw_quote['exchange'],
            currency = raw_quote['currency'],
            open = round(float(raw_quote['open']), 2),
            high = round(float(raw_quote['high']), 2),
            low = round(float(raw_quote['low']), 2),
            close = round(float(raw_quote['close']), 2),
            volume = int(raw_quote['volume']),
            change = round(float(raw_quote['change']), 2),
            percent_change = round(float(raw_quote['percent_change']), 2),
            avg_volume = int(raw_quote['average_volume']),
            year_range_high = round(float(raw_quote['fifty_two_week']['high']), 2),
            year_range_low = round(float(raw_quote['fifty_two_week']['low']), 2)
        ).model_dump()
        return raw_quote_to_return
    except ValueError as e:
        print(f"Error converting data for {raw_quote['symbol']}: {e}")
