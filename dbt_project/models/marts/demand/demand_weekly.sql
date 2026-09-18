-- Mart: final weekly demand table consumed by dashboards and forecasting.
-- Convention: the time column in every mart is named period_date.

select
    region,
    region_name,
    week_date        as period_date,
    total_packages,
    express_packages
from {{ ref('int_demand_weekly') }}
