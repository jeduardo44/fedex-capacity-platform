-- Mart: final daily capacity table consumed by dashboards and forecasting.
-- Convention: the time column in every mart is named period_date.

select
    hub,
    region,
    capacity_date    as period_date,
    total_available,
    total_used,
    utilization_pct
from {{ ref('int_capacity_daily') }}
