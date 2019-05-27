
import os
import ast
import json

import mapscript

from map_pub import PubMap


########################################################################
class Protocol(object):
    """
    Class for serialization & render maps:
    mapscript as mapscript_publisher
    """
    
    #----------------------------------------------------------------------
    def __init__(self, url, logging):
       
        self.url = url 
        self.logging = logging
        self.proto_schema = {
            "json": {
                "test": self.is_json,
                "get": self.get_mapjson,
                "request": self.request_mapscript,
                "metadata": self.get_metadata,
                "enable": True,
                },
            "map": {
                "test": self.is_map,
                "get": self.get_mapfile,
                "request": self.request_mapscript,
                "metadata": self.get_metadata,
                "enable": True,
                },
        }
            
    def is_json(self, test_cont):
        try:
            if os.path.isfile(test_cont):
                with open(test_cont) as file_:  
                    _ = json.load(file_)
            else:
                _ = json.loads(test_cont)
        except:
            return False
        else:
            return True    

    def is_map(self, test_cont):
        try:
            if os.path.isfile(test_cont):
                _ = mapscript.mapObj(test_cont)
            else:
                raise # map file content in DB: to do
        except:
            return False
        else:
            return True
        
    def get_mapfile(self, map_name, content):
        """
        get map on map file
        PubMap()
        """
        try:
            if os.path.isfile(content):
                pub_map = mapscript.mapObj(content)
            else:
                raise # map file content in DB: to do
        except:
            self.logging(
                0, 
                "ERROR: Content {} not init as Map FILE".format(content)
            )
        else:
            return self.edit_mapscript(map_name, pub_map())
    
    def get_mapjson(self, map_name, content):
        """
        get map on json template
        PubMap()
        """
        try:
            if os.path.isfile(content):
                pub_map = PubMap()
                pub_map.load_json(content)
            else:
                content = ast.literal_eval(content)
                pub_map = PubMap(content)
        except:
            self.logging(
                0, 
                "ERROR: Content {} not init as Map JSON".format(content)
            )
        else:
            return self.edit_mapscript(map_name, pub_map())
     
    def edit_mapscript(self, map_name, content):
        """
        edit requests resources in mapscript object
        """
        if isinstance(content, mapscript.mapObj):
            if map_name != "":
                map_url = "{0}/{1}".format(self.url, map_name)
                if "wms_enable_request" in content.web.metadata.keys():
                    content.web.metadata.set("wms_onlineresource", map_url)
                if "wfs_enable_request" in content.web.metadata.keys():
                    content.web.metadata.set("wfs_onlineresource", map_url)
                return content
    
    def request_mapscript(self, env, mapdata, que=None):
        """
        render on mapserver mapscript request
        """
        request = mapscript.OWSRequest()
        mapscript.msIO_installStdoutToBuffer()
        request.loadParamsFromURL(env['QUERY_STRING'])
    
        try:
            status = mapdata.OWSDispatch(request)
        except Exception as err:
            pass
    
        content_type = mapscript.msIO_stripStdoutBufferContentType()
        result = mapscript.msIO_getStdoutBufferBytes()
        out_req = (content_type, result)
        if que is None:
            return out_req
        else:
            que.put(out_req)
            
    def get_metadata(self, map_cont):
        matadata_keys = map_cont.web.metadata.keys() 
        return {my: map_cont.web.metadata.get(my) for my in matadata_keys}
