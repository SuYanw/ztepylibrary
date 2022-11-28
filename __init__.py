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
