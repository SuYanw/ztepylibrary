# Python OLT ZTE Library
This is an ZTE library for Python, basic functions to manage your provider OLT!


## Examples
```python

from classes.zte import ZTE 

if __name__ == '__main__':

    zte = ZTE("10.0.0.2", "admin", "1234")

    out_array = []

    if(zte.login()):
        getOnus = zte.getOnuUnAuth()
        zte.logout()

        
        if not (getOnus is None):
            for onu in getOnus:
                out_array.append(onu[4])
    else:
        return "Error for connecting on OLT"

    zte.logout()
```



## Main Functions:
```python
login() #Log-in on OLT
logout() #log-out in olt
getOnuUnAuth() # Show ONUs pending adoption
onuun(onu_sn) # Check if onu is pending adoption
setAuthOnu(chassi, board, pon, onuid, model, sn) # adopt Onu on the OLT
getPonAvailableId(classi, board, pon) # Get available ONU ID on PON
getOnuInfoBySN(onu_sn) # Get onu information by Serial Number
onuwhitelist(chassi, board, pon, sn) # check Onu is pending on specified slot
setOnuName(chassi, board, pon, onuid, name) # set onu name 
setOnuProfile(chassi, board, pon, uid, tcont, profilename) # set onu profile and tcont
setOnuPortBridge(chassi, board, pon, onuid, port, vlan) # Set onu mode bridge
setOnuBridgeVport(chassi, board, pon, uid, vport) # set onu Bridge vport
setOnuiPoE(chassi, board, pon, onuid, vlan) # Set onu iPoE Mode
setOnuBridge(chassi, board, pon, onuid, port vlan) # Set onu Bridge Mode
```



## Testing
Already tested on this software in procution cases:
```
OLT ZTE C610, Ver: ZTE ZXA10 Software, Version: V1.2.1, Release software
OLT ZTE C650, Ver: ZTE ZXA10 Software, Version: V1.2.2, Release software
```

## Internal Adjustmments
``` python
DEFAULT_MAX_SSH_RECV    = 99999999  # Max recevied for ssh conn 
DEFAULT_SLEEP_COMMAND   = 0.5  # default sleep command for recevied response
DEFAULT_MAX_ONU_PER_PON = 256 # max pon per board on olt
```