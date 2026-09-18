-- Business logic: aggregate capacity across vehicle types per hub/day
-- and compute utilization.

select
    c.hub,
    coalesce(h.region_code, 'UNKNOWN') as region,
    c.capacity_date,
    sum(c.vehicles_available)          as total_available,
    sum(c.vehicles_used)               as total_used,
    round(
        100.0 * sum(c.vehicles_used) / nullif(sum(c.vehicles_available), 0),
        2
    )                                  as utilization_pct
from {{ ref('stg_fleet_capacity') }} c
left join {{ ref('hub_regions') }} h
    on c.hub = h.hub
group by 1, 2, 3
