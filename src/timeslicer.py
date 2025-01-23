import pandas as pd

#Represents a single time slice
class TimeSlice:
    def __init__(self):
        self.classes = []
        self.dataframe = None
        self.start = None
        self.end = None
        self.par = None
        self.duration = None
        
    def __repr__(self):
        return str(" ".join(self.classes)) + " for " + str(self.duration) + "s from " + str(self.start) + " to " + str(self.end)
        
    #Performs final calculations (such as calculating total duration)
    def Update(self):
        self.duration = (self.end - self.start).total_seconds()
        
    #Checks to see if a single class is present
    def HasClass(self,classname):
        if classname in self.classes:
            return True
        return False
    
    #Checks to see if ALL of the classes are present
    def Matches(self,classlist):
        bits = classlist.split(' ')        
        for b in bits:
            if b not in self.classes:
                return False
        return True
        
#The detail of an individual test
class SliceTest:
    def __init__(self,test,positive,negative):
        self.positive = positive
        self.negative = negative
        self.test = test
        
#A collection of TimeSlice objects
class TimeSlices:
    def __init__(self):
        self.slices = []          
    
    #Get the total time (ie. all up)
    def TotalTime(self):
        ttl = 0
        for q in range(0,len(self.slices)):
            ttl += self.slices[q].duration
        return ttl

    def CalcTime(self,selector):
        ttl = 0
        for sl in self.slices:
            if sl.Matches(selector):
                ttl += (sl.dataframe.index[len(sl.dataframe.index)-1] - sl.dataframe.index[0]).total_seconds()
                    
        return ttl

    def CountMatches(self,selector):
        ttl = 0
        for sl in self.slices:
            if sl.Matches(selector):
                ttl += 1
                    
        return ttl
    
    #Get a list of the different classes
    def Classes(self):
        com = []
        for x in self.slices:
            for q in x.classes:
                if q not in com:
                    com.append(q)
                
        return com
            
    #Calculate the total amount of time each class was active
    def ClassTime(self,classname):
        ttl = 0
        for q in range(0,len(self.slices)):
            if self.slices[q].Matches(classname):
                ttl += self.slices[q].duration
        return ttl
    
    #Use a dictionary of selectors to group results
    #Input is a dictionary of strings, the values are arrays of time-slice selectors    
    def SelectSlices(self,selectors,collapse=False):
        hits = {}
        touched = []
        
        #For each selector...
        for name in selectors:
            #Go through each slice looking for matches
            for sl in self.slices:
                if sl in touched:
                    continue
                
                matches = False
                for sel in selectors[name]:
                    if sl.Matches(sel) == True:
                        matches = True                                           
                        break
                        
                #If any selector matches, record it and break
                if matches == True:
                    touched.append(sl)
                    if name not in hits:
                        hits[name] = []
                    hits[name].append(sl)                    
                
        #Capture any unmatched selectors
        unmatched = []
        for sl in self.slices:
            if sl not in touched:
                unmatched.append(sl)
                
        #If there were any unmatched, add them to the array
        if len(unmatched) > 0:
            hits['*'] = unmatched

        #If 'collapse' is requested, rolls the results up into individual             
        if collapse == True:
            final = []
            for name in hits:
                slc = TimeSlice()
                for x in hits[name]:
                    slc.classes = [name]
                    if x.duration is None:
                        continue
                    if slc.start is None:
                        slc.start = x.start
                    slc.end = x.end
                    if slc.duration is None:
                        slc.duration = x.duration
                    else:
                        slc.duration += x.duration
                    if slc.dataframe is None:
                        slc.dataframe = x.dataframe
                    else:
                        slc.dataframe = pd.concat([slc.dataframe,x.dataframe])
                        
                final.append(slc)
                
            return final
                
        return hits
    
    #Get a list of the unique class combinations
    def Combinations(self):
        com = []
        for x in self.slices:
            st = " ".join(x.classes)
            if st not in com:
                com.append(st)
                
        return com
    
    #Combine all slices of the same class
    def Collapse(self):
        results = {}
        combs = self.Combinations()
        for c in combs:
            slc = TimeSlice()
            for x in self.slices:
                st = " ".join(x.classes)
                if c == st:
                    if x.duration is None:
                        continue
                    if slc.start is None:
                        slc.start = x.start
                    slc.end = x.end
                    if slc.duration is None:
                        slc.duration = x.duration
                    else:
                        slc.duration += x.duration
                    if slc.dataframe is None:
                        slc.dataframe = x.dataframe
                    else:
                        slc.dataframe = pd.concat([slc.dataframe,x.dataframe])
            results[c] = slc
            
        return results
    
    #Get dataframe rows for a combination
    def GetData(self,classname):
        df = None
        for sl in self.slices:
            if sl.Matches(classname):
                if df is None:
                    df = sl.dataframe.copy()
                else:
                    df = pd.concat([df,sl.dataframe])
                    
        return df

    def CalcRate(self,classname,colname,timefactor = 1,mult=None):
        indexes = []
        data = []
        lastmatch = False
        totalamount = 0
        
        lastpoint = None
        for sl in self.slices:
            #print("Working On Slice: "+ str(len(sl.dataframe.index)))
            if classname == "*" or sl.Matches(classname):
                if lastmatch == False:
                    prevrow = None
                    prevpoint = None
                    
                for indx,rw in sl.dataframe.iterrows():
                    amnt = rw[colname]
                    if prevpoint is None:
                        prevrow = rw
                        prevpoint = indx
                        
                        amnt = 0                        
                        
                    if amnt != 0:                        
                        diff = (indx - prevpoint).total_seconds()
                        dist = diff * (amnt / timefactor)                        

                        if mult is None:
                            totalamount += dist
                        else:
                            totalamount += (dist * rw[mult])

                    indexes.append(indx)                        
                    data.append(totalamount)
                    prevrow = rw
                    prevpoint = indx
                    
                lastmatch = True
            else:
                for indx,rw in sl.dataframe.iterrows():
                    prevrow = rw
                    prevpoint = indx
                    indexes.append(indx)                        
                    data.append(totalamount)
                lastmatch = False
                    
        if len(indexes) == 0:
            return None
            
        return pd.DataFrame(data = data, index=indexes, columns = ["Total"])    
        
    def RateIndex(self,classname,colname,timefactor=1):
        df = None
        collist = None
        indexes = []
        data = []
        totalamount = 0
        lastmatch = False
        
        lastpoint = None
        for sl in self.slices:
            if classname == "*" or sl.Matches(classname):
                if collist is None:
                    collist = []
                    for c in sl.dataframe.columns:
                        collist.append(c)

                if lastmatch == False:
                    prevrow = None
                    prevpoint = None
                for indx,rw in sl.dataframe.iterrows():
                    amnt = rw[colname]
                    if prevpoint is None:
                        prevrow = rw
                        prevpoint = indx
                        indexes.append(totalamount)
                        dx = [0] * len(collist)
                        for x in range(0,len(collist)):
                            dx[x] = rw[rw.columns[x]]
                        data.append(dx)
                        continue
                        
                    if amnt == 0:
                        prevrow = rw
                        prevpoint = indx
                        continue                        
                        
                    diff = (indx - prevpoint).total_seconds()
                    dist = diff * (amnt / timefactor)

                    totalamount += dist

                    indexes.append(totalamount+0)
                    dx = [0] * len(collist)
                    for x in range(0,len(collist)):
                        dx[x] = rw[rw.columns[x]]
                    data.append(dx)
                    
                lastmatch = True
            else:
                lastmatch = False
                    
        if len(indexes) == 0:
            return None
            
        return pd.DataFrame(data = data, index=indexes, columns = collist)

    def GetClassAt(self,dt):
        for sl in self.slices:
            if sl.start <= dt:
                if sl.end > dt:
                    return sl.classes

        return []
        
