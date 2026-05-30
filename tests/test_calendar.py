from datetime import date

from mmsr.periods.calendar import KdbTradingCalendarSource, weekdays_between


class FakeKdbClient:
    def __init__(self) -> None:
        self.queries: list[str] = []
        self.args_by_query: list[tuple[object, ...]] = []

    @property
    def query(self) -> str:
        return self.queries[-1]

    @property
    def args(self) -> tuple[object, ...]:
        return self.args_by_query[-1]

    def execute(self, query: str, *args: object) -> dict[str, list[date]]:
        self.queries.append(query)
        self.args_by_query.append(args)
        return {"date": [date(2026, 5, 1), date(2026, 5, 7)]}


def test_kdb_trading_calendar_source_calls_configured_calendar_function() -> None:
    client = FakeKdbClient()
    source = KdbTradingCalendarSource(
        client=client,
        function=".sb.mmsr.getTradingCalendar",
    )

    result = source.trading_days(date(2026, 5, 1), date(2026, 5, 10))

    assert result == [date(2026, 5, 1), date(2026, 5, 7)]
    assert len(client.queries) == 1
    assert ".sb.mmsr.getTradingCalendar[start;end]" in client.query
    assert client.args == (date(2026, 5, 1), date(2026, 5, 10))


def test_weekdays_between_is_available_for_offline_fixtures() -> None:
    result = weekdays_between(date(2026, 5, 1), date(2026, 5, 3))

    assert result == [date(2026, 5, 1)]
