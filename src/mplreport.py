import os
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.image as mpimg
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
import json
import datetime
import traceback
import pytz

try:
    import sitecommon
except:
    pass

try:
    import ardi.util.outputengine as outengine
except:
    pass

try:
    import ardiapi
except:
    pass

def ardireport(*args,**kwargs):    
    def wrap_report(func):
        import aql
                
        stime = datetime.datetime.now()
        rargs = aql.ReportArgs(args[0])
        report = CreateFromArgs(rargs,*kwargs)

        configfile = None        

        if rargs.nopng == False:
            basepath = os.path.dirname(__file__)
            tgt = rargs.target.replace("\\","/")
            basepath = basepath.replace("\\","/")
            
            if basepath in tgt:
                basepath = os.path.dirname(tgt)
                configfile = basepath + "/outputs.json"

        if configfile is not None:
            try:
                if rargs.nopng == False:
                    keyvalue = outengine.KVOutput("Report Output",configfile = configfile)
                    event = outengine.EVOutput("Report Output",configfile = configfile)                       
            except:
                event = None
                keyvalue = None

        report.keyvalue = keyvalue
        report.event = event

        try:            
            func(report,rargs)            

            if rargs.nopng == False:
                if keyvalue is not None:
                    try:                    
                        etime = datetime.datetime.now()
                        tmx = (etime - stime).total_seconds()                    
                        keyvalue.Set(args[0] + " Report/Success",1)
                        keyvalue.Set(args[0] + " Report/Last Generated",stime.strftime("%Y-%m-%d %H:%M:%S"))
                        keyvalue.Set(args[0] + " Report/Generation Time",tmx)
                        keyvalue.Stop()
                        
                        event.Write(args[0] + " Generated",tmx,options={"success":  True,"report": args[0]})
                        event.Stop()
                    except:
                        traceback.print_exc()
                        pass
        except:
            report.Failed()

            if rargs.nopng == False:
                try:
                    etime = datetime.datetime.now()
                    tmx = (etime - stime).total_seconds()
                    keyvalue = outengine.KVOutput("Report Output",configfile = configfile)                
                    keyvalue.Set(args[0] + " Report/Success",0)
                    keyvalue.Set(args[0] + " Report/Last Generated",stime.strftime("%Y-%m-%d %H:%M:%S"))
                    keyvalue.Set(args[0] + " Report/Generation Time",-1)
                    keyvalue.Stop()

                    event = outengine.EVOutput("Report Output",configfile = configfile)                
                    event.Write(args[0] + " Failed To Generate",tmx,options={"failure": True,"report": args[0]})
                    event.Stop()
                except:
                    pass
    
    return wrap_report


def CreateFromArgs(args):
    paper = "default"
    if args.size is not None:
        paper = args.size
    previewdir = args.target + ".png"
    if args.nopng == True:
        previewdir = None
    rep = MPLReport(args.reportname,args.target + ".pdf",preview=previewdir,fmt=args.format,style=args.style,papersize=paper)
    rep.location = args.location
    rep.defaultstart = args.utcstart
    rep.defaultend = args.utcend
    rep.ardiserver = args.server
    rep.arguments = args
    rep.timezonename = args.timezone
    try:
        rep.common = sitecommon.SiteCommon()
    except:
        rep.common = None
        
    return rep

def LocalTimeToUTC(tm):
    ltz = datetime.datetime.now().astimezone().tzinfo
    tm = tm.replace(tzinfo=ltz)    
    tm = tm.astimezone(pytz.utc)
    tm = tm.replace(tzinfo=None)
    return tm

def UTCToLocalTime(tm):
    ltz = datetime.datetime.now().astimezone().tzinfo
    tm = tm.replace(tzinfo=pytz.utc)    
    tm = tm.astimezone(ltz)
    tm = tm.replace(tzinfo=None)
    return tm

