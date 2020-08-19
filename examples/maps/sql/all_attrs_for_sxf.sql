with layer as (
    select *
    --from sxf_union('polygon')
    --from sxf_union('line')
    from sxf_union('point')
    )
select distinct layername, (regexp_split_to_array(all_attrs.attrs, ':'))[1] as key_attrs
from (
    select layername, attr1 as attrs
    from layer
    union
    select layername, attr2 as attrs
    from layer
    union
    select layername, attr3 as attrs
    from layer
    union
    select layername, attr4 as attrs
    from layer
    union
    select layername, attr5 as attrs
    from layer
    ) as all_attrs
    group by layername, key_attrs
    order by layername, key_attrs