from mmsr.config.models import (
    BrandingConfig,
    CalendarConfig,
    HtmlTemplateConfig,
    IntradayConfig,
    ReferenceComparisonConfig,
    ReportConfig,
    ToxicityConfig,
    ToxicityEventClusteringConfig,
    ToxicityFiltersConfig,
    ToxicityConfidenceConfig,
)


def test_report_config_supports_html_branding() -> None:
    config = ReportConfig(
        title="Daily Monitor",
        metrics=["quoted_spread_bps"],
        html=HtmlTemplateConfig(
            branding=BrandingConfig(
                brand_name="Example Securities",
                header_image_src="assets/header.png",
                footer_image_src="assets/footer.png",
            )
        ),
    )

    assert config.html.branding.brand_name == "Example Securities"
    assert config.html.branding.header_image_src == "assets/header.png"
    assert config.html.branding.footer_image_src == "assets/footer.png"


def test_report_config_defaults_to_kdb_calendar_and_auction_buckets() -> None:
    config = ReportConfig(title="Daily Monitor", metrics=["quoted_spread_bps"])

    assert isinstance(config.calendar, CalendarConfig)
    assert config.calendar.source == "kdb"
    assert isinstance(config.intraday, IntradayConfig)
    assert config.intraday.auction_buckets.enabled is True
    assert config.intraday.auction_buckets.morning_open == "AMO"
    assert config.intraday.auction_buckets.afternoon_close == "PMC"


def test_reference_comparison_config_defaults_to_daily_observation_unit() -> None:
    config = ReportConfig(title="Daily Monitor", metrics=["quoted_spread_bps"])

    assert isinstance(config.reference, ReferenceComparisonConfig)
    assert config.reference.observation_unit == "trading_day"
    assert config.reference.min_samples_for_z_score == 30
    assert config.reference.default_user_facing_score == "empirical_percentile"


def test_reference_comparison_config_validates_thresholds() -> None:
    try:
        ReferenceComparisonConfig(min_samples_for_z_score=1)
    except ValueError as exc:
        assert "min_samples_for_z_score" in str(exc)
    else:
        raise AssertionError("Expected invalid z-score sample threshold to fail")


def test_toxicity_config_defaults_match_reversion_report_contract() -> None:
    config = ReportConfig(
        title="Daily Monitor",
        metrics=["primary_quote_reversion_100ms_bps"],
    )

    assert isinstance(config.toxicity, ToxicityConfig)
    assert config.toxicity.section_title == "Cross-Venue Toxicity"
    assert config.toxicity.primary_venue == "TSE"
    assert config.toxicity.venues == ("TSE", "SBIJ", "ODX")
    assert config.toxicity.reversion_horizons == (
        "10ms",
        "100ms",
        "500ms",
        "1s",
        "5s",
        "10s",
    )
    assert config.toxicity.side_source == "feed"
    assert config.toxicity.filters.max_primary_quote_age == "1s"
    assert config.toxicity.confidence.min_trade_count == 100


def test_toxicity_config_validates_duration_side_and_primary_venue() -> None:
    for kwargs, expected in [
        ({"reversion_horizons": ["100milliseconds"]}, "reversion_horizons"),
        ({"side_source": "unknown"}, "side_source"),
        ({"primary_venue": "TSE", "venues": ["SBIJ"]}, "primary_venue"),
    ]:
        try:
            ToxicityConfig(**kwargs)
        except ValueError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError(f"Expected invalid toxicity config {kwargs!r} to fail")


def test_toxicity_nested_configs_validate_thresholds_and_durations() -> None:
    for factory, expected in [
        (
            lambda: ToxicityEventClusteringConfig(window="0ms"),
            "event_clustering.window",
        ),
        (
            lambda: ToxicityFiltersConfig(max_primary_quote_age="fresh"),
            "filters.max_primary_quote_age",
        ),
        (
            lambda: ToxicityConfidenceConfig(min_trade_count=0),
            "confidence.min_trade_count",
        ),
        (lambda: ToxicityConfidenceConfig(min_notional=-1), "confidence.min_notional"),
    ]:
        try:
            factory()
        except ValueError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError(
                f"Expected invalid nested toxicity config for {expected}"
            )


def test_toxicity_config_populates_metric_run_parameters() -> None:
    config = ReportConfig(
        title="Daily Monitor",
        metrics=["primary_quote_reversion_100ms_bps"],
        toxicity=ToxicityConfig(
            primary_venue="TSE",
            venues=["TSE", "SBIJ"],
            reversion_horizons=["100ms", "1s"],
            side_source="inferred",
            event_clustering=ToxicityEventClusteringConfig(
                enabled=False,
                window="250ms",
            ),
            filters=ToxicityFiltersConfig(
                exclude_auction=False,
                exclude_stale_primary_quote=True,
                max_primary_quote_age="500ms",
            ),
            confidence=ToxicityConfidenceConfig(
                min_trade_count=25,
                min_notional=50_000_000,
            ),
        ),
    )

    params = config.metric_parameters_for("primary_quote_reversion_100ms_bps")

    assert params == {
        "primary_venue": "TSE",
        "venues": ("TSE", "SBIJ"),
        "max_primary_quote_age": "500ms",
        "side_source": "inferred",
        "event_clustering_enabled": False,
        "event_clustering_window": "250ms",
        "exclude_auction": False,
        "exclude_stale_primary_quote": True,
        "min_trade_count": 25,
        "min_notional": 50_000_000,
    }
    assert config.toxicity.reversion_metric_names() == (
        "primary_quote_reversion_100ms_bps",
        "primary_quote_reversion_1s_bps",
    )
    assert config.metric_parameters_for("turnover") == {}
