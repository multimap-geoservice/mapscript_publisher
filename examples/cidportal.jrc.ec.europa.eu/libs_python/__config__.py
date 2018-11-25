#!python
#
# Copyright (c) 2015, European Union
# All rights reserved.
# Authors: Simonetti Dario, Marelli Andrea

import os

# ----------------------------------
# change to false before prod push
dev = False
# ----------------------------------


GLOBALS = dict()

if dev:
    GLOBALS['app_name'] = 'Sentinel Processing Tool - DEV -'
    GLOBALS['base_url'] = 'https://cidportal.jrc.ec.europa.eu/forobsdev/'
    GLOBALS['mapserver_url'] = 'https://cidportal.jrc.ec.europa.eu/forobsdev/'
    GLOBALS['debug'] = 'true'
else:
    GLOBALS['app_name'] = 'Sentinel Processing Tool'
    GLOBALS['base_url'] = 'https://cidportal.jrc.ec.europa.eu/forobs/'
    GLOBALS['mapserver_url'] = 'https://cidportal.jrc.ec.europa.eu/forobs/'
    GLOBALS['debug'] = 'false'

GLOBALS['S2'] = dict()

GLOBALS['S2']['root_path'] = '/var/S2_repository/'
GLOBALS['S2']['cid_paths'] = ["/eos/jeodpp/data/SRS/Copernicus/S2/scenes/source/L1C/"]

# -- list of CID paths : used to build list of symlinks
GLOBALS['S2']['zip_path'] = os.path.join(GLOBALS['S2']['root_path'], 'S2_zip')
GLOBALS['S2']['unzip_path'] = os.path.join(GLOBALS['S2']['root_path'], 'S2_unzip')
GLOBALS['S2']['scripts_path'] = os.path.join(GLOBALS['S2']['root_path'], 'S2_scripts')
GLOBALS['S2']['qklooks_path'] = os.path.join(GLOBALS['S2']['root_path'], 'S2_qklook')
GLOBALS['S2']['virtual_path'] = os.path.join(GLOBALS['S2']['root_path'], 'S2_virtual')
GLOBALS['S2']['sqlite_database'] = os.path.join(GLOBALS['S2']['virtual_path'],'Main_catalogue.db')
GLOBALS['S2']['sqlite_database_tmp'] = os.path.join(GLOBALS['S2']['virtual_path'],'Main_catalogue_tmp.db')


# -- Catalogs' paths --
GLOBALS['S2']['catalogue_path'] = os.path.join(GLOBALS['S2']['virtual_path'], 'Sentinel2_catalogue1.shp')
GLOBALS['S2']['qklooks_catalogue_path'] = os.path.join(GLOBALS['S2']['qklooks_path'], 'Sentinel2_qklooks.shp')

# -- MGRS grid paths --
GLOBALS['S2']['MGRS'] = os.path.join(GLOBALS['S2']['virtual_path'], 'MGRS.shp')

# -- Sentinel2 bands --
GLOBALS['S2']['s2_bands'] = [
    'B01.jp2', 'B02.jp2', 'B03.jp2', 'B04.jp2', 'B05.jp2', 'B06.jp2',
    'B07.jp2', 'B08.jp2', 'B8A.jp2', 'B09.jp2', 'B10.jp2', 'B11.jp2', 'B12.jp2'
]
GLOBALS['S2']['qklooks_bands'] = ['_B12.jp2', '_B8A.jp2', '_B11.jp2']
GLOBALS['S2']['qklooks_resolutions'] = ['500']   # in meters
GLOBALS['S2']['resolutions'] = ['10']  # in meters
GLOBALS['S2']['tileindex_basename'] = 'Sentinel2_imagery'

# Temporary processing folders
GLOBALS['S2']['processing_out'] = os.path.join(GLOBALS['S2']['root_path'], 'S2_out')
GLOBALS['S2']['processing_tmp'] = os.path.join(GLOBALS['S2']['processing_out'], 'tmp')
GLOBALS['S2']['www_tmp'] = 'temp'
GLOBALS['S2']['server_tmp'] = os.path.join(GLOBALS['S2']['scripts_path'], 'www', GLOBALS['S2']['www_tmp'])

# Optional
GLOBALS['S2']['tiff_path'] = os.path.join(GLOBALS['S2']['root_path'], 'S2_Tiff')
GLOBALS['S2']['classification_catalogue_path'] = os.path.join(GLOBALS['S2']['tiff_path'], 'Sentinel2_class.shp')

GLOBALS['S2']['mosaic_path'] = os.path.join(GLOBALS['S2']['root_path'],  'S2_mosaic')
GLOBALS['S2']['tmp_mosaic_path'] = os.path.join(GLOBALS['S2']['mosaic_path'],'Tmp')
GLOBALS['S2']['class_mosaic_path'] = os.path.join(GLOBALS['S2']['mosaic_path'],'Classification')
GLOBALS['S2']['image_mosaic_path'] = os.path.join(GLOBALS['S2']['mosaic_path'],'Composite')

