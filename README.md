# MPLReport
The ARDI reporting engine library

## Description
A helper library designed to make it extremely quick and efficient to make MatPlotLib reports, along with a number of additional features specifically targeted at the ARDI reporting engine.

## Report Parameters
If running examples/development reports outside the ARDI server, the following parameters are required...

Start Date (YYYY-MM-DD, Local Time)
End Date (YYYY-MM-DD, Local Time)
Output File (Without Extension)
Timezone (UTC or Region/City)
--server <url> (URL to ARDI server, without prefix/http)

### report.py "2024-09-30 05:00:00" "2024-10-01 05:00:00" "OutputFile" "Australia/Sydney" --server localhost/s/default