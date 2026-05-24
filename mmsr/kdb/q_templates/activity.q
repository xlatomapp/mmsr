/ Activity metrics template.
/ Expected params:
/   `trades_table`
/   `date_filter`
/   `time_filter`
/   `bucket_expr`
/   `group_by`

select
    turnover: sum trade_price * trade_size,
    volume: sum trade_size,
    trade_count: count i
by date, time_bucket: {{ bucket_expr }}{{ group_by }}
from {{ trades_table }}
where {{ date_filter }}, {{ time_filter }}
