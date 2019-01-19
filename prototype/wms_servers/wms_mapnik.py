# -*- coding: utf-8 -
from __future__ import absolute_import, unicode_literals
from django.http import QueryDict
import string
try:
    import mapnik
except ImportError:
    import mapnik2 as mapnik
from django.contrib.gis.gdal import SpatialReference, Envelope, OGRGeometry


wms_template = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE WMT_MS_Capabilities SYSTEM "http://schemas.opengis.net/wms/1.1.1/WMS_MS_Capabilities.dtd"
 [
 <!ELEMENT VendorSpecificCapabilities EMPTY>
 ]>  <!-- end of DOCTYPE declaration -->
<WMT_MS_Capabilities version="1.1.1">
<Service>
  <Name>OGC:WMS</Name>
  <Title>$title</Title>
  <Abstract></Abstract>
  <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href=""/>
  <Fees>none</Fees>
  <AccessConstraints>none</AccessConstraints>
</Service>
<Capability>
  <Request>
    <GetCapabilities>
      <Format>application/vnd.ogc.wms_xml</Format>
      <DCPType>
        <HTTP>
          <Get><OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="$url"/></Get>
        </HTTP>
      </DCPType>
    </GetCapabilities>
    <GetMap>
        <Format>image/png</Format>
      <DCPType>
        <HTTP>
          <Get><OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="$url"/></Get>
        </HTTP>
      </DCPType>
    </GetMap>
    <GetFeatureInfo>
      <Format>text/plain</Format>
      <Format>text/html</Format>
      <Format>application/vnd.ogc.gml</Format>
      <DCPType>
        <HTTP>
          <Get><OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="$url"/></Get>
        </HTTP>
      </DCPType>
    </GetFeatureInfo>
  </Request>
  <Exception>
    <Format>application/vnd.ogc.se_xml</Format>
    <Format>application/vnd.ogc.se_inimage</Format>
    <Format>application/vnd.ogc.se_blank</Format>
  </Exception>
  <Layer>
    <Title>$title</Title>
    <SRS>EPSG:4326</SRS>
    <LatLonBoundingBox minx="-180" miny="-89.999999" maxx="180" maxy="89.999999" />
    <BoundingBox SRS="EPSG:4326" minx="-180.0" miny="-90.0" maxx="180.0" maxy="90.0" />
    <Layer>
      <Name>$name</Name>
      <Title>$title</Title>
      <LatLonBoundingBox minx="$minx" miny="$miny" maxx="$maxx" maxy="$maxy" />
      <BoundingBox SRS="EPSG:4326" minx="$minx" miny="$miny" maxx="$maxx" maxy="$maxy" />
    </Layer>
  </Layer>
</Capability>
</WMT_MS_Capabilities>

"""


def get_wms_mapnik_response(query_string, mapnik_file, name, base_url, geom):
    data = QueryDict(query_string)
    if data.get('request') == 'GetCapabilities' or data.get('REQUEST') == 'GetCapabilities':
        templ = string.Template(wms_template)
        prms = {}
        prms['name'] = name
        prms['title'] = name
        prms['url'] = base_url
        env = geom.ogr.envelope
        prms['minx'] = str(env.min_x)
        prms['miny'] = str(env.min_y)
        prms['maxx'] = str(env.max_x)
        prms['maxy'] = str(env.max_y)
        #return source.extent.wkt, 'text/xml', False
        return templ.substitute(prms), 'text/xml', False
    height = data.get('HEIGHT') or data.get('height')
    width = data.get('WIDTH') or data.get('width')
    srs = data.get('SRS') or data.get('srs')
    bbox = data.get('BBOX') or data.get('bbox')
    transparent = data.get('TRANSPARENT', False) or data.get('transparent')
    #request = 'GetMap'
    #service = 'WMS'
    #version = '1.1.1'
    #format = 'image/jpeg' 'image/png'
    if not data or not height or not width or not srs or not bbox:
        raise Exception('Не найден один из обязательных атрибутов: data, height, width, srs, bbox')

    width = int(width)
    height = int(height)

    srs = SpatialReference(srs)

    m = mapnik.Map(width, height)
    mapnik.load_map(m, mapnik_file.encode('utf8'))   # TODO: проверить работу с кириллицей

    if transparent:
        m.background = mapnik.Color('transparent'.encode('utf8'))
    else:
        m.background = mapnik.Color('white'.encode('utf8'))

    prj1 = mapnik.Projection(str(srs.proj4))
    m.srs = prj1.params()

    bbox = [float(coord) for coord in bbox.split(',')]
    bbox = Envelope(bbox)
    bbox_polygon = OGRGeometry(bbox.wkt, srs=srs)
    map_bbox = mapnik.Box2d(*bbox_polygon.envelope.tuple)

    m.zoom_to_box(map_bbox)

    im = mapnik.Image(width, height)
    mapnik.render(m, im)
    content = im.tostring('png256'.encode('utf8'))
    content_type = 'image/png'
    error = False
    return content, content_type, error
