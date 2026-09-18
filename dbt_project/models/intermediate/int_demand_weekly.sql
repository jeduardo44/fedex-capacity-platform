-- Business logic: aggregate demand across product categories per region/week
-- and attach the human-readable region name from the seed.

with demand as (

    select
        region,
        week_date,
        sum(packages) as total_packages,
        sum(case when product_category = 'express' then packages else 0 end)
            as express_packages
    from {{ ref('stg_weekly_demand') }}
    group by 1, 2

)

select
    d.region,
    coalesce(m.region_name, d.region) as region_name,
    d.week_date,
    d.total_packages,
    d.express_packages
from demand d
left join {{ ref('region_mapping') }} m
    on d.region = m.region_code
