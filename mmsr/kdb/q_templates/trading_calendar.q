/ Trading calendar query template.
/ Production implementations should bind start/end as parameters rather than
/ interpolating unchecked values into q strings.
/ Expected output column: date

select {{ date_column }} from {{ table }}
where {{ date_column }} within (start;end), {{ is_trading_day_column }}
