# Read first
This tool can only run under Linux for now.

This program can **only test the speed** of some vmess connections, you need to do more steps to use these connection informations which is not involved in this tool.

# Structure:
- data/		to store tested json files
- json/		to store old tested json files
- autovm.py	to test vmesses
- vm2jsn.py	to convert vmess to json
- vping		to ping vmess
- vspeed	to test speed of vmess
- youneedwind.html	vmess informations

# How to use:
1. You need to have the access of Google.com first because the website of youneedwind and subscription urls are all blocked by the GFW.
2. create directory **data** and **json** if there does not.
3. Go to [youneedwind.html](https://www.youneed.win/free-v2ray) and complete the simple verification.
4. Download the whole page to ./youneedwind.html (Note: filename must be exactly ***youneedwind.html***)
5. Run `./autovm.py` and wait to finish

The tested vmesses are converted to json files and stored in data/, the programe will move everything in data/ to json/ **automatically**, no need to clean files under json/ before run autovm cause the program will cover files with the same name.

The tested vmess share links are stored in vmOut.txt file with download, upload, location informations.

Name of jsons are based on the speed of each vmess, just simply use them in numerical order.

# Additional steps
You can use any graphical tools to manage vmess connections such as [qv2ray](https://github.com/Qv2ray/Qv2ray), [v2rayN](https://github.com/2dust/v2rayN), [v2rayA](https://github.com/v2rayA/v2rayA), simply import from json files or import from vmess share links.

or use [xray-core](https://github.com/XTLS/Xray-core) which need more modifications but light weight and can be modified in a more flexible way.

# Credits
This project relies on the following third-party projects:

- vping and vspeed:
  - [v2fly/vmessping](https://github.com/v2fly/vmessping)
- vm2jsn.py:
  - [boypt/vmess2json](https://github.com/boypt/vmess2json)
