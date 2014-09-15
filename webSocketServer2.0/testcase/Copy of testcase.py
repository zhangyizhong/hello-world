'''
Created on Sep 3, 2014

@author: zhang.yizhong
'''
from pywebsocketserver.webSocketServer import webSocketThread,configure_logging_level
import time

            
def test_error_page():
    result = "No.\tTest Steps\t\tResult\n-------------------------------------------\n"
    soket_login = webSocketThread(81)  
    
    #step1:click login button without user name and password 
    step1 = "document.getElementById('login_button').click()"
    #start webSocket server for page navigation
    soket_error_page = webSocketThread(82)
    if not soket_login.send_data_to_client(step1):
        print "command send fail \t click login button"
        return False
    result += "step1\tclick login button\tpass\n"
    
    #step2:check the page title
    step2 = "document.getElementById('error').textContent"
    if not soket_error_page.send_data_to_client(step2):
        print "command send fail \t get error page title"
        return False
    result += "step2\tget error page title\tpass\n"
    
    if soket_error_page.get_data_from_client().find("Error Page") == -1:
        print "jump to error page fail"
        return False
    result += "step3\tcheck error page title\tpass\n" 
    soket_error_page.close_connection()
    print result
    print 'complete test'
    
    
def test_welcom_page():
    result = "No.\tTest Steps\t\tResult\n-------------------------------------------\n"
    soket_login = webSocketThread(81)  
    
    #step1:input correct user name 
    step1 = "document.getElementById('username_field').value='demo'"
    if not soket_login.send_data_to_client(step1):
        print "command send fail \t input user name"
        return False
    if soket_login.get_data_from_client().find("demo") == -1:
        print "command get fail \t input user name"
        return
    result += "Step1\tinput user name\t\tpass\n"
    time.sleep(2)

    #step2:input correct password 
    step2 = "document.getElementById('password_field').value = 'mode'"
    if not soket_login.send_data_to_client(step2):
        print "command send fail \t input password"
        return False
    if soket_login.get_data_from_client().find("mode") == -1:
        print "command get fail \t input password"
        return False
    result += "Step2\tinput password\t\tpass\n"
    time.sleep(2)
    
    #step3:click login button
    step3 = "document.getElementById('login_button').click()"
    soket_welcom_page = webSocketThread(82)
    if not soket_login.send_data_to_client(step3):
        print "command send fail \t click login button"
        return False
    result += "Step3\tclick login button\tpass\n"
    
    #step4:get login page title
    step4 = "document.getElementById('welcome').textContent"
    if not soket_welcom_page.send_data_to_client(step4):
        print "command send fail \t get page title"
        return False
    result += "Step4\tget login page title\tpass\n"
    
    #step5:check login page title
    if soket_welcom_page.get_data_from_client().find("Welcome Page")==-1:
        print "command get fail \t check page title"
        return False
    result += "Step5\tcheck login page title\tpass\n"
    soket_welcom_page.close_connection()
    print result
    print 'complete test'



if __name__ == '__main__':
    configure_logging_level('debug')
    test_error_page()
    
    