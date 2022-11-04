import os
import re
import time
import paramiko as paramiko
from paramiko import AutoAddPolicy
import unidecode



DEFAULT_MAX_SSH_RECV    = 99999999
DEFAULT_SLEEP_COMMAND   = 0.5 
DEFAULT_MAX_ONU_PER_PON = 256


class ZTE:
    





    '''
        @doc: Init function
        @description: initialization of function
        @input_params: IP-ADDRESS, USERNAME, PASSWORD, PORT
    ''' 
    def __init__(self, ipaddr, username, password, port=22):


        self.sshtunnel = paramiko.SSHClient()
        self.sshtunnel.load_system_host_keys()
        self.sshtunnel.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #self.sshtunnel.set_missing_host_key_policy(paramiko.WarningPolicy())

        self.__username = username
        self.__password = password
        self.__ipaddr   = ipaddr
        self.__port     = port

        self.__connected = False
        self.__online = False

        if(os.system(f'ping -c 1 -w2 {ipaddr} > /dev/null 2>&1') > 0):
            self.__connected = False
            self.__online = False
        else:
            self.__online = True





    '''
        @doc: login
        @description: log-in on OLT
        @input_params: 
        @output_type: bool
        @output_params: if logged return true, returns false if not
    '''  
    def login(self):
        if not (self.__online):
            self.__connected = False
            return False
        
        # Login SSH
        self.sshtunnel.connect(
                    hostname=self.__ipaddr, 
                    username=self.__username, 
                    password=self.__password, 
                    port=self.__port)

        self.Bash = self.sshtunnel.invoke_shell()
        self.Bash.send("terminal length 0\n")

        self.__connected = True
        return True





    '''
        @doc: logout
        @description: log-out on OLT
        @input_params: 
        @output_type: bool
        @output_params: if logged login out, returns false if already not logged
    '''  
    def logout(self):
        if not (self.__connected):
            return False

        self.Bash.send(b"end\n")
        time.sleep(1)

        self.Bash.send(b"exit\n")
        time.sleep(1)

        self.sshtunnel.close()
        self.__connected = False
        return True







    '''
        @doc: getOnuUnAuth
        @description: Show ONUs pending adoption
        @input_params: None
        @output_type: Array
        @output_params: [
            Chassis-ID,
            Board-ID,
            Pon-ID,
            Model whithout-version,
            Serial Number (starter with ZTE tag), 
            PW
            
        ]
    '''  
    def getOnuUnAuth(self):

        if not (self.__connected):
            return False


        self.Bash.send(b"show pon onu uncfg\n")
        time.sleep(1)
        getUnauthorizedOnu = self.Bash.recv(DEFAULT_MAX_SSH_RECV)
        

        __out_rtn = []
        for line in getUnauthorizedOnu.splitlines(True):
            __line = line.decode('utf-8')
            if(re.search("gpon_olt", __line) is not None):
                __tmp_line = list(filter(None, re.split(r"[\s+]", __line)))

                
                ## Chassis, Placa, Pon
                __out_rtn = __out_rtn + re.split("/",re.sub("gpon_olt-", "", __tmp_line[0]))
                
                # Modelo (retirando a versão)  F670LV1.1.01 ficará F670L
                __out_rtn.append(re.findall("F[0-9]{3}[A-Z]?", __tmp_line[1])[0])

                ## MAC
                __out_rtn.append(__tmp_line[2])

                ## SN
                __out_rtn.append(__tmp_line[3])

        if not (len(__out_rtn)):
            return None
        else:
            return [
                    __out_rtn
            ]






    '''
        @doc: onuun
        @description: Check if onu is pending adoption
        @input_params: onu-mac
        @output_type: Bool
        @output_params: Return True if onu pending, False if not
    '''  
    def isOnuPending(self, onu):

        if not (self.__connected):
            return False

        OnuList = self.getOnuUnAuth()

        if(OnuList is None):
            return None
        
        for __onu in OnuList:
            if(__onu == onu):
                return True

        return False







    '''
        @doc: setAuthOnu
        @description: Auth ONu on the board
        @input_params: Chassi, Board, Pon, Onuid, Model, SN
        @output_type: Bool
        @output_params: Return True if successfull, False if not
    ''' 
    def setAuthOnu(self, chassi, board, pon, onuid, model, sn):

        if not (self.__connected):
            return False

        self.Bash.send(f"config terminal\ninterface gpon_olt-{chassi}/{board}/{pon}\nonu {onuid} type {model} sn {sn}\nend\n")

        time.sleep(DEFAULT_SLEEP_COMMAND * 2)
        
        if(str(self.Bash.recv(DEFAULT_MAX_SSH_RECV)).find("Error") == -1):
            return True
        else:
            return False





    '''
        @doc: getPonAvailableId
        @description: Get available ONU ID on PON
        @input_params: Chassi, Board, Pon
        @output_type: int
        @output_params: Return id available, if pon is full, return -1
    ''' 
    def getPonAvailableId(self, classi, board, pon):

        if not (self.__connected):
            return False

        self.Bash.send(f"config terminal\ninterface gpon_olt-{classi}/{board}/{pon}\nshow this\nend\n")
        time.sleep(DEFAULT_SLEEP_COMMAND)

        __getTerminalOut = self.Bash.recv(DEFAULT_MAX_SSH_RECV)
        time.sleep(DEFAULT_SLEEP_COMMAND)

        __pon_numbers = []
        for __raw_onu in __getTerminalOut.splitlines(True):
            __onu = __raw_onu.decode('utf-8')

            if(re.search("onu\s[0-9]{1,3}\stype", __onu) is not None):
                __pon_numbers.append(int(str(re.findall("\s[0-9]{1,3}\s",__onu)[0])))

        __pon_numbers_size = len(__pon_numbers)

        if(__pon_numbers_size == DEFAULT_MAX_ONU_PER_PON):
            return 0

        _y = 1
        while(_y <= __pon_numbers_size-1):

            if(__pon_numbers[_y-1] != _y):
                break

            _y = _y + 1
    
        return (_y == __pon_numbers_size and _y+1 or _y)





    '''
        @doc: getOnuInfoBySN
        @description: Get onu information by Serial Number
        @input_params: Onu Serial number(started by ZTE-tag)
        @output_type: array
        @output_params: [
            Chassis-Id,
            Board-id
            Pon-Id
            Onu-id
        ]
    ''' 
    def getonuinfobysn(self, onusn):

        if not (self.__connected):
            return False

        self.Bash.send("show gpon onu by sn {}\n". format(onusn))
        time.sleep(DEFAULT_SLEEP_COMMAND)
        
        getOnuRtn = self.Bash.recv(DEFAULT_MAX_SSH_RECV)
        for line in getOnuRtn.splitlines(True):
            if(str(line).find("gpon_onu") != -1):
                
                istr = re.sub('[^[0-9\/\:]*', "", str(line)).split("/")

                return [
                    istr[0],
                    istr[1],
                    istr[2].split(":")[0],
                    istr[2].split(":")[1]
                ]
        
        return None






    '''
        Pega o ID da ONU pelo Serial Number (SN)
    '''
    def getonuidbysn(self, onusn):
        return self.getonuinfobysn(onusn)[3]

    '''
        Pegar id do chassi by sn
    '''
    def getonuchassisbysn(self, onusn):
        return self.getonuinfobysn(onusn)[0]


    '''
        Pegar id do Placa by sn
    '''
    def getonuboardbysn(self, onusn):
        return self.getonuinfobysn(onusn)[1]


    '''
        Pegar id do Pon by sn
    '''
    def getonuponbysn(self, onusn):
        return self.getonuinfobysn(onusn)[2]

    '''
        Verificar se ONU está autenticada
    '''
    def isonuauth(self, onusn):
        return self.getonuinfobysn(onusn) != None

    '''
        Coletar última ONU Provisionada
    '''
    def getlastonu(self, onuchassi, onuplaca, onupon):
        return self.getPonAvailableId(onuchassi, onuplaca, onupon)


    '''
        Verificar se ONU está pedindo autorização
        em determinada PON
    '''
    def onuwhitelist(self, chassi, placa, pon, sn):
        rtn = self.getOnuUnAuth(sn)
        if(rtn != None):
            if(rtn[0] == chassi and rtn[1] == placa and rtn[2] == pon):
                return 1
            else:
                return 0
        else:
            return 0






    '''
        @doc: setOnuName
        @description: Set Onu Name
        @input_params: Chassi, Board, Pon, Onuid, Name
        @output_type: bool
        @output_params: True if successful named.

    ''' 
    def setOnuName(self, onuchassi, onuplaca, onupon, onuid, name):

        if not (self.__connected):
            return False

        self.Bash.send(f"config terminal\ninterface gpon_onu-{onuchassi}/{onuplaca}/{onupon}:{onuid}\nname {unidecode.unidecode(name)}\nend\n")
        time.sleep(DEFAULT_SLEEP_COMMAND)
        
        if(str(self.Bash.recv(DEFAULT_MAX_SSH_RECV)).find("Error") == -1):
            return True
        else:
            return False





    '''
        @doc: setOnuProfile
        @description: Set velocity profile
        @input_params: Chassi, Board, Pon, Onuid, tCont, ProfileName
        @output_type: bool
        @output_params: True if successful applyed.

    ''' 
    def setOnuProfile(self, onuchassi, onuplaca, onupon, onuid, tcont, profilename):

        if not (self.__connected):
            return False

        self.Bash.send(f"config terminal\ninterface gpon_onu-{onuchassi}/{onuplaca}/{onupon}:{onuid}\ntcont {tcont} profile {profilename}\ngemport {tcont} tcont {tcont}\nend\n")

        time.sleep(DEFAULT_SLEEP_COMMAND)
        
        if(str(self.Bash.recv(DEFAULT_MAX_SSH_RECV)).find("Error") == -1):
            return True
        else:
            return False



            
    '''
        @doc: SetOnuPortBridge
        @description: Set OnuPortBridge
        @input_params: Chassi, Board, Pon, Onuid, port, vlan, service (op, def is 1), gemport(op def is 1)
        @output_type: bool
        @output_params: True if successful applyed.

    ''' 
    def setOnuPortBridge(self, onuchassi, onuplaca, onupon, onuid, port, vlan, service = 1, gemport = 1):

        if not (self.__connected):
            return False


        self.Bash.send(f"config terminal\npon-onu-mng gpon_onu-{onuchassi}/{onuplaca}/{onupon}:{onuid}\nservice {service} gemport {gemport} ethuni ETH_0/{port} cos 0 vlan {vlan}\nvlan port ETH_0/{port} mode tag vlan {vlan}\nend\n")

        time.sleep(DEFAULT_SLEEP_COMMAND)
        
        if(str(self.Bash.recv(DEFAULT_MAX_SSH_RECV)).find("Error") == -1):
            return True
        else:
            return False



            
    '''
        @doc: setOnuBridgeVport
        @description: Set onu Bridge vPort
        @input_params: Chassi, Board, Pon, Onuid, vport, vlan, service (op, def is 1)
        @output_type: bool
        @output_params: True if successful applyed.
    ''' 
    def setOnuBridgeVport(self, onuchassi, onuplaca, onupon, onuid, vport, vlan, service = 1):

        if not (self.__connected):
            return False


        self.Bash.send(f"config terminal\ninterface vport-{onuchassi}/{onuplaca}/{onupon}.{onuid}:{vport}\nservice-port {service} user-vlan {vlan} vlan {vlan}\nend\n")
        time.sleep(DEFAULT_SLEEP_COMMAND)

        if(str(self.Bash.recv(DEFAULT_MAX_SSH_RECV)).find("Error") == -1):
            return True
        else:
            return False



            
    '''
        @doc: setOnuiPoE
        @description: Set onu iPoE Mode
        @input_params: Chassi, Board, Pon, Onuid, vlan, service(op, def is 1)
        @output_type: bool
        @output_params: True if successful applyed.
    ''' 
    def setOnuiPoE(self, onuchassi, onuplaca, onupon, onuid, vlan, service=1):

        if not (self.__connected):
            return False


        self.Bash.send(f"config terminal\npon-onu-mng gpon_onu-{onuchassi}/{onuplaca}/{onupon}:{onuid}\nservice {service} gemport {service} vlan {vlan}\nwan-ip ipv4 mode dhcp vlan-profile {vlan} host 1\nend\n")
        time.sleep(DEFAULT_SLEEP_COMMAND)

        if(str(self.Bash.recv(DEFAULT_MAX_SSH_RECV)).find("Error") == -1):
            return True
        else:
            return False



            
    '''
        @doc: setOnuBridge
        @description: Set onu iPoE Mode
        @input_params: Chassi, Board, Pon, Onuid, vlan, service(op, def is 1)
        @output_type: bool
        @output_params: True if successful applyed.
    ''' 
    def setOnuBridge(self, onuchassi, onuplaca, onupon, onuid, port, vlan):

        if not (self.__connected):
            return False

        self.Bash.send(f"config terminal\npon-onu-mng gpon_onu-{onuchassi}/{onuplaca}/{onupon}:{onuid}\nservice y gemport y vlan {vlan}\nvlan port eth_0/{port} mode tag vlan {vlan}\nend\n")
        time.sleep(DEFAULT_SLEEP_COMMAND)

        if(str(self.Bash.recv(DEFAULT_MAX_SSH_RECV)).find("Error") == -1):
            return True
        else:
            return False