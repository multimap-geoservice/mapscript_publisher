# -*- coding: utf-8 -
from __future__ import unicode_literals
import mapscript


def get_raster_layer(data, name, group, crs=None):
    """
    Mapscript Layer для растра.
    """
    layer = mapscript.layerObj()
    layer.type = mapscript.MS_LAYER_RASTER
    layer.status = mapscript.MS_ON   # mapscript.MS_DEFAULT
    layer.name = name
    layer.group = group
    layer.data = data
    layer.setProjection(crs or "AUTO")
    layer.metadata.set('wms_srs', 'AUTO EPSG:4326')
    layer.metadata.set('wms_title', name)
    # layer.setExtent({'minx': 3, 'miny': 3, 'maxx': 3, 'maxy': 3})
    # layer.setExtent(1, 2, 3, 4)
    # layer.setProjection('EPSG:4326')
    # layer.setProcessing("SCALE=0,255")
    # layer.setProcessing("DITHER=YES")
    # layer.setProcessing("RESAMPLE=BILINEAR")   # BILINEAR, AVERAGE, NEAREST
    # layer.setProcessing("EXTENT_PRIORITY=WORLD")
    # layer.setProcessing("LOAD_FULL_RES_IMAGE=NO")
    # layer.setProcessing("LOAD_WHOLE_IMAGE=NO")
    return layer


def get_vector_layer(data, name, group, crs=None):
    """
    Mapscript Layer для векторных данных.
    """
    layer = mapscript.layerObj()
    layer.type = mapscript.MS_LAYER_POLYGON
    layer.status = mapscript.MS_ON   # mapscript.MS_DEFAULT
    layer.name = name
    layer.group = group
    layer.setProjection('EPSG:4326')
    layer.metadata.set('wms_srs', 'EPSG:4326')
    layer.metadata.set('wms_title', name)
    for polygon in data:
        shape = mapscript.shapeObj_fromWKT(polygon.wkt)
        layer.addFeature(shape)
    # layer.setExtent({'minx': 3, 'miny': 3, 'maxx': 3, 'maxy': 3})
    # layer.setExtent(1, 2, 3, 4)
    # layer.setProjection('EPSG:4326')
    # layer.setProcessing("SCALE=0,255")
    # layer.setProcessing("DITHER=YES")
    # layer.setProcessing("RESAMPLE=BILINEAR")   # BILINEAR, AVERAGE, NEAREST
    # layer.setProcessing("EXTENT_PRIORITY=WORLD")
    # layer.setProcessing("LOAD_FULL_RES_IMAGE=NO")
    # layer.setProcessing("LOAD_WHOLE_IMAGE=NO")
    c = mapscript.classObj(layer)
    style = mapscript.styleObj(c)
    fill_color = mapscript.colorObj(0, 255, 0)
    out_color = mapscript.colorObj(0, 0, 255)
    style.color = fill_color
    style.outlinecolor = out_color
    style.opacity = 50
    layer.opacity = 50
    return layer


def get_pg_layer(data, name, group, connection, query_filter=None, crs=None, fill_color=None,
                 out_color=None, opacity=None):
    """
    Mapscript Layer для векторных данных, хранящихся в Postgres.
    """
    layer = mapscript.layerObj()
    layer.type = mapscript.MS_LAYER_POLYGON
    layer.status = mapscript.MS_ON   # mapscript.MS_DEFAULT
    layer.name = name
    layer.group = group
    layer.setProjection('EPSG:4326')
    layer.metadata.set('wms_srs', 'EPSG:4326')
    layer.metadata.set('wms_title', name)
    layer.connectiontype = mapscript.MS_POSTGIS
    layer.connection = connection
    layer.data = data   # "geom from data"
    # status = layer.setFilter(query_filter)  # "id = 123"
    # layer.setExtent({'minx': 3, 'miny': 3, 'maxx': 3, 'maxy': 3})
    # layer.setExtent(1, 2, 3, 4)
    # layer.setProjection('EPSG:4326')
    # layer.setProcessing("SCALE=0,255")
    # layer.setProcessing("DITHER=YES")
    # layer.setProcessing("RESAMPLE=BILINEAR")   # BILINEAR, AVERAGE, NEAREST
    # layer.setProcessing("EXTENT_PRIORITY=WORLD")
    # layer.setProcessing("LOAD_FULL_RES_IMAGE=NO")
    # layer.setProcessing("LOAD_WHOLE_IMAGE=NO")
    c = mapscript.classObj(layer)
    style = mapscript.styleObj(c)
    if fill_color:
        fill_color = mapscript.colorObj(*fill_color)
        style.color = fill_color
    if out_color:
        out_color = mapscript.colorObj(*out_color)
        style.outlinecolor = out_color
    if opacity:
        # style.opacity = opacity
        layer.opacity = opacity
    return layer


def get_output_format(format_type='png'):
    """
    Output format (png или geotiff)
    """
    out = None
    if format_type == 'png':
        out = mapscript.outputFormatObj('GD/PNG'.encode('utf8'))
        out.name = 'png'
        out.mimetype = 'image/png'
        out.driver = 'AGG/PNG'
        out.extension = 'png'
        out.imagemode = mapscript.MS_IMAGEMODE_RGBA
        out.transparent = mapscript.MS_TRUE
        # out.setOption('INTERLACE', 'OFF')
        # out.setOption('QUANTIZE_FORCE', 'OFF')
        # out.setOption('QUANTIZE_DIRTHER', 'OFF')
        # out.setOption('QUANTIZE_COLORS', '256')
    elif format_type == 'geotiff':
        out = mapscript.outputFormatObj('GDAL/GTiff'.encode('utf8'), 'gtiff'.encode('utf8'))
        out.name = 'GTiff'
        out.mimetype = 'image/tiff'
        out.driver = 'GDAL/GTiff'
        out.extension = 'tif'
        out.imagemode = mapscript.MS_IMAGEMODE_INT16
        out.transparent = mapscript.MS_FALSE
    return out


