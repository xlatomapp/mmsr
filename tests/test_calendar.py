from datetime import date

from mmsr.periods.calendar import KdbTradingCalendarSource, weekdays_between


class FakeKdbClient:
    def __init__(self) -> None:
        self.query = ""
        self.args = ()

    def execute(self, query: str, *args: object) -> dict[str, list[date]]:
        self.query = query
        self.args = args
        return {"date": [date(2026, 5, 1), date(2026, 5, 7)]}


def test_kdb_trading_calendar_source_queries_dedicated_calendar_table() -> None:
    client = FakeKdbClient()
    source = KdbTradingCalendarSource(client=client)

    result = source.trading_days(date(2026, 5, 1), date(2026, 5, 10))

    assert result == [date(2026, 5, 1), date(2026, 5, 7)]
    assert "from trading_calendar" in client.query
    assert "is_trading_day" in client.query
    assert client.args == (date(2026, 5, 1), date(2026, 5, 10))


def test_weekdays_between_is_available_for_offline_fixtures() -> None:
    result = weekdays_between(date(2026, 5, 1), date(2026, 5, 3))

    assert result == [date(2026, 5, 1)]
