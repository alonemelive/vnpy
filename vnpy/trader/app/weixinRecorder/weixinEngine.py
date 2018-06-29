# encoding: UTF-8

'''
本文件中实现了微信企业号下单记录引擎，用于通知企业号下单的记录信息.

使用WX_setting.json来配置需要收集的合约，以及主力合约代码。
'''

import json
import csv
import os
import copy
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta
from Queue import Queue, Empty
from threading import Thread
import urllib2

from vnpy.event import Event
from vnpy.trader.vtEvent import *
from vnpy.trader.vtFunction import todayDate, getJsonPath
from vnpy.trader.vtObject import VtSubscribeReq, VtLogData, VtBarData, VtTickData
from vnpy.trader.app.ctaStrategy.ctaTemplate import BarGenerator

#from .drBase import *
from .language import text


########################################################################
class WeixinEngine(object):
    """数据记录引擎"""
    
    settingFileName = 'WX_setting.json'
    settingFilePath = getJsonPath(settingFileName, __file__)  

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        
        # 当前日期
        self.today = todayDate()
        
        # 主力合约代码映射字典，key为具体的合约代码（如IF1604），value为主力合约代码（如IF0000）
        self.activeSymbolDict = {}
        
        # Tick对象字典
        self.tickSymbolSet = set()
        
        # K线合成器字典
        self.bgDict = {}
        
        # 配置字典
        self.settingDict = OrderedDict()

        self.WXuser=None
        self.WXcorpid=None
        self.WXcorpsecret=None
        self.WXaccesstoken=None
        
        # 载入设置，订阅行情
        self.loadSetting()
        
        # 注册事件监听
        self.registerEvent()  
        self.sendWXdata ( self.WXaccesstoken, self.WXuser, "开始微信通知...", self.WXagentid )

    
    #----------------------------------------------------------------------
    def loadSetting(self):
        """加载配置"""
        with open(self.settingFilePath) as f:
            setting = json.load(f)
            self.WXuser = str(setting['WXuserID'])
            self.WXcorpid = str(setting['WXcorpid'])
            self.WXcorpsecret = str(setting['WXcorpsecret'])
            self.WXagentid = str(setting['WXagentid'])

            if self.WXaccesstoken is None:
                self.WXaccesstoken = self.getToken(self.WXcorpid, self.WXcorpsecret)
    
    def processOrderEvent(self, event):
        """处理委托事件"""
        print ("weixinEngine.....processOrderEvent \n")
        order = event.dict_['data']
        order.orderTime = datetime.now().strftime('%m%d-%H:%M:%S')
        content = '-'.join ( [ str(order.vtSymbol), str(order.direction), str(order.offset) , str(order.price), str(order.volume), str(order.orderTime) ] )
        self.sendWXdata ( self.WXaccesstoken, self.WXuser, content, self.WXagentid )

    def sendWXdata(self, access_token,user,content, agentid):
        send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + access_token
        send_values = {
            "touser":user,    #企业号中的用户帐号，在用户Media中配置，如果配置不正常，将按部门发送。
            "toparty":"1",    #企业号中的部门id
            "msgtype":"text",  #企业号中的应用id，消息类型。
            "agentid":agentid,
            "text":{
                "content":content
            },
            "safe":"0"
        }
        send_data = json.dumps(send_values, ensure_ascii=False)
        send_request = urllib2.Request(send_url, send_data)
        response = json.loads(urllib2.urlopen(send_request).read())
        #print str(response)

    def getToken(self,corpid,corpsecret):
        gettoken_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=' + corpid + '&corpsecret=' + corpsecret
        try:
            token_file = urllib2.urlopen(gettoken_url)
        except urllib2.HTTPError, e:
            print e.code
            print e.read().decode("utf8")
        token_data = token_file.read().decode('utf-8')
        token_json = json.loads(token_data)
        token_json.keys()
        token = token_json['access_token']
        return token

    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.eventEngine.register(EVENT_PRE_ORDER, self.processOrderEvent)
        self.eventEngine.register(EVENT_PRE_CANCEL_ORDER, self.processOrderEvent)

 
    #----------------------------------------------------------------------
    def start(self):
        """启动"""
        pass
    #----------------------------------------------------------------------
    def stop(self):
        """退出"""
        pass
    #----------------------------------------------------------------------
    def writeDrLog(self, content):
        """快速发出日志事件"""
        log = VtLogData()
        log.logContent = content
        event = Event(type_=EVENT_DATARECORDER_LOG)
        event.dict_['data'] = log
        self.eventEngine.put(event)   
    
