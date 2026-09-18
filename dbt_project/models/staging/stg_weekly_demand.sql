-- Staging: 1:1 with the raw source, column renaming and type casting only.

select
    cast(region as varchar)            as region,
    cast(week as date)                 as week_date,
    cast(product_category as varchar)  as product_category,
    cast(packages as bigint)           as packages,
    _source_file,
    _ingested_at
from {{ source('raw', 'weekly_demand') }}
