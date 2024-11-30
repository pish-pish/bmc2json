# Gamecube/Wii BMC to JSON Converter by PishPish

A tool to convert BinaryMessageColor (BMC) files to JSON and back to BMC.

*Requires Python 3.12+*

### Usage:
1. Drag and drop *.BMC files onto `convertbmc.bat` to convert to JSON. 

*This batch script contains an optional parameter to group colors by a specified group size. The default group size is `1`.

2. The outputted json will be a list of hex color strings. Adding or removing color entries is supported.
3. Once done editing, drag the json onto `convertjson.bat` to convert the file back to BMC and save your changes.
