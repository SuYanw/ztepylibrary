from classes.zte import ZTE 

if __name__ == '__main__':
    zte = ZTE("10.0.0.2", "admin", "1234")
    zte.login()
    zte.logout()


