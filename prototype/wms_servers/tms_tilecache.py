# -*- coding: utf-8 -
from __future__ import unicode_literals

from TileCache.Layers.GDAL import GDAL
from TileCache.Layers.Image import Image as TileCacheImage
from TileCache.Layer import Tile, MetaLayer

from osgeo import gdal
import osgeo.gdal_array as gdalarray

from PIL import Image

import numpy

import StringIO


class FixedImage(TileCacheImage):
    """
    Создание тайлов с помощью PIL.
    """

    def renderTile(self, tile):
        import PIL.Image as PILImage

        bounds = tile.bounds()
        size = tile.size()
        min_x = int((bounds[0] - self.filebounds[0]) / self.image_res[0])
        min_y = int((self.filebounds[3] - bounds[3]) / self.image_res[1])
        max_x = int((bounds[2] - self.filebounds[0]) / self.image_res[0])
        max_y = int((self.filebounds[3] - bounds[1]) / self.image_res[1])
        if self.scaling == "bilinear":
            scaling = PILImage.BILINEAR
        elif self.scaling == "bicubic":
            scaling = PILImage.BICUBIC
        elif self.scaling == "antialias":
            scaling = PILImage.ANTIALIAS
        else:
            scaling = PILImage.NEAREST

        crop_size = (max_x-min_x, max_y-min_y)

        if self.transparency and self.image.mode not in ("LA", "RGBA"):
            self.image = self.image.convert("RGBA")   # TODO

        if min(min_x, min_y, max_x, max_y) < 0:
            if self.transparency and self.image.mode in ("L", "RGB"):
                self.image.putalpha(PILImage.new("L", self.image_size, 255))
            sub = self.image.transform(crop_size, PILImage.EXTENT, (min_x, min_y, max_x, max_y))
        else:
            sub = self.image.crop((min_x, min_y, max_x, max_y))
        if crop_size[0] < size[0] and crop_size[1] < size[1] and self.scaling == "antialias":
            scaling = PILImage.BICUBIC
        sub = sub.resize(size, scaling)

        buf = StringIO.StringIO()
        if 'transparency' in self.image.info:
            sub.save(buf, self.extension, transparency=True)
            sub.save()
        else:
            sub.save(buf, self.extension)

        buf.seek(0)
        tile.data = buf.read()
        return tile.data