#Performs time-slicing on a Pandas DataFrame
class TimeSlicer:
    def __init__(self,df):
        self.df = df
        self.tests = []
        
    #Adds a test
    def AddTest(self,test,positive,negative):
        self.tests.append(SliceTest(test,positive,negative))

    #Adds a splitter
    def AddSplit(self,value):
        self.tests.append(SliceTest(value,None,None))

    #Adds a channel from an array of events
    def AddEventRegions(self,arr,colname,source,start,end,utc=False,default=None):
        inarr = [default] * len(self.df.index)
        indx = 0
        for x in self.df.index:
            for n in range(0,len(arr)):
                if x > arr[n][start] and x < arr[n][end]:
                    inarr[indx] = arr[n][source]
            indx += 1

        self.df[colname] = inarr

    def cleanclassname(self,nm):
        return nm.replace(" ","")
        
    #Performs slicing using the tests
    def Slice(self):
        laststart = None
        lastindx = None
        lastrow = None
        prevclass = []
        slices = []
        
        for indx,rw in self.df.iterrows():
            #Check for classes...
            classlist = []
            for t in self.tests:
                if t.positive is None:                    
                    classlist.append(self.cleanclassname(t.test+"_"+rw[t.test]))
                else:
                    if t.test(rw) == True:
                        if t.positive is not None:
                            classlist.append(t.positive)
                    else:
                        if t.negative is not None:
                            classlist.append(t.negative)
                        
            #Ignore first sample
            if lastindx is None:
                lastindx = indx
                lastrow = rw
                laststart = indx
                prevclass = classlist
                continue
            
            tdiff = indx - lastindx                       
                                    
            #Check for previous class match...
            changed = False
            if len(prevclass) != len(classlist):
                changed = True
            else:
                for a in classlist:
                    if a not in prevclass:
                        changed = True
                        break                               
            
            #Record slices
            if changed == True:                
                ts = TimeSlice()
                ts.classes = prevclass
                ts.start = laststart
                ts.end = indx
                ts.dataframe = self.df[laststart:lastindx]
                laststart = indx
                slices.append(ts)
                
            lastindx = indx
            lastrow = rw
            prevclass = classlist
            
        #Add the last/incomplete item
        if indx > laststart:
            ts = TimeSlice()
            ts.classes = prevclass
            ts.start = laststart
            ts.end = indx
            ts.dataframe = self.df[laststart:lastindx]
            slices.append(ts)
        
        #Calculate totals and refresh
        final = TimeSlices()
        for x in slices:
            x.par = final
            x.Update()
            final.slices.append(x)
            
        return final
                
