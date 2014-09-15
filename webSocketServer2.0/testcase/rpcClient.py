'''
Created on 2014-9-12

@author: Administrator
'''

from xmlrpclib import ServerProxy


svr=ServerProxy("http://10.86.8.132:8282")
svr.start_storm_server()
svr.press_CC_key()
svr.stop_storm_server()