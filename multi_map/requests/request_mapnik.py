
from xml.etree import ElementTree

try:
    import mapnik
except ImportError:
    import mapnik2 as mapnik

from mapweb import MapsWEB


########################################################################
class Protocol(object):
    """
    Class for serialization & render maps:
    mapnik as OGCServer
    """
    
    #----------------------------------------------------------------------
    def __init__(self):
        
        self.proto_schema = {
            "xml": {
                "test": self.is_xml,
                "get": self.get_mapnik,
                "request": self.request_mapnik,
                },
        }
            
    def is_xml(self, test_cont):
        try:
            if os.path.isfile(test_cont):
                _ = ElementTree.parse(test_cont)
            else:
                _ = ElementTree.fromstring(test_cont)
        except:
            return False
        else:
            return True
        
    def get_mapnik(self, map_name, content):
        """
        get map on mapnik xml
        mapnik.load_map_from_string()
        """
        pass
    
    def request_mapnik(self, env, mapdata, que=None):
        """
        render on mapnik request
        """
        pass
