
DROP FUNCTION sxf_union(text,text[],integer[]);
create or replace function sxf_union(
    geom_type text,
    layer_name text[],
    map_ids int[]
    )
returns table (
    gid integer,
    code integer,
    rsc_code integer,
    key character varying,
    name character varying,
    layername character varying,
    botscale integer,
    topscale integer,
    attr1 character varying,
    attr2 character varying,
    attr3 character varying,
    attr4 character varying,
    attr5 character varying,
    map_id integer,
    wkb_geometry geometry
) as $$
    declare
        all_tables text[];
        table_name text;
        query_array text[];
        query_str text;
    begin
        execute'
            select array_agg(table_name::text)
            from information_schema.tables
            where table_type=''BASE TABLE''
            and table_schema=''public''
            and (regexp_split_to_array(table_name, ''_''))[4] = '''||geom_type||''';'
        into all_tables;

        foreach table_name in array all_tables
        loop
            query_array := array_append(
                query_array,'
                select *
                from '||table_name||' as geodata
                where layername = any(array['''||array_to_string(layer_name,''',''')||'''])
                and map_id in (
                    select map_id 
                    from sxf_common_loaded_maps 
                    where external_id = any(array['||array_to_string(map_ids,',')||'])
                )
                '
            );
        end loop;
        query_str := array_to_string(query_array, 'union');
        
        return query execute query_str;
    end;
$$ language plpgsql