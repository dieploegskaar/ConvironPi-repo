#!/usr/bin/env python3
import threading
import time
import datetime
import RPi.GPIO as GPIO
from bmp280 import BMP280
import psutil
import csv
import os

Mrng_MaxTemp = 8.0                      #Define Morning Tempreature
Day_MaxTemp = 15.0                      #Define Day Tempreature
Evng_Maxtemp = 8.0                      #Define Evening Tempreature
Night_Maxtemp = 5.0                     #Define Night Tempreature

GPIO.cleanup()
#If there ara any other processes using the GPIO pins , Kill it firs
for proc in psutil.process_iter():
    if proc.name() == 'libgpiod_pulsein' or proc.name() == 'libgpiod_pulsei':
        proc.kill()
        
try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

bus = SMBus(1)                            #Settin up I2C Bus
bmp280 = BMP280(i2c_dev=bus)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)                    #Setup use to use GPIO port numbers
GPIO.setup(17, GPIO.OUT)                  #GPIO17 contols compressor solenoid valve physical pin11
GPIO.setup(27, GPIO.OUT)                  #LED Bank 1
GPIO.setup(22, GPIO.OUT)                  #LED Bank 2
GPIO.setup(23, GPIO.OUT)                  #LED Bank 3
GPIO.setup(24, GPIO.OUT)                  #LED Bank 4
GPIO.setup(25, GPIO.OUT)                  #LED Bank 5
GPIO.setup(16, GPIO.OUT)                  #Blower Fans
GPIO.setup(26, GPIO.OUT)                  #Heating elemts
GPIO.output(17,False)                     #At startup first turn all outputs/relays off
GPIO.output(27,False)
GPIO.output(22,False)
GPIO.output(23,False)
GPIO.output(24,False)
GPIO.output(25,False)
GPIO.output(16,True)                       #Start blower fan when machine starts
GPIO.output(26,False)
time.sleep(3)

def Lighting_Timer():
    while True:     
        now = datetime.datetime.now()
        onTime = now.replace(hour = 8, minute = 0, second  = 0, microsecond = 0)    # set hours to start turning on leds
        offTime = now.replace(hour = 16, minute = 0, second  = 0, microsecond = 0)  # set time to start turnomg leds off
        LEDsOn = now > onTime and now < offTime
        LEDsOff = now > offTime or now < onTime
        if(LEDsOn == True):
            GPIO.output(27,True)
            time.sleep(1200)          #wait 20 minutes before turning on next LED bank(cascaded to simulate sunrise/sunset)
            GPIO.output(22,True)
            time.sleep(1200)
            GPIO.output(23,True)
            time.sleep(1200)
            GPIO.output(24,True)
            time.sleep(1200)
            GPIO.output(25,True)
        if(LEDsOff == True):
            GPIO.output(25,False)
            time.sleep(1200)
            GPIO.output(24,False)
            time.sleep(1200)
            GPIO.output(23,False)
            time.sleep(1200)
            GPIO.output(22,False)
            time.sleep(1200)
            GPIO.output(27,False)

def Cooling():
    GPIO.output(26,False)   #Heating OFF
    GPIO.output(17,True)    #cooling ON

def Heating():
    GPIO.output(17,False)   #Cooling OFF
    GPIO.output(26,True)    #Heating ON
    time.sleep(12.0)
    GPIO.output(26,False)
    time.sleep(30.0)

def In_Range():
    time.sleep(5.0)
    GPIO.output(17,False)   #Cooling OFF
    GPIO.output(26,False)   #Heating OFF
    time.sleep(25.0)
     
def Temp_Control(): #Tempreature sensing and control
    while True:
        try:
            now = datetime.datetime.now()
            temp = bmp280.get_temperature()
            isMrng =now.replace(hour = 10, minute = 0, second = 0, microsecond = 0)
            isDay = now.replace(hour = 11, minute = 0, second  = 0, microsecond = 0)    #Day start
            isEvng =now.replace(hour = 16, minute = 0, second = 0, microsecond = 0)
            isNight = now.replace(hour = 18, minute = 0, second  = 0, microsecond = 0)  #Night start
            mrngTemps = now > isMrng and now < isDay
            dayTemps = now > isDay and now < isEvng
            evngTemps = now > isEvng and now < isNight
            nightTemps = now > isNight or now < isMrng 
            #Morning Tempreatire Scenario
            if(mrngTemps == True):
                if temp > (Mrng_MaxTemp+0.5):
                    Cooling()                    
                elif temp < (Mrng_MaxTemp-3.0):
                    Heating()
                else:
                    In_Range()
            #Day Tempreatue scenario
            if(dayTemps == True):
                if temp > (Day_MaxTemp+0.5):
                    Cooling()
                elif temp < (Day_MaxTemp-3.0):
                    Heating()
                else:
                    In_Range() 
            #Evening Tempreature scenario  
            if(evngTemps == True):
                if temp > (Evng_Maxtemp+0.5):
                    Cooling()
                elif temp < (Evng_Maxtemp-3.0):
                    Heating()
                else:
                    In_Range()
            #Night Tempreature scenario               
            if(nightTemps == True):
                if temp > (Night_Maxtemp+0.5):
                    Cooling()
                elif temp < (Night_Maxtemp-3.0):
                    Heating()
                else:
                    In_Range()
        except RuntimeError as error:
            print("\n"+error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            bmp280.exit()
            raise error                
     
def data_log():
    while True:
        now = datetime.datetime.now()
        temp = bmp280.get_temperature()
        pressure = bmp280.get_pressure()
        degree_sign = u"\N{DEGREE SIGN}"
        format_temp = " {:.2f}".format(temp)
        format_press = " {:.2f}".format(pressure)
        fieldnames = ["Date_Time", "Temp", "Pressure"]
        with open("/home/pi/Desktop/PY_scripts/Conviron/Log.csv", "a", newline="") as log:
            writer = csv.DictWriter(log, delimiter=',',fieldnames=fieldnames)
            writer.writerow({"Date_Time" : now.strftime("%c ") , "Temp" : format_temp + degree_sign + 'C ' , "Pressure" : format_press + ' hPa'})
            time.sleep(60)

def out_put():
    clear = lambda: os.system('clear')
    while True:
        now = datetime.datetime.now()
        temp = bmp280.get_temperature()         
        pressure = bmp280.get_pressure()
        degree_sign = u"\N{DEGREE SIGN}"
        format_temp = "{:.3f}".format(temp)
        print("Building E6, room B17 EnviroPi climate data:")
        print(now.strftime("%c\n"))
        if GPIO.input(17):
            print("Cooling ON!\n")
        elif GPIO.input(26):
            print("Heating ON!\n")
        else:
            print("Cooling & Heating OFF!\n")
        print('Temperature: ' + format_temp + degree_sign + 'C')
        format_press = "{:.3f}".format(pressure)
        print('Pressure: ' + format_press + ' hPa \n') 
        time.sleep(0.1)
        clear()
        
threading.Thread(target=Lighting_Timer).start()
threading.Thread(target=Temp_Control).start()
threading.Thread(target=data_log).start()
threading.Thread(target=out_put).start() 