def get_web(projections, url):
    web = mapscript.webObj()
    web.metadata.set('wms_title', 'Геопространственный банк данных'.encode('utf8'))
    #map_obj.web.metadata.set('wms_onlineresource', 'http://localhost/cgi-bin/osm_water_line')   # TODO
    #raster_map.web.metadata.set('wms_srs',  ' '.join([proj_name for proj_name in PROJS]))
    web.metadata.set('wms_srs', projections)
    web.metadata.set('wms_abstract', 'Геопространственный банк данных'.encode('utf8'))
    web.metadata.set('wms_enable_request', '*')
    web.metadata.set('wms_encoding', 'utf-8')
    web.metadata.set('wms_onlineresource', url)   # TODO
    web.metadata.set('wms_bbox_extended', mapscript.MS_TRUE)
    return web


def get_map(base_url, out_format, layers, group):
    projections = 'EPSG:4326'   # TODO: вынести в аргументы

    # Map
    map_obj = mapscript.mapObj()
    # map_obj.debug = mapscript.MS_FALSE   # mapscript.MS_ON
    map_obj.debug = mapscript.MS_TRUE
    map_obj.name = 'RASTER'

    # Projection
    map_obj.setProjection('EPSG:4326')

    # Output format
    if out_format == 'png':
        format = map_obj.getOutputFormatByName('png')
        format.name = 'png'
        format.mimetype = 'image/png'
        format.driver = 'AGG/PNG'
        format.extension = 'png'
        format.imagemode = mapscript.MS_IMAGEMODE_RGBA
        format.transparent = mapscript.MS_TRUE
        # format.setOption('INTERLACE', 'OFF')
        # format.setOption('QUANTIZE_FORCE', 'OFF')
        # format.setOption('QUANTIZE_DITHER', 'OFF')
        # format.setOption('QUANTIZE_COLORS', '256')
        map_obj.setOutputFormat(format)
        map_obj.setImageType('png')

    elif out_format == 'geotiff':
        format = map_obj.getOutputFormatByName('GTiff')
        format.imagemode = mapscript.MS_IMAGEMODE_FLOAT32
        format.transparent = mapscript.MS_FALSE
        map_obj.setOutputFormat(format)
        map_obj.setImageType('GTiff')
    else:
        raise ValueError("Format not supported")
    # Web
    #map_obj.web = get_web(projections, base_url)
    map_obj.web.metadata.set('wms_title', 'Геопространственный банк данных'.encode('utf8'))
    #map_obj.web.metadata.set('wms_onlineresource', 'http://localhost/cgi-bin/osm_water_line')   # TODO
    #raster_map.web.metadata.set('wms_srs',  ' '.join([proj_name for proj_name in PROJS]))
    map_obj.web.metadata.set('wms_srs', projections)
    map_obj.web.metadata.set('wms_abstract', 'Геопространственный банк данных'.encode('utf8'))
    map_obj.web.metadata.set('wms_enable_request', '*')
    map_obj.web.metadata.set('wms_encoding', 'utf-8')
    map_obj.web.metadata.set('wms_onlineresource', base_url)   # TODO
    map_obj.web.metadata.set('wms_bbox_extended', 'true')

    # Layers
    for layer in layers:
        layer_type = layer['layer_type']
        layer_name = layer['name']
        layer_data = layer['data']
        layer_crs = layer['crs']
        layer_extra = layer.get('extra', {})
        if layer_type == 'raster':
            layer = get_raster_layer(data=layer_data, name=layer_name, group=group, crs=layer_crs)
        # elif layer_type == 'vector':
        #     layer = get_vector_layer(data=layer_data, name=layer_name, group=group, crs=layer_crs)
        elif layer_type == 'pg':
            layer_style = layer_extra.get('style', {})
            layer = get_pg_layer(data=layer_data, name=layer_name, group=group,
                                 connection=layer_extra.get('connection'),
                                 query_filter=layer_extra.get('query_filter'), crs=layer_crs,
                                 fill_color=layer_style.get('fill_color'),
                                 out_color=layer_style.get('out_color'),
                                 opacity=layer_style.get('opacity'))
        else:
            layer = None
        if layer:
            map_obj.insertLayer(layer)

    return map_obj


def get_wms_request(query_string, layer_names):
    req = mapscript.OWSRequest()
    req.loadParamsFromURL(query_string)
    req.setParameter('service', 'wms')
    req.setParameter('layers', ','.join(set(layer_names)))
    return req


# def get_wms_response(query_string, layer_name, data, base_url, out_format, layer_crs, layer_type,
# extra=None):
def get_wms_response(query_string, base_url, out_format, layers):
    group = 'raster_layers'
    layer_names = []
    for layer in layers:
        name = layer.get('name')
        if name:
            layer_names.append(name)
    req = get_wms_request(query_string=query_string, layer_names=layer_names)
    src_map = get_map(base_url=base_url, out_format=out_format, layers=layers, group=group)
    # raise ValueError(src_map.outputformat.imagemode, mapscript.MS_IMAGEMODE_INT16)
    mapscript.msIO_installStdoutToBuffer()
    try:
        src_map.OWSDispatch(req)
        error = False
    except mapscript.MapServerError:
        error = True
    content_type = mapscript.msIO_stripStdoutBufferContentType()
    content = mapscript.msIO_getStdoutBufferBytes()
    mapscript.msIO_resetHandlers()

    # if content_type == 'vnd.ogc.se_xml':
    #     content_type = 'text/xml'
    return content, content_type, error
