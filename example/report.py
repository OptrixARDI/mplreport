import os
import sys

#Add the parent directory to the path - this is where MPLReport and settings are normally found.
#sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))

#For this example, we import the functions in the 'src' folder instead. For real applications, comment this line out and uncomment the line above...
sys.path.insert(0,os.path.dirname(__file__) + "/../src")

import datetime
import mplreport

@mplreport.ardireport("A Sample")
def CreateReport(report,args):

    #Create a page containing a single plot.
    fig,ax = report.CreatePage(1)

    #Print a title block for the page.
    report.Title()    
    
    #Prepare an ARDI query
    query = "('Shearer') ASSET ('Closest Support') PROPERTY VALUES"

    #Get Query Results, along with metadata
    rdata = report.FetchHistory(query)

    #Get the pandas dataframe
    df = rdata.data

    #------------Start Report Body
    
    #Plot every column as a line graph
    for c in df.columns:
        ax.plot(df[c])

    #Make the report pretty

    ax.set_xlabel("Time")
    ax.set_ylabel("Measurement (units)")
    ax.margins(x=0)
    report.Grid(ax)
    report.TimeAxis(ax.xaxis)

    #------------Finish Report Body

    #Save this report out.
    report.Save()