class MPLReport():
    def __init__(self,name,target,preview=None,papersize="default",orient="portrait",multipage=False,fmt="pdf",style=None,defaultstart=None,defaultend=None):
        self.multi = multipage
        self.papersize = papersize
        self.orientation = orient
        self.multipage = False
        self.firstpage = True
        self.target = target
        self.pdf = None
        self.fig = None
        self.plt = None
        self.name = name
        self.location = ""
        self.preview = preview
        self.pages = 1
        self.titled = False
        self.fmt = fmt
        self.location = None
        self.style = style
        self.nudge = (0,0)
        self.alerts = None
        self.sizeset = False
        self.defaultstart = defaultstart
        self.defaultend = defaultend
        self.ardiserver = None
        self.srv = None
        self.datasummaries = []
        self.titlespace = 0
        self.timezonename = "UTC"
        self.tz = None

        pd.plotting.register_matplotlib_converters()

    def CreatePage(self,*args,**kwargs):

        if self.tz is None:
            if self.timezonename == "UTC":
                self.tz = pytz.utc
            else:
                self.tz = pytz.timezone(self.timezonename)

        columns = 1
        rows = 1
        #print(str(args))
        if len(args) > 0:
            columns = args[0]
        if len(args) > 1:
            rows = args[1]

        if self.pdf is not None:
            if self.sizeset == False:
                self.figure.tight_layout(rect=[0.05+self.nudge[0], 0.05+self.nudge[1], 0.96, 0.96])    
                if self.titlespace != 0:
                    plt.subplots_adjust(top=1-self.titlespace)
                self.sizeset = True

            self.pages = self.pages + 1
            self.pdf.savefig(self.fig)
            if self.preview is not None:
                plt.savefig(
                    self.preview,
                    dpi=100,
                    pad_inches=0.1,
                    bbox_inches="tight",
                    transparent=True,
                )
            self.plt.close()        
            
        psize = None
        header = None
        orient = None

        if 'psize' in kwargs:
            psize = kwargs['psize']
            del kwargs['psize']
        if 'orient' in kwargs:
            orient = kwargs['orient']
            del kwargs['orient']
        if 'header' in kwargs:
            header = kwargs['header']
            del kwargs['header']

        if psize is None:
            psize = self.papersize
        if orient is None:
            orient = self.orientation
        if header is None:
            header = self.firstpage

        wid = 8.27
        hit = 11.69
        psize = psize.upper()

        #print("New Page Size: " + str(psize))
        if psize == "DEFAULT":
            psize = "A4"

        if psize == "A4":
            wid = 8.3
            hit = 11.7
        
        if psize == "LETTER":
            wid = 8.5
            hit = 11

        if psize == "720P":
            hit = 10
            wid = 10 / (16/9)

        if psize == "1080P":
            hit = 20
            wid = 20 / (16/9)
            
        bits = psize.split("X")
        if len(bits) > 1:
            #Custom size passed on command-line
            pxscale = 1/plt.rcParams['figure.dpi']
            hit = pxscale * int(bits[0])
            wid = pxscale * int(bits[1])
            print("Custom Paper Size: " + str(wid) + " x " + str(hit))
        else:
            if orient.upper() != "PORTRAIT":
                w2 = wid
                wid = hit
                hit = w2

        if self.pdf is None:
            self.pdf = PdfPages(self.target)
            self.plt = plt

            stylefile = os.path.dirname(os.path.abspath(__file__)) + "/globalstyle.mplstyle"
            if self.style is not None:
                if self.style == "darkmode":
                    plt.style.use('dark_background')
                else:
                    stylefile = os.path.abspath(__file__) + "/" + self.style + ".mplstyle"
                
            if not os.path.exists(stylefile):
                stylefile = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/globalstyle.mplstyle"
            if os.path.exists(stylefile):
                plt.style.use(stylefile)


        fig, ax = plt.subplots(
                    *args,
                    **kwargs
        )
        fig.set_size_inches(hit, wid)        
    
        self.figure = fig
        return (fig,ax)

    def NudgeContent(self,x,y):
        self.nudge = (x,y)

    def WriteAlert(self,alertname,alertvalue):
        if self.alerts is None:
            self.alerts = {}
            
        if alertname not in self.alerts:
            self.alerts[alertname] = alertvalue
        else:
            if self.alerts[alertname] == "":
                self.alerts[alertname] = alertvalue
            else:
                self.alerts[alertname] += "," + alertvalue

    def DateFormat(self,starttime=None,endtime=None):
        if endtime is None:
            endtime = self.defaultend
        if starttime is None:
            starttime = self.defaultstart
            
        df = (endtime - starttime).total_seconds()
        if df > (60*60*24):
            if df > (60*60*24*3):
                return '%d/%m'
            else:
                return '%H %d/%m'        
        return '%H:%M'

    def DateFormatter(self,starttime=None,endtime=None):        
        return mdates.DateFormatter(self.DateFormat(starttime,endtime))

    def AdjustLogoForDPI(self,dpi):
        img = None
        try:
            if self.logoimage is not None:
                img = self.logoimage
        except:
            pass

        if img is None:
            return

    def Title(self,starttime=None,endtime=None,override=None,location=None,args=None):        
        
        top = 0.94
        name = self.name
        if override is not None:
            name = override

        if args is not None:
            if starttime is None:
                starttime = args.localstart
                endtime = args.localend

        if starttime is None:            
            starttime = self.LocalTime(self.defaultstart)            
        if endtime is None:
            endtime = self.LocalTime(self.defaultend)            

        #Skip the logo on inline versions...
        if 'inline' not in self.fmt:
        
            dirx = os.path.dirname(os.path.abspath(__file__))
            logofile = dirx + "/logo.jpg"
            if not os.path.exists(logofile):
                logofile = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/logo.jpg"

            if not os.path.exists(logofile):
                dirx = os.path.dirname(os.path.abspath(__file__))
                logofile = dirx + "/logo.png"
            if not os.path.exists(logofile):
                logofile = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/logo.png"
                
            if os.path.exists(logofile):
                newax = self.figure.add_axes([0.8, 0.8, 0.15, 0.17], anchor='NE', zorder=100)                
                newax.axis('off')

                img = mpimg.imread(logofile)

                newax.imshow(img)

                ht = img.shape[0]
                wd = img.shape[1]
                top = 0.94                
                
        self.figure.text(0.05, top, name, fontsize=20)
        
        top = top - 0.03
        if location is not None:
            self.figure.text(0.05, top, location, fontsize=12)
            top = top - 0.02
        else:
            if self.location is not None:
                self.figure.text(0.05, top, self.location, fontsize=12)
                top = top - 0.02
                
        try:
            startstr = starttime.strftime("%Y-%m-%d %H:%M:%S")
        except:
            startstr = starttime

        try:
            endstr = endtime.strftime("%Y-%m-%d %H:%M:%S")
        except:
            endstr = endtime        
            
        self.figure.text(
            0.05,
            top,
            startstr
            + " to "
            + endstr,
            fontsize=10,
        )

        self.figure.tight_layout(rect=[0.05+self.nudge[0], 0.05+self.nudge[1], 0.96, 0.87]) 
        if self.titlespace != 0:
            plt.subplots_adjust(top=1-self.titlespace)
        self.sizeset = True

    def Save(self):

        if self.sizeset == False:
                self.figure.tight_layout(rect=[0.05+self.nudge[0], 0.05+self.nudge[1], 0.96, 0.96])    
                if self.titlespace != 0:
                    plt.subplots_adjust(top=0.85)
                self.sizeset = True

        if self.fmt == "inlinesvg":
            from io import StringIO
            f = StringIO()            
            self.figure.savefig(f,format="svg",bbox_inches="tight",
                transparent=True)
            #print("Saving Figure to SVG...")
            print("-------------")
            print(f.getvalue())
            sys.exit()

        if self.fmt == "svg":            
            self.figure.savefig(self.target.replace(".pdf",".svg"),format="svg",bbox_inches="tight",
                transparent=True)                        

        if self.fmt == "inlinepng":
            from io import StringIO
            f = StringIO()            
            self.figure.savefig(f,format="png",dpi=100,
                pad_inches=0.1,
                bbox_inches="tight",
                transparent=True)
            print("-------------")
            print(f.getvalue())
            sys.exit()
                    
        self.pdf.savefig(self.figure)
        if self.pages == 1:
            if self.preview is not None:
                plt.savefig(
                    self.preview,
                    dpi=100,
                    pad_inches=0.1,
                    bbox_inches="tight",
                    transparent=True,
                )
            
        try:
            self.figure.close()
        except:
            pass

        try:
            self.plt.close()
        except:
            pass

        try:
            self.pdf.close()
        except:
            pass

        if self.alerts is not None:
            try:
                fl = open(self.target.replace("pdf","alerts"),'w')
                for k in self.alerts:
                    fl.write(k + "\t" + self.alerts[k])
                fl.flush()
                fl.close()
            except:
                pass

        if len(self.datasummaries) > 0:            
            #Build a single data summary file from the various sub-files
            finalsummary = self.arguments.target + ".aijs"
            fl = open(finalsummary,"w")

            fl.write('{')

            indx = -1
            for nm,f in self.datasummaries:
                indx += 1

                try:
                    fx = open(f,"r")
                    content = fx.read()
                    fx.close()
                    if indx > 0:
                        fl.write(",\n")

                    fl.write('"' + str(nm) + '":')
                    fl.write(content)
                except:
                    pass

                try:
                    fx.close()
                    os.remove(f)
                except:
                    pass                

            fl.write('}')
            fl.flush()
            fl.close()

    def FailedAxis(self,ax,message="Invalid / No Data"):
        try:
            ax.axis('tight')
            ax.axis('off')
            ax.broken_barh([(0,1)],(0,1),facecolors=(1,0,0,0.2),edgecolor=(1,0,0,0.5),linestyle='--')            
            ax.text(0.5,0.5,message,verticalalignment='center',horizontalalignment='center')
            ax.set_xlim(0,1)
            ax.set_ylim(0,1)
        except:
            traceback.print_exc()
        
    def Grid(self,ax):
        ax.set_axisbelow(True)
        ax.yaxis.grid(color='gray', linestyle='dashed')
        ax.xaxis.grid(color='gray', linestyle='dashed')

    def GetCurrent(self,query):
        self.srv = self.GetARDIServer()
        qry = self.srv.StartQuery()
        result = qry.Execute(query)

        columns = []
        values = []

        for r in result['results']:
            if r['type'] == 'pointlist':
                for v in r['value']:                    
                    columns.append(v['name'] + " " + v['propname'])
                    try:
                        values.append(float(v['value']))
                    except:
                        values.append(v['value'])

        return pd.DataFrame(data = [values],columns=columns,index=[datetime.datetime.now()])

    def FetchHistory(self,query,**kwargs):
        kwargs["md"] = True
        return self.GetHistory(query,**kwargs) 

    def GetHistory(self,query,start=None,end=None,samples=None,method=None,utc=False,md=False):

        if "GETHISTORY" not in query:
            query += " {} GETHISTORY"
        
        self.srv = self.GetARDIServer()

        if samples is None:
            samples = 2000

        if start is None:
            start = self.defaultstart
            
        if end is None:
            end = self.defaultend

        if start is None:
            return None

        if end is None:
            end = LocalTimeToUTC(datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

        #Prepare the actual query
        qry = self.srv.StartQuery()        
        req = qry.StartHistoryRequest(query,start,end)
        req.chunks = 24
        req.samples = samples
        if utc == False:
            if self.tz is None:
                self.tz = pytz.timezone(self.timezonename)
            
            req.SetLocalTimezone(self.tz)
        if method == "raw":
            req.Raw()
        if method == "max":
            req.Max()
        if method == "min":
            req.Min()

        #Get the pandas data-frame with the results.
        return qry.GetHistory(req,md)

    def GetEvents(self,source=None,start=None,end=None,utc=True):
        if start is None:
            start = self.defaultstart
            
        if end is None:
            end = self.defaultend

        query='{"start": "' + str(start.strftime("%Y-%m-%d %H:%M:%S")) + '", "end": "' + str(end.strftime("%Y-%m-%d %H:%M:%S")) + '"'
        if source is not None:
            query += ',"sources": "' +  str(source) + '"'
            
        query += '} GETEVENTS'        
        
        self.srv = self.GetARDIServer()
        qry = self.srv.StartQuery()
        result = qry.Execute(query)

        resolved = []
        for n in result['results']:
            if n['type'] == 'map':
                for q in n['value']:
                    try:
                        q['start'] = datetime.datetime.strptime(q['start'],"%Y-%m-%d %H:%M:%S")
                        q['end'] = datetime.datetime.strptime(q['end'],"%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                    
                    if utc == False:
                        q['start'] = self.LocalTime(q['start'])
                        q['end'] = self.LocalTime(q['end'])
                    resolved.append(q)
            
        return resolved

    def Clear(self):
        self.pdf = None

    def TimeAxis(self,ax):
        ax.set_major_formatter(self.DateFormatter())

    def DurationUnit(self,start=None,end=None):
        if start is None:
            start = self.defaultstart
        if end is None:
            end = self.defaultend

        spn = (end - start).total_seconds()

        unit = 's'
        multiplier = 1

        if spn > 90:
            unit = 'm'
            multiplier = 60
        if spn > 5400:
            unit = 'h'
            multiplier = 60*60
        if spn > 172800:
            unit = 'days'
            multiplier = 60*60*24

        return (unit, multiplier)    

    def HeatMapTimeAxis(self,ax,samples,starttime=None,endtime=None):

        if starttime is None:
            starttime = self.LocalTime(self.defaultstart)
        if endtime is None:
            endtime = self.LocalTime(self.defaultend)
            
        xticks = []
        xticklabels = []
        xspot = starttime
        toffset = (endtime - starttime).total_seconds() / 8
        xoffset = samples / 8

        dateformat = self.DateFormat(starttime,endtime)
                
        plotx = 0
        while xspot <= endtime:
            xticks.append(plotx)
            xticklabels.append(xspot.strftime(dateformat))            
            xspot += datetime.timedelta(seconds=toffset)            
            plotx += xoffset

        ax.set_ticks(xticks)
        ax.set_ticklabels(xticklabels)

    def SimplifyTicks(self,ticks):
        common = None

        for x in range(0,len(ticks)):
            if ticks[x] != "":
                if common is None:
                    common = ticks[x]
                    continue

                ln = len(ticks[x])
                if len(ticks[x]) < ln:
                    ln = len(ticks[x])
                    common = common[0:ln]

                if ticks[x][0:ln] != common:
                    anymatch = None
                    for q in range(ln-1,1,-1):
                        if ticks[x][0:q] == common[0:q]:
                            anymatch = q
                            break
                    if anymatch is not None:
                        common = common[0:anymatch]
                    else:
                        common = None
                        break

        if common is None:
            return ticks
        
        trimlen = len(common)
        for t in range(0,len(ticks)):
            ticks[t] = ticks[t][trimlen:]

        common = None

        for x in range(0,len(ticks)):
            if ticks[x] != "":
                if common is None:
                    common = ticks[x]
                    continue

                ln = len(ticks[x])
                if len(ticks[x]) < ln:
                    ln = len(ticks[x])
                    common = common[len(common)-ln:]

                if ticks[x][0:ln] != common:
                    anymatch = None
                    for q in range(ln-1,1,-1):
                        if ticks[x][len(ticks[x])-q:] == common[len(common)-q:]:
                            anymatch = q
                            break
                    if anymatch is not None:
                        common = common[len(common)-anymatch:]
                    else:
                        common = None
                        break

        if common is None:
            return ticks
        
        trimlen = len(common)
        for t in range(0,len(ticks)):
            ticks[t] = ticks[t][0:len(ticks[t])-trimlen]

        return ticks

    def GetDefaultSequence(self):
        return ['g','b','y','m','c','r','purple','orange','silver']

    def GetDiscreteLegend(self,dta,col):

        from matplotlib.patches import Patch        

        namemap = dta.GetValueMap(col)
        colours = dta.GetColourMap(col)
        if len(colours) == 0:
            colours = self.GetDefaultSequence()
        
        named = []
        coloured = []
        for x in namemap:            
            if namemap[x] in named:
                    continue
            named.append(namemap[x])
            try:
                coloured.append(colours[x])
            except:
                if x == 0:
                    coloured.append('c')
                else:
                    if x == 1:                        
                        coloured.append('b')
                    else:
                        coloured.append('r')

        litems = []
        for q in range(0,len(named)):
                litems.append(Patch(facecolor=coloured[q],edgecolor=coloured[q],label=named[q]))

        return (litems,named)

    def GetDiscreteColourMap(self,dta,col):
        mp = dta.GetColourMap(col)
        indx = -1
        for x in mp:
            indx += 1
            if str(x)[0] == '#':
                mp[indx] = ardiapi.ParseHexColour(x[1:])
            else:
                mp[x] = ardiapi.ParseHexColour(mp[x])
            
        return mp

    def GetDiscreteValueMap(self,dta,col):
        return dta.GetValueMap(col)

    def GetAnalogueColourMap(self,dta,col):
        return self.GetAnalogColourMap(dta,col)

    def GetAnalogColourMap(self,dta,col):
        from matplotlib.colors import LinearSegmentedColormap
        md = dta.GetColumnData(col)
        
        if 'colours' in md:            

            minvalue = float(md['min'])
            maxvalue = float(md['max'])
            ran = maxvalue - minvalue
                          
            colours=[]
            nodes = []
            for x in md['colours']:
                if isinstance(x,str):
                    colours.append(ardiapi.ParseHexColour(x))
                    nodes.append((float(len(nodes)) - minvalue) / ran)
                else:
                    if len(nodes) == 0:
                        if float(x) > minvalue:
                            colours.append(ardiapi.ParseHexColour(md['colours'][x]))
                            nodes.append(0)
                            
                    colours.append(ardiapi.ParseHexColour(md['colours'][x]))
                    nodes.append((float(x) - minvalue) / ran)

            if nodes[len(nodes)-1] < 1:
                nodes.append(1)
                colours.append(colours[len(colours)-1])            
            
            cmap = LinearSegmentedColormap.from_list(col, list(zip(nodes, colours)))            
            
            return (cmap,minvalue,maxvalue)

        import matplotlib
        
        return matplotlib.cm.get_cmap('viridis')

    def GetARDIServer(self):
        if self.ardiserver is None:
            return None
        
        if self.srv is None:            
            self.srv = ardiapi.Server(self.ardiserver)
            
            if self.srv.Connect() == False:
                self.srv = None
                
        return self.srv
        
    def Failed(self,showex=True):
        try:
            import traceback
        except:
            pass

        self.Clear()

        fig,ax = self.CreatePage(1)

        self.Title(self.name)

        ax.text(0.5,0.65,"An Error Occured Generating This Chart",verticalalignment='top',horizontalalignment='center',fontsize=20,fontweight='bold')
        
        ax.text(0.5,0.35,"This is usually due to little or no activity during the reporting period.",verticalalignment='top',horizontalalignment='center',multialignment='center')
        
        try:
            content = traceback.format_exc()
            lines = content.split("\n")
            summary = lines[len(lines)-2]            

            ax.text(0.5,0.2,summary,verticalalignment='top',horizontalalignment='center',multialignment='center')
            
            traceback.print_exc()
        except:
            pass

        ax.axis('off')     

        self.Save()

    def UTCTime(self,tm):
        if self.tz is None:
            if self.timezonename == "UTC":
                self.tz = pytz.utc
            else:
                self.tz = pytz.timezone(self.timezonename)
                
        tm = tm.replace(tzinfo=self.tz)    
        tm = tm.astimezone(pytz.utc)
        tm = tm.replace(tzinfo=None)
        return tm

    def LocalTime(self,tm):
        if self.tz is None:
            if self.timezonename == "UTC":
                self.tz = pytz.utc
            else:
                self.tz = pytz.timezone(self.timezonename)
                
        tm = tm.replace(tzinfo=pytz.utc)    
        tm = tm.astimezone(self.tz)
        tm = tm.replace(tzinfo=None)
        return tm

    def LogEvent(self,name,duration,offset=0,options=None):
        if self.events is not None:
            self.events.Write(name,duration,offset=offset,options=options)        

    def LogValue(self,name,value,options=None):
        if self.keyvalue is not None:
            self.keyvalue.Set(name,value,options=options)        

    def AIChannel(self,name,data,precision=2):
        try:
            if self.arguments.nopng == True:
                return
        except:
            pass

        try:            

            dspath = self.arguments.target + "_" + name.replace(" ","_") + ".json"
            self.datasummaries.append((name,dspath))
            fl = open(self.arguments.target + "_" + name.replace(" ","_") + ".json",'w')            

            if data is None:
                fl.write("null")
            else:
                handled = False
                if isinstance(data,pd.Series):
                    #Process a pandas series...
                    arr = [0] * len(data.index)
                    indx = -1
                    for i,v in data.items():
                        indx += 1
                        arr[indx] = round(v,precision)
                    fl.write(json.dumps(arr))
                    handled = True
                if isinstance(data,pd.DataFrame):
                    #Process pandas dataframe...
                    arr = [0] * (len(data.index) * len(data.columns))
                    indx = -1
                    for c in data.columns:
                        ser = data[c]
                        for i,v in c.items():
                            indx += 1
                            arr[indx] = round(v,precision)
                            
                    fl.write(json.dumps(arr))                
                    handled = True

                if handled == False:
                    fl.write(json.dumps(data))
                    
            fl.flush()
            fl.close()
        except:
            traceback.print_exc()
            pass
