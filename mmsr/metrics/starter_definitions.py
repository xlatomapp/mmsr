"""Starter metric definitions."""

from __future__ import annotations

from mmsr.metrics.base import MetricDefinition

STARTER_METRICS: list[MetricDefinition] = [
    MetricDefinition(
        name="turnover",
        label="Turnover",
        category="Activity",
        description=(
            "Summed traded notional at the selected aggregation grain "
            "(for example, per intraday bucket or per day)."
        ),
        formula="sum(tradePrice * tradeSize)",
        formula_latex=r"\sum_i \mathrm{price}_i \cdot \mathrm{qty}_i",
        interpretation="Higher turnover indicates more trading activity.",
        unit="JPY",
        higher_is_better=None,
        default_aggregation="sum",
        supports_intraday=True,
        supports_symbol_level=True,
        required_tables=["trades"],
        required_columns=["tradePrice", "tradeSize"],
        caveats=["Auction and off-market prints may need explicit filtering."],
    ),
    MetricDefinition(
        name="volume",
        label="Volume",
        category="Activity",
        description="Total traded shares over the selected period or bucket.",
        formula="sum(tradeSize)",
        formula_latex=r"\sum_i q_i",
        interpretation="Higher volume indicates more share trading activity.",
        unit="shares",
        higher_is_better=None,
        default_aggregation="sum",
        supports_intraday=True,
        supports_symbol_level=True,
        required_tables=["trades"],
        required_columns=["tradeSize"],
    ),
    MetricDefinition(
        name="trade_count",
        label="Trade Count",
        category="Activity",
        description="Number of trades over the selected period or bucket.",
        formula="count trades",
        formula_latex=r"N_{\mathrm{trades}}",
        interpretation="Higher trade count indicates more frequent trading.",
        unit="count",
        higher_is_better=None,
        default_aggregation="sum",
        supports_intraday=True,
        supports_symbol_level=True,
        required_tables=["trades"],
        required_columns=["trade_time"],
    ),
    MetricDefinition(
        name="quoted_spread_bps",
        label="Quoted Spread",
        category="Liquidity",
        description="Best ask minus best bid, normalized by mid price.",
        formula="10000 * (askPrice - bidPrice) / ((askPrice + bidPrice) / 2)",
        formula_latex=r"10000 \cdot \frac{\mathrm{ask}-\mathrm{bid}}{(\mathrm{ask}+\mathrm{bid})/2}",
        interpretation="Higher values usually indicate worse liquidity and higher immediate transaction cost.",
        unit="bps",
        higher_is_better=False,
        default_aggregation="median",
        supports_intraday=True,
        supports_symbol_level=True,
        required_tables=["quotes"],
        required_columns=["bidPrice", "askPrice"],
        caveats=["Can be distorted by stale, crossed, or locked quotes."],
    ),
    MetricDefinition(
        name="top_of_book_depth",
        label="Top-of-Book Depth",
        category="Liquidity",
        description="Visible size at the best bid and best ask, normalized by lot size.",
        formula="(bidSize + askSize) / lotSize",
        formula_latex=r"\frac{\mathrm{bidSize}+\mathrm{askSize}}{\mathrm{lot\_size}}",
        interpretation="Higher values usually indicate more immediately available liquidity.",
        unit="lots",
        higher_is_better=True,
        default_aggregation="median",
        supports_intraday=True,
        supports_symbol_level=True,
        required_tables=["quotes"],
        required_columns=["bidSize", "askSize", "lotSize"],
    ),
    MetricDefinition(
        name="parkinson_volatility_bps",
        label="Parkinson Vola",
        category="Liquidity",
        description="Parkinson volatility: range-based estimator derived from trade high-low ranges.",
        formula=(
            "10000 * sqrt((1 / (4 * log(2))) * (log(high/low))^2) "
            "where high=max(tradePrice), low=min(tradePrice)"
        ),
        formula_latex=(
            r"10000 \cdot \sqrt{\frac{1}{4\ln 2}\left(\ln\!\left(\frac{H}{L}\right)\right)^2}"
        ),
        interpretation=(
            "Higher values indicate wider intrabucket price ranges and potentially "
            "higher short-horizon market-state volatility."
        ),
        unit="bps",
        higher_is_better=False,
        default_aggregation="mean",
        supports_intraday=True,
        supports_symbol_level=True,
        required_tables=["trades"],
        required_columns=["tradePrice"],
        caveats=[
            "Sensitive to sparse trade updates in a bucket.",
            "Trade-based range can differ from executable quote-based range in thin names.",
        ],
    ),
]

PRIMARY_QUOTE_REVERSION_HORIZONS: tuple[tuple[str, str], ...] = (
    ("10ms", "+10ms Reversion"),
    ("100ms", "+100ms Reversion"),
    ("500ms", "+500ms Reversion"),
    ("1s", "+1s Reversion"),
    ("5s", "+5s Reversion"),
    ("10s", "+10s Reversion"),
)

for horizon, label in PRIMARY_QUOTE_REVERSION_HORIZONS:
    metric_safe_horizon = horizon.replace("ms", "ms").replace("s", "s")
    STARTER_METRICS.append(
        MetricDefinition(
            name=f"primary_quote_reversion_{metric_safe_horizon}_bps",
            label=label,
            category="Toxicity",
            description=(
                "Signed movement of the primary exchange mid price from the "
                f"prevailing mid before an aggressive venue trade to {horizon} "
                "after the trade."
            ),
            formula=("side * 10000 * (primary_mid[t + horizon] - primary_mid[t-]) / primary_mid[t + horizon]"),
            formula_latex=(
                r"\mathrm{side}\cdot 10000 \cdot \frac{\mathrm{mid}_{t+h}-\mathrm{mid}_{t^-}}{\mathrm{mid}_{t+h}}"
            ),
            interpretation=(
                "Positive values mean the primary mid moved in the aggressive "
                "trade direction, suggesting greater adverse selection or "
                "toxicity. Negative values mean the initial trade direction "
                "reverted at the selected horizon."
            ),
            unit="bps",
            higher_is_better=False,
            default_aggregation="notional_weighted_mean",
            supports_intraday=True,
            supports_symbol_level=True,
            required_tables=["pts_trades", "pts_quotes", "primary_quotes"],
            required_columns=[
                "time",
                "sym",
                "venue",
                "tradePrice",
                "tradeSize",
                "bidPrice",
                "askPrice",
            ],
            caveats=[
                "MMSR infers aggressor side per PTS venue and symbol from the matched prevailing PTS quote midpoint.",
                "Short horizons such as 10ms and 100ms are sensitive to timestamp synchronization and feed latency.",
                "Results should be filtered for stale, crossed, locked, or unavailable primary and PTS quotes.",
                "Small sample sizes by venue, symbol, or bucket should be flagged in the report.",
            ],
        )
    )
