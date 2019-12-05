#!/usr/bin/env python
# -*- coding: utf-8 -*-
#############################



import ConfigParser
import string
import os
import subprocess
import time
import sys
import json

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish


conf={}
vcpath="/usr/bin/vcgencmd"



def getbit(x,n):
  """Get the n-th bit of the number x"""
  return x & (1 << n) and 1 or 0


def get_script_path():
    """return the path of the currently running script"""
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def LoadConfig(file, config={}):
    """
    returns a dictionary with keys of the form
    <section>.<option> and the corresponding values
    """
    config = config.copy(  )
    cp = ConfigParser.ConfigParser(  )
    cp.read(file)
    for sec in cp.sections(  ):
        name = string.lower(sec)
        obj  = { }
        for opt in cp.options(sec):
            obj[string.lower(opt)] = string.strip(
                cp.get(sec, opt))
        config[name]=obj
    return config

def cpu_usage():
    # load average, uptime
    #uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    av1, av2, av3 = os.getloadavg()
    return "%.1f %.1f %.1f" \
            % (av1, av2, av3)

def checkThings():
    health={"_type":"health","id":conf['settings']['id']}
    # temp
    p = subprocess.Popen([vcpath,"measure_temp"], stdout=subprocess.PIPE)
    val, err = p.communicate()
    val=val.replace('temp=','').replace("'C","").strip()
    health["temp"]=val

    # current CPU frequence
    p = subprocess.Popen([vcpath,"measure_clock","arm"], stdout=subprocess.PIPE)
    val, err = p.communicate()
    val=val.replace('frequency(45)=','').strip()
    health["clock"]=val

    # current core voltage
    p = subprocess.Popen([vcpath,"measure_volts"], stdout=subprocess.PIPE)
    val, err = p.communicate()
    val=val.replace('volt=','').replace("'V","").strip()
    health["volt"]=val

    # RAM
    p = subprocess.Popen([vcpath,"get_mem","arm"], stdout=subprocess.PIPE)
    val, err = p.communicate()
    val=val.replace('arm=','').replace("M","").strip()
    health["ram"]=val

    # graphic Ram
    p = subprocess.Popen([vcpath,"get_mem","gpu"], stdout=subprocess.PIPE)
    val, err = p.communicate()
    val=val.replace('gpu=','').replace("M","").strip()
    health["gram"]=val

    # RAM usage
    tot_m, used_m, free_m = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
    val="total: "+str(tot_m)+" used: "+str(used_m)+" free: "+str(free_m)
    health["memuse"]=val

    # cpu-load
    av1, av2, av3 = os.getloadavg()
    val=str(av1)+" "+str(av2)+" "+str(av3)
    health["cpuload"]=val

    # throttled
    # vcgencmd get_throttled
    p = subprocess.Popen([vcpath,"get_throttled"], stdout=subprocess.PIPE)
    hexval, err = p.communicate()
    val=hexval.replace('throttled=','').strip()
    hex_int=int(val, 16)

    # 0: under-voltage
    if getbit(hex_int,0):
        val="ON"
    else:
        val="OFF"
    health["under_voltage"]=val


    #1: arm frequency capped
    if getbit(hex_int,1):
        val="ON"
    else:
        val="OFF"
    health["frequency_capped"]=val


    #2: currently throttled
    if getbit(hex_int,2):
        val="ON"
    else:
        val="OFF"
    health["throttled"]=val

    #16: under-voltage has occurred
    if getbit(hex_int,16):
        val="ON"
    else:
        val="OFF"
    health["under_voltage_once"]=val


    #17: arm frequency capped has occurred
    if getbit(hex_int,17):
        val="ON"
    else:
        val="OFF"
    health["frequency_capped_once"]=val


    #18: throttling has occurred
    if getbit(hex_int,18):
        val="ON"
    else:
        val="OFF"
    health["throttled_once"]=val

    #finito: publish
    publishDict(health)

############### MQTT section ##################

# when connecting to mqtt do this;

def on_connect(client, userdata, flags, rc):
    #print("Connected with result code "+str(rc))
    client.subscribe(cmdTopic)

# when receiving a mqtt message do this;

def on_message(client, userdata, msg):
    message = str(msg.payload)
    #print(msg.topic+" "+message)

def on_publish(mosq, obj, mid):
    #print("mid: " + str(mid))


def publishDict(obj):
    #print obj
    json_string = json.dumps(obj)
    #print json_string
    #print pubTopic
    client.publish(pubTopic,json_string,1)

# begin
conf=LoadConfig(get_script_path()+"/"+"settings.ini", conf)

mqbroker = conf['settings']['mqbroker']
mquser =   conf['settings']['mquser']
mqpasswd = conf['settings']['mqpasswd']
mqport   = conf['settings']['mqport']
# mqtt
pubTopic="raspi/health/"+conf['settings']['id']+"/state"
cmdTopic="raspi/health/"+conf['settings']['id']+"/cmd"

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.username_pw_set(mquser,mqpasswd)
client.connect(mqbroker, mqport, 60)
time.sleep(1)
client.loop_start()





try:
  # loop
  while 1:
    checkThings()
    time.sleep(float(conf['settings']['interval']))
except:
  client.loop_stop()
  client.disconnect()
  time.sleep(1)


