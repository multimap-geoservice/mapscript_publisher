select st_extent(ST_Envelope(geom)), st_srid(geom)
from rasters
group by geom
limit 1