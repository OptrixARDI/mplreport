import pandas as pd

class DiscretePatterns:
    def __init__(self):
        self.frame = None
        self.any = False
        self.discs = []
        self.conts = []

    def AddDiscrete(self,name,table):
        table = table.rename(columns={'value': name})
        if self.any == False:
            self.any = True
            self.frame = table
        else:
            self.frame = self.frame.join(table,how='outer')        
        self.discs.append(name)

    def AddAnalog(self,name,table):
        table = table.rename(columns={'value': name})
        if self.any == False:
            self.any = True
            self.frame = table
        else:
            self.frame = self.frame.join(table,how='outer')
        self.conts.append(name)

    def SetDataframe(self,frame):
        self.frame = frame

    def combinefunction(self, collist, row):
        val = 0
        for i in range(0,len(collist)):
            val = val + (row[collist[i]] * (i+1))
        return val

    def CombineDigital(self,collist,result):
        self.frame[result] = self.frame.apply(lambda row: int(self.combinefunction(collist,row)),axis=1)

        for n in collist:
            self.frame.drop(n,axis=1,inplace=True)        

    def Ready(self):
        for n in self.conts:
            self.frame[n] = self.frame[n].interpolate(method='linear')
        self.frame = self.frame.fillna(method='backfill')
        self.frame = self.frame.fillna(method='ffill')
        return self.frame

    def GetAllTimeframes(self, colname):
        frames = {}
        distinct = self.frame[colname].unique()
        for val in distinct:
            #print("Requesting Times For " + str(val))
            tf = self.GetTimeframesFor(lambda row: row[colname] == val)
            v = int(val)
            for n in tf:
                try:
                    frames[v].append(n)
                except:
                    frames[v] = []
                    frames[v].append(n)
        return frames

    def GetTimeframesFor(self,lamb):
        
        frames = []

        seri = self.frame.apply(lamb, axis=1)
 
        lasttime = None
        try:
            for n in seri.iteritems():
                if n[1] == True:
                    if lasttime is None:
                        lasttime = n[0]
                else:
                    if lasttime is not None:
                        frames.append((lasttime,n[0]))
                        lasttime = None
        except:
            for n in seri.items():
                if n[1] == True:
                    if lasttime is None:
                        lasttime = n[0]
                else:
                    if lasttime is not None:
                        frames.append((lasttime,n[0]))
                        lasttime = None
                        
        if lasttime is not None:
            frames.append((lasttime,n[0]))
        
        return frames

    def GetInFrameData(self,lamb):
        timeframes = self.GetTimeframesFor(lamb)

        #print(timeframes)

        df = None
        for tf in timeframes:        
            active = self.frame[tf[0] : tf[1]]
            if df is None:
                df = active
            else:                
                df = df.append(active)

        return df

    def GetTotalTimeFor(self, lamb):
        timeframes = self.GetTimeframesFor(lamb)

        #print(str(timeframes))

        ttltime = 0
        for tf in timeframes:        
            active = self.frame[tf[0] : tf[1]]            
            mintime = active.index.min()
            maxtime = active.index.max()            

            ttltime = ttltime + float(pd.Timedelta(maxtime - mintime).total_seconds())

        return ttltime

    def GetTotalTime(self):
        mintime = self.frame.index.min()
        maxtime = self.frame.index.max()        

        amnt = float(pd.Timedelta(maxtime - mintime).total_seconds())

        return amnt

def hours(seconds):
        return round(seconds / (60*60),2)

def calctotaltimes(series, seriesb = None):

    if seriesb is not None:
        series = cliptimes(series,seriesb)
        
    al = 0
    for n in series:
        al = al + (n[1] - n[0]).total_seconds()

    return al

def cliptimes(seriesa, seriesb):
    ret = []    
    for a in seriesa:
        for b in seriesb:
            #Does B start before A ends?
            if a[0] <= b[1] and b[0] < a[1]:
                st = a[0]
                en = b[1]
                if a[1] < b[1]:
                    en = a[1]
                if b[0] > a[0]:
                    st = b[0]
                ret.append((st,en))
    return ret

def combinetimes(seriesa, seriesb):
    ret = []
    for a in seriesa:
        line = [a[0],a[1]]
        for b in seriesb:
            if line[0] <= b[1] and b[0] < line[1]:
                line[1] = b[0]

        if line[0] == line[1]:
            continue

        ret.append(line)

    return ret

