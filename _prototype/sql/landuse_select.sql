select way as geometry,
osm_id, 
concat(
    landuse, 
    "natural", 
    leisure
) as type, 
name as name 
from planet_osm_polygon 
where landuse in 
(
    'forest',
     'wood',
     'pedestrian',
     'cemetery',
     'industrial',
     'commercial',
     'brownfield',
     'residential',
     'school',
     'college',
     'university',
     'military',
     'park',
     'golf_course',
     'hospital',
     'parking',
     'stadium',
     'sports_center',
     'pitch'
) 
or "natural" in ('wood') 
or leisure in 
(
     'park',
     'golf_course' 
) 
order by area desc