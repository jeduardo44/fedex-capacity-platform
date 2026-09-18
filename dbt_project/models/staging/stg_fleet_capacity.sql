-- Staging: 1:1 with the raw source, column renaming and type casting only.

select
    cast(hub as varchar)                as hub,
    cast(date as date)                  as capacity_date,
    cast(vehicle_type as varchar)       as vehicle_type,
    cast(vehicles_available as bigint)  as vehicles_available,
    cast(vehicles_used as bigint)       as vehicles_used,
    _source_file,
    _ingested_at
from {{ source('raw', 'fleet_capacity') }}
