# encoding: UTF-8

from __future__ import absolute_import
from .weixinEngine import WeixinEngine
from .uiWeixinWidget import WeixinEngineManager

appName = 'WeixinRecorder'
appDisplayName = u'微信下单记录'
appEngine = WeixinEngine
appWidget = WeixinEngineManager
appIco = 'dr.ico'
