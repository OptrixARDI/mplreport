import os
import json
import glob
import datetime

class KPICapture:
    def __init__(self,name,path = None):
        self.basedir = path
        if self.basedir is None:
            self.basedir = os.path.dirname(__file__) + "/_capture"
            if not os.path.exists(self.basedir):
                os.mkdir(self.basedir)
            self.basedir += "/" + name
            if not os.path.exists(self.basedir):
                os.mkdir(self.basedir)
                
        self.values = {}
        
    def CaptureValue(self,name,value):
        self.values[name] = value

    def Commit(self,dt):           
        filename = self.basedir + "/" + dt.strftime("%Y%m%d%H") + ".json"
        if not os.path.exists(self.basedir):
            os.mkdir(self.basedir)

        if os.path.exists(filename):
            try:
                fl = open(filename,'r')
                content = fl.read()
                fl.close()
                content = json.loads(content)
            except:
                print("Previous Captured Content Lost due to File Correuption")
                content = {}
        else:
            content = {}


        for q in self.values:
            content[q] = self.values[q]

        fl = open(filename,'w')
        fl.write(json.dumps(content))
        fl.flush()
        fl.close()
        #print(str(content))

class KPIAccess:
    def __init__(self,name,path = None):
        self.basedir = path
        if self.basedir is None:
            self.basedir = os.path.dirname(__file__) + "/_capture/" + name
        self.values = {}
        
    def GetValues(self,fromdt,todt):
        files = glob.glob(self.basedir + "/*.json")

        fromstr = fromdt.strftime("%Y%m%d%H")
        tostr = todt.strftime("%Y%m%d%H")
        files.sort()

        values = {}
        
        for f in files:
            nm = os.path.basename(f)
            if nm > tostr:
                break
            if nm < fromstr:
                continue

            dtx = datetime.datetime.strptime(nm.replace(".json",""),"%Y%m%d%H")
            try:
                values[dtx] = self.GetFileContent(f)
            except:
                values[dtx] = {}
                pass

        return values

    def GetFileContent(self,filename):           
        
        if os.path.exists(filename):
            fl = open(filename,'r')
            content = fl.read()
            fl.close()
            return json.loads(content)
        else:
            return {}
