'''
Created on Aug 22, 2014

@author: zhang.yizhong
'''
# -*- coding: utf8 -*-

import socket
import time
import threading
import hashlib
import base64
import struct
import json
import datetime
import logging
import sys


HOST = "10.86.8.71"
PORT = 81
event = threading.Event()
macKey = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
HSHAKE_RESP = "HTTP/1.1 101 Switching Protocols\r\n" + \
            "Upgrade: websocket\r\n" + \
            "Connection: Upgrade\r\n" + \
            "Sec-WebSocket-Accept: %s\r\n" + \
            "\r\n"


def configure_logging_level(level='info'):
    """Define log file and console log level and format.
    
    Args:
        level: console display log level, eg. info, debug
    """
    logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='webSocket.log',
                filemode='w')
    console = logging.StreamHandler()
    if level=='info':
        console.setLevel(logging.INFO)
    elif level=='debug':
        console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


class webSocketThread(threading.Thread):
    
    def __init__(self, port):
        threading.Thread.__init__(self)     
        self.received_data_from_stb = ''
        self.port = port
        self.online = True        
        self.start()
        logging.info(self.name + "\twebSocket thread start, waiting for connection")        
    
    def connect_client(self):
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
        sock.bind(('', self.port))
        sock.listen(10)
        connection, address = sock.accept()
        self.con = connection
        
        try:       
            logging.info(self.name + "\tStart hands shake with " + str(address))
            clientData  = self.con.recv(1024)
            logging.debug(self.name + "\tClient Data: \n" + clientData)   
            dataList = clientData.split("\r\n")
            header = {}
            for data in dataList:
                if ": " in data:
                    unit = data.split(": ")
                    header[unit[0]] = unit[1]
            secKey = header['Sec-WebSocket-Key'];         
            resKey = base64.b64encode(hashlib.sha1(secKey + macKey).digest())
            response = HSHAKE_RESP %(resKey, )
            logging.debug(self.name + "\tResponse Data: \n" + response)
            if(self.con.send(response)>=0):
                logging.info(self.name + "\tHands Shake Successfully")
            else:
                logging.warning(self.name + "\tHands Shake Fail")
                return False
            if self.send_packed_data("init"):
                logging.debug(self.name + "\tClient initialize successfully and start listening")
                return True                    
            else:
                logging.debug(self.name + "\tClient initialize fail")
                return False   
        except Exception, e:
            logging.error(self.name + e)
            return False
        
    def send_data_to_client(self, text):
        global event
        if not event.isSet():
            start_time = datetime.datetime.now()
            event.wait(600)
            end_time = datetime.datetime.now()
            if (end_time - start_time).seconds >= 599:
                logging.debug(self.name + '\tsend_data_to_client timeout')
                return False
        self.send_packed_data(text)
        return True
        
    def send_packed_data(self, data):  
        global event
        event.clear()
        #head
        self.con.send(struct.pack("!B",0x81))
        #calculate length
        length = len(data)
        if length<=125:
            self.con.send(struct.pack("!B",length))
        elif length<=65535:
            self.con.send(struct.pack("!B",126))
            self.con.send(struct.pack("!H",length))
        else:
            self.con.send(struct.pack("!B",127))
            self.con.send(struct.pack("!Q",length))
        self.con.send(struct.pack("!%ds"%(length,),data))
        return True
        
    def get_data_from_client(self):
        global event
        if not event.isSet():
            start_time = datetime.datetime.now()
            event.wait(600)
            end_time = datetime.datetime.now()
            if (end_time - start_time).seconds >= 599:
                logging.debug(self.name + '\tget_data_from_client timeout')
                return 
        return self.received_data_from_stb
        
    def close_dead_connection(self):
        self.online = False
        logging.info(self.name + "\twebSocket closed")
        global event
        event.clear()
    
    def close_active_connection(self):
        self.online = False
#        self.con.close()
        logging.info(self.name + "\twebSocket closed")
#        global event
#        event.clear()
        self.send_data_to_client('close')
        
    def run(self):
        if not self.connect_client():
            return
        while self.online:
            try:
                data_head = self.con.recv(1)
                print len(data_head)                
                if repr(data_head)=='':
                    logging.warning(self.name + "\tListening: empty data head, client disconnect")
                    self.close_connection()
                    return
        
                header = struct.unpack("B",data_head)[0]
                opcode = header & 0b00001111
#                print "Operate code %d"%(opcode,)
        
                if opcode==8:
                    logging.warning(self.name + "\tListening: Opcode error:" + str(opcode) + ", client disconnect")
                    self.con.close()
                    return
        
                data_length = self.con.recv(1)
                data_lengths= struct.unpack("B",data_length)[0]
                data_length = data_lengths& 0b01111111
                masking = data_lengths >> 7
                if data_length<=125:
                    payloadLength = data_length
                elif data_length==126:
                    payloadLength = struct.unpack("H",self.con.recv(2))[0]
                elif data_length==127:
                    payloadLength = struct.unpack("Q",self.con.recv(8))[0]
                logging.debug(self.name + "\tReceived data length:%d" %(data_length,))
                if masking==1:
                    maskingKey = self.con.recv(4)
                    self.maskingKey = maskingKey
                data = self.con.recv(payloadLength)
                global event
                if masking==1:
                    i = 0
                    true_data = ''
                    for d in data:
                        true_data += chr(ord(d) ^ ord(maskingKey[i%4]))
                        i += 1
                    self.received_data_from_stb = true_data
                else:
                    self.received_data_from_stb = data
                logging.debug(self.name + "\treceived_data_from_stb: %s" %(self.received_data_from_stb,))
                if self.received_data_from_stb == "ready":
                    logging.debug(self.name + "\tClient ready, set EVENT() true")
                    event.set()
#                elif self.received_data_from_stb == 'closed':
#                    self.con.close()
#                    self.online = False
#                    logging.debug("webSocket closed")
                else:
                    event.set()
                    
            except Exception,e:
                logging.critical(self.name + '\t' + str(e))
                self.con.close()
                return
            

if __name__ == '__main__':
    configure_logging_level()


    
    
    