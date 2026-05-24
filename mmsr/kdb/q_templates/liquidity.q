/ Liquidity metrics template.
/ Expected params:
/   `quotes_table`
/   `date_filter`
/   `time_filter`
/   `bucket_expr`
/   `group_by`

select
    quoted_spread_bps: med 10000 * (ask_price - bid_price) % ((ask_price + bid_price) % 2),
    top_of_book_depth: med bid_size + ask_size
by date, time_bucket: {{ bucket_expr }}{{ group_by }}
from {{ quotes_table }}
where {{ date_filter }}, {{ time_filter }}, bid_price > 0, ask_price > bid_price
