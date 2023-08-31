import os

class SiteCommon:
    def __init__(self):
        self.properties = {}
        self.Set("common_value", 0)
        

    def Set(self, prop, value):
        self.properties[prop] = value

    def Get(self, prop, default=None):
        try:
            return self.properties[prop]
        except:
            return default