class FixedGDAL(GDAL):
    """
    Создание тайлов с помощью GDAL.
    """

    def __init__(self, name, file=None, **kwargs):

        MetaLayer.__init__(self, name, **kwargs)

        self.ds = gdal.Open(file, gdal.GA_ReadOnly)
        #self.geo_transform = self.ds.GetGeoTransform()
        # if self.geo_transform[2] != 0 or self.geo_transform[4] != 0:
        #     raise Exception("Image is not 'north-up', can not use.")
        self.geo_transform = (0.0, 1.0, 0.0, self.ds.RasterYSize, 0.0, -1.0)
        self.image_size = [self.ds.RasterXSize, self.ds.RasterYSize]
        xform = self.geo_transform
        self.data_extent = [
            xform[0] + self.ds.RasterYSize * xform[2],
            xform[3] + self.ds.RasterYSize * xform[5],
            xform[0] + self.ds.RasterXSize * xform[1],
            xform[3] + self.ds.RasterXSize * xform[4],
        ]

    def renderTile(self, tile):
        bounds = tile.bounds()
        im = None

        tile_offset_left = 0
        tile_offset_top = 0

        if not (bounds[2] < self.data_extent[0]
                or bounds[0] > self.data_extent[2]
                or bounds[3] < self.data_extent[1]
                or bounds[1] > self.data_extent[3]):

            target_size = tile.size()

            off_x = int((bounds[0] - self.geo_transform[0]) / self.geo_transform[1])
            off_y = int((bounds[3] - self.geo_transform[3]) / self.geo_transform[5])
            width_x = int(((bounds[2] - self.geo_transform[0]) / self.geo_transform[1]) - off_x)
            width_y = int(((bounds[1] - self.geo_transform[3]) / self.geo_transform[5]) - off_y)

            # Prevent from reading off the sides of an image
            if off_x + width_x > self.ds.RasterXSize:
                oversize_right = off_x + width_x - self.ds.RasterXSize
                target_size = [
                    target_size[0] - int(float(oversize_right) / width_x * target_size[0]),
                    target_size[1]
                ]
                width_x = self.ds.RasterXSize - off_x

            if off_x < 0:
                oversize_left = -off_x
                tile_offset_left = int(float(oversize_left) / width_x * target_size[0])
                target_size = [
                    target_size[0] - int(float(oversize_left) / width_x * target_size[0]),
                    target_size[1],
                ]
                width_x += off_x
                off_x = 0

            if off_y + width_y > self.ds.RasterYSize:
                oversize_bottom = off_y + width_y - self.ds.RasterYSize
                target_size = [
                    target_size[0],
                    target_size[1] - round(float(oversize_bottom) / width_y * target_size[1])
                ]
                width_y = self.ds.RasterYSize - off_y

            if off_y < 0:
                oversize_top = -off_y
                tile_offset_top = int(float(oversize_top) / width_y * target_size[1])
                target_size = [
                    target_size[0],
                    target_size[1] - int(float(oversize_top) / width_y * target_size[1]),
                ]
                width_y += off_y
                off_y = 0

            bands = self.ds.RasterCount
            empty_array = numpy.zeros(shape=(target_size[1], target_size[0]), dtype=numpy.uint8)
            rgba_array = numpy.zeros((target_size[1], target_size[0], 4), dtype=numpy.uint8)
            for i in range(bands):
                band = self.ds.GetRasterBand(i+1)
                color_interp = band.GetColorInterpretation()
                band_array = gdalarray.BandReadAsArray(
                    band, off_x, off_y, width_x, width_y, target_size[0], target_size[1], empty_array)

                if color_interp == gdal.GCI_PaletteIndex:
                    color_table = band.GetRasterColorTable()
                    if color_table:
                        color_table_size = color_table.GetCount()
                        lookup = [
                            numpy.arange(color_table_size),
                            numpy.arange(color_table_size),
                            numpy.arange(color_table_size),
                            numpy.ones(color_table_size) * 255
                        ]
                        for color_i in range(color_table_size):
                            entry = color_table.GetColorEntry(color_i)
                            for color_ii in range(4):
                                lookup[color_ii][color_i] = entry[color_ii]
                    else:
                        lookup = []

                    for band_row in range(len(band_array)):
                        for band_col in range(len(band_array[band_row])):
                            color_pixel = numpy.zeros(shape=(4,), dtype=numpy.uint8)
                            for channel in range(4):
                                color_pixel[channel] = lookup[channel][band_array[band_row][band_col]]
                                rgba_array[band_row, band_col] = color_pixel

                elif color_interp in [gdal.GCI_RedBand, gdal.GCI_GreenBand, gdal.GCI_BlueBand, gdal.GCI_AlphaBand]:
                    index = {
                        gdal.GCI_RedBand: 0,
                        gdal.GCI_GreenBand: 1,
                        gdal.GCI_BlueBand: 2,
                        gdal.GCI_AlphaBand: 3,
                    }
                    for band_row in range(len(band_array)):
                        for band_col in range(len(band_array[band_row])):
                            rgba_array[band_row, band_col, 3] = 255   # TODO
                            rgba_array[band_row, band_col, index[color_interp]] = band_array[band_row][band_col]
                else:
                    for band_row in range(len(band_array)):
                        for band_col in range(len(band_array[band_row])):
                            rgba_array[band_row, band_col, 0] = band_array[band_row][band_col]
                            rgba_array[band_row, band_col, 1] = band_array[band_row][band_col]
                            rgba_array[band_row, band_col, 2] = band_array[band_row][band_col]
                            rgba_array[band_row, band_col, 3] = 255

            im = Image.fromarray(rgba_array)

        big = Image.new("RGBA", tile.size(), (0, 0, 0, 0))
        if im:
            big.paste(im, (tile_offset_left, tile_offset_top))
        buf = StringIO.StringIO()

        big.save(buf, self.extension)

        buf.seek(0)
        tile.data = buf.read()
        return tile.data


def get_tms_tile(src_file, bbox, z, y, x, name=None):
    levels = 5
    name = name or ''
    size = (256, 256)

    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    if width >= height:
        aspect = 1.0   # int(float(width) / float(height))
        max_res = float(width) / float(size[0] * aspect)
    else:
        aspect = 1.0   # int(float(height) / float(width))
        max_res = float(height) / float(size[1] * aspect)
    resolutions = [max_res / 2 ** i for i in range(int(levels))]

    layer = FixedGDAL(
        size=size,
        resolutions=resolutions,
        name=name,
        file=src_file,
        filebounds=','.join(str(v) for v in bbox),
        transparency=True,
        bbox=bbox,
        tms_type="google",
        extension="png"
    )
    tile = Tile(layer, int(y), int(x), int(z))
    data = layer.renderTile(tile)
    return 'image/png', data
