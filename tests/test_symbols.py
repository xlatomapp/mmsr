from datetime import date

from mmsr.periods.symbols import KdbSymbolUniverseSource


class FakeKdbClient:
    def __init__(self) -> None:
        self.query = ""
        self.args = ()

    def execute(self, query: str, *args: object) -> dict[str, list[str]]:
        self.query = query
        self.args = args
        return {"sym": ["7203", "6758"]}


def test_kdb_symbol_universe_source_calls_configured_symbol_function() -> None:
    client = FakeKdbClient()
    source = KdbSymbolUniverseSource(
        client=client,
        function=".sb.mmsr.getSymbols",
    )

    result = source.symbols_for_day(date(2026, 5, 1))

    assert result == ["7203", "6758"]
    assert ".sb.mmsr.getSymbols[date]" in client.query
    assert client.args == (date(2026, 5, 1),)


def test_kdb_symbol_universe_source_accepts_vector_results() -> None:
    class VectorClient:
        def execute(self, query: str, *args: object) -> list[str]:
            return ["8306", "9984"]

    result = KdbSymbolUniverseSource(
        client=VectorClient(),
        function=".sb.mmsr.getSymbols",
    ).symbols_for_day(date(2026, 5, 1))

    assert result == ["8306", "9984"]
