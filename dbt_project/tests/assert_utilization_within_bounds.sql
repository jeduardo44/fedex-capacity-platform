-- Singular test: utilization must stay within a sane range.
-- Over 130% or negative means bad source data or a broken calculation.

select *
from {{ ref('capacity_daily') }}
where utilization_pct < 0
   or utilization_pct > 130
