with
    --ids as (
    --    select map_id
    --    from sxf_common_loaded_maps
    --    where external_id in (9511,9512,9513,9514,9515,9516,9517,9518,9519,9520,9521,9522,9523,9524,9525,9526,9527,9528,9529,9530)
    --),
    objs as (
        select rsc_code+code+gid as id,
               name as type,
               array[
                   (regexp_split_to_array(attr1, ':'))[1],
                   (regexp_split_to_array(attr2, ':'))[1],
                   (regexp_split_to_array(attr3, ':'))[1],
                   (regexp_split_to_array(attr4, ':'))[1],
                   (regexp_split_to_array(attr5, ':'))[1]
               ] as attr_keys,
               array[
                   (regexp_split_to_array(attr1, ':'))[2],
                   (regexp_split_to_array(attr2, ':'))[2],
                   (regexp_split_to_array(attr3, ':'))[2],
                   (regexp_split_to_array(attr4, ':'))[2],
                   (regexp_split_to_array(attr5, ':'))[2]
               ] as attr_vals,
               wkb_geometry as geometry,
               '[^a-zA-Zа-яА-ЯёЁ0-9 .,-]*|' as sym_bug
        from (
            select *
            from sxf_union(
                 'polygon',
                 --'line',
                 --'point',
                 --array['ГИДРОГРАФИЯ'],
                 array[
                     'ПРОМЫШЛЕН.И СОЦИАЛЬНЫЕ ОБЪЕКТЫ',
                     'ПРОМЫШЛЕН.И СОЦИАЛЬНЫЕ ОБ''''ЕКТ',
                     'ПРОМЫШЛЕННЫЕ,СОЦИАЛЬН. ОБ''''ЕКТЫ',
                     'ПРОМЫШЛЕННЫЕ,СОЦИАЛЬН.ОБ''''ЕКТЫ'
                 ],
                 array[9511,9512,9513,9514,9515,9516,9517,9518,9519,9520,9521,9522,9523,9524,9525,9526,9527,9528,9529,9530]
            )
            --select *
            --from sxf_common_50000_polygon
            --from sxf_common_200000_polygon
            --where layername = any(array['ГИДРОГРАФИЯ','ЖД'])
            --and map_id in (select map_id from ids)
            --union
            --select *
            --from sxf_common_100000_polygon
            --where layername = any(array['ГИДРОГРАФИЯ','ЖД'])
            --and map_id in (select map_id from ids)
            --union
            --select *
            --from sxf_common_1000000_polygon
            --where layername = any(array['ГИДРОГРАФИЯ','ЖД'])
            --and map_id in (select map_id from ids)
        ) as unions
        group by id,
            name,
            attr1,
            attr2,
            attr3,
            attr4,
            attr5,
            wkb_geometry,
            sym_bug
    )
select id,
       type,
       case
           when array_position(attr_keys,'СОБСТВЕН.НАЗВАН.,ТЕКСТ ПОДПИС') > 0 then regexp_replace(attr_vals[array_position(attr_keys,'СОБСТВЕН.НАЗВАН.,ТЕКСТ ПОДПИС')], E''||sym_bug,'', 'g')
           when array_position(attr_keys,'СОБСТВЕН.НАЗВАН.(ТЕКСТ ПОДПИСИ)') > 0 then regexp_replace(attr_vals[array_position(attr_keys,'СОБСТВЕН.НАЗВАН.(ТЕКСТ ПОДПИСИ)')], E''||sym_bug,'', 'g')
           when array_position(attr_keys,'СОБСТВЕН.НАЗВ.(ТЕКСТ ПОДПИСИ)') > 0 then regexp_replace(attr_vals[array_position(attr_keys,'СОБСТВЕН.НАЗВ.(ТЕКСТ ПОДПИСИ)')], E''||sym_bug,'', 'g')
           when array_position(attr_keys,'СОБСТВЕННОЕ НАЗВАНИЕ') > 0 then regexp_replace(attr_vals[array_position(attr_keys,'СОБСТВЕННОЕ НАЗВАНИЕ')], E''||sym_bug,'', 'g')        
           else null
       end as name,
       case
           when array_position(attr_keys,'ПРИЗНАК СУДОХОДСТВА') > 0 then regexp_replace(attr_vals[array_position(attr_keys,'ПРИЗНАК СУДОХОДСТВА')], E''||sym_bug||'КОД','', 'g')
           else null
       end as shipping,
       case
           when array_position(attr_keys,'ТИП ВОДОТОКА,БЕРЕГОВОЙ ЛИНИИ') > 0 then regexp_replace(attr_vals[array_position(attr_keys,'ТИП ВОДОТОКА,БЕРЕГОВОЙ ЛИНИИ')], E''||sym_bug||'КОД','', 'g')
           when array_position(attr_keys,'ТИП ВОДОТОКА (ВОДОЕМА)') > 0 then regexp_replace(attr_vals[array_position(attr_keys,'ТИП ВОДОТОКА (ВОДОЕМА)')], E''||sym_bug||'КОД','', 'g')
           else null
       end as watercourse,
       case
           when array_position(attr_keys,'КАЧЕСТВЕННЫЕ ОСОБЕННОСТИ ВОДЫ') > 0 then regexp_replace(attr_vals[array_position(attr_keys,'КАЧЕСТВЕННЫЕ ОСОБЕННОСТИ ВОДЫ')], E''||sym_bug||'КОД','', 'g')
           else null
       end as quality,
       geometry
from objs
