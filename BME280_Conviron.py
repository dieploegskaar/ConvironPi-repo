#!/usr/bin/env python3
#Author Petrus Bronkhorst 2022
import threading
import time
from datetime import datetime
import RPi.GPIO as GPIO
import psutil
import csv
import os
import board
from adafruit_bme280 import basic as adafruit_bme280
#import tkinter as tk

Mrng_MaxTemp = 8.0                      #Define Morning Tempreature
Day_MaxTemp = 15.0                      #Define Day Tempreature
Evng_MaxTemp = 8.0                      #Define Evening Tempreature
Night_MaxTemp = 5.0                     #Define Night Tempreature
SunRse = 8                              #LEDs start switching ON @
SunSet = 16                             #LEDs start switching OFF @

GPIO.cleanup()
#If there ara any other processes using the GPIO pins , Kill it firs
for proc in psutil.process_iter():
    if proc.name() == 'libgpiod_pulsein' or proc.name() == 'libgpiod_pulsei':
        proc.kill()
        
# Create sensor object, using the board's default I2C bus.
i2c = board.I2C()  # uses board.SCL and board.SDA
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

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

temp = 0.0
pressure = 0.0
Rh = 0.0
now = 0
onTime = 0
offTime = 0
isMrng = 0
isDay = 0
isEvng = 0
isNight = 0
LEDsOn = False
LEDsOff = False
mrngTemps = False
dayTemps = False
evngTemps = False
nightTemps = False

def read_sensor():
    while True:
        try:
            global temp, pressure, Rh, now, onTime, offTime, isMrng, isDay, isEvng, isNight, LEDsOn, LEDsOff, mrngTemps, dayTemps, evngTemps, nightTemps
            temp = round(bme280.temperature,2)
            pressure = round(bme280.pressure,3)
            Rh = round(bme280.relative_humidity,2)
            now = datetime.now()
            onTime = now.replace(hour = SunRse, minute = 0, second  = 0, microsecond = 0)    # set hours to start turning on leds
            offTime = now.replace(hour = SunSet, minute = 0, second  = 0, microsecond = 0)
            isMrng = now.replace(hour = 10, minute = 0, second = 0, microsecond = 0)
            isDay = now.replace(hour = 11, minute = 0, second  = 0, microsecond = 0)    #Day start
            isEvng =now.replace(hour = 16, minute = 0, second = 0, microsecond = 0)
            isNight = now.replace(hour = 18, minute = 0, second  = 0, microsecond = 0)  #Night start
            LEDsOn = now > onTime and now < offTime
            LEDsOff = now > offTime or now < onTime
            mrngTemps = now > isMrng and now < isDay
            dayTemps = now > isDay and now < isEvng
            evngTemps = now > isEvng and now < isNight
            nightTemps = now > isNight or now < isMrng
            time.sleep(0.1)             
        except RuntimeError as error:
            print("\n"+error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            raise error

def Lighting_Timer():
    while True:
        if LEDsOn == True:
            GPIO.output(27,True)
            time.sleep(1200)          #wait 20 minutes before turning on next LED bank(cascaded to simulate sunrise/sunset)
            GPIO.output(22,True)
            time.sleep(1200)
            GPIO.output(23,True)
            time.sleep(1200)
            GPIO.output(24,True)
            time.sleep(1200)
            GPIO.output(25,True)
        if LEDsOff == True:
            GPIO.output(25,False)
            time.sleep(1200)
            GPIO.output(24,False)
            time.sleep(1200)
            GPIO.output(23,False)
            time.sleep(1200)
            GPIO.output(22,False)
            time.sleep(1200)
            GPIO.output(27,False)

def Heating():
    GPIO.output(17,False)   #Cooling OFF
    GPIO.output(26,True)    #Heating ON
    time.sleep(20.0)
    GPIO.output(26,False)
    time.sleep(10.0)

def HeatingRescue():
    GPIO.output(17,False)   #Cooling OFF
    GPIO.output(26,True)    #Heating ON
    time.sleep(60.0)
    GPIO.output(26,False)

def In_Range():
    time.sleep(10.0)
    GPIO.output(17,False)   #Cooling OFF
    GPIO.output(26,False)   #Heating OFF
    time.sleep(10.0)     
     
def Temp_Control(): #Tempreature sensing and control
    while True:
        try:
            if mrngTemps == True:               #Morning Tempreatire Scenario
                if temp < Mrng_MaxTemp-2.0:
                    Heating()
                elif temp > Mrng_MaxTemp+0.5:
                    while temp > Mrng_MaxTemp:
                        GPIO.output(26,False)   #Heating OFF
                        GPIO.output(17,True)	#Cooling ON
                    GPIO.output(17,False)		#Cooling OFF
                else:
                    In_Range()
            if dayTemps == True:                #Day Tempreatue scenario
                if temp < Day_MaxTemp-2.0:
                    Heating()	
                elif temp > Day_MaxTemp+0.5:
                    while temp > Day_MaxTemp:
                        GPIO.output(26,False)   #Heating OFF
                        GPIO.output(17,True)	#Cooling ON
                    GPIO.output(17,False)		#Cooling OFF
                else:
                    In_Range()
            if evngTemps == True:               #Evening Tempreature scenario  
                if temp < Evng_MaxTemp-2.0:
                    Heating()
                elif temp > Evng_MaxTemp+0.5:
                    while temp > Evng_MaxTemp:
                        GPIO.output(26,False)   #Heating OFF
                        GPIO.output(17,True)	#Cooling ON
                    GPIO.output(17,False)		#Cooling OFF
                else:
                    In_Range()
            if nightTemps == True:              #Night Tempreature scenario     
                if temp <= Night_MaxTemp-2.0:
                    Heating()
                elif temp > Night_MaxTemp+0.5:
                    while temp > Night_MaxTemp:
                        GPIO.output(26,False)   #Heating OFF
                        GPIO.output(17,True)	#Cooling ON
                    GPIO.output(17,False)		#Cooling OFF
                else:
                    In_Range()               
        except RuntimeError as error:
            print("\n"+error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            raise error                
     
def data_log():
    while True:
        try:
            degree_sign = u"\N{DEGREE SIGN}"
            fieldnames = ["Date_Time", "Temp", "Pressure","Rh","Cooling","Heating"]
            with open("/home/pi/Desktop/PY_scripts/Conviron/Log.csv", "a", newline="") as log:
                writer = csv.DictWriter(log, delimiter=',',fieldnames=fieldnames)
                writer.writerow({"Date_Time" : now , "Temp" : str(temp) + degree_sign + 'C ' , "Pressure" : str(pressure) + 'hPa ', "Rh" : str(Rh) + '% ' ,"Cooling" : GPIO.input(17), "Heating" : GPIO.input(26)})
                time.sleep(60)
        except RuntimeError as error:
            print("\n"+error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            raise error
                
def out_put():
    while True:
        try:
            degree_sign = u"\N{DEGREE SIGN}"
            print("Building E6, room B17 EnviroPi climate data:")
            print(now)
            print('\nTemperature:		' + str(temp) + degree_sign + 'C\n')
            print('Atmospheric Pressure:	' + str(pressure) + ' hPa')
            print('Relative Humidity:	' + str(Rh) + ' % \n')  
            print("Is temp less than 0 ? ")
            print(temp < 0)
            if mrngTemps == True:
                print("\n-<_Morning Tempreatures:_>-\n")
                print("Heat when less than :")
                print(Mrng_MaxTemp-2.0)
                print("Shoul Heat ?")
                print(temp < Mrng_MaxTemp-2.0)
                print("Cool when more than :")
                print(Mrng_MaxTemp+0.5)
                print("Should cool ?")
                print(temp > Mrng_MaxTemp+0.5)
            if dayTemps == True:
                print("\n-<_Day Tempreatures:_>-\n")
                print("Heat when less than :")
                print(Day_MaxTemp-2.0)
                print("Shoul Heat ? ")
                print(temp < Day_MaxTemp-2.0)
                print("Cool when more than :")
                print(Day_MaxTemp+0.5)
                print("Should cool ?")
                print(temp > Day_MaxTemp+0.5)
            if evngTemps == True:
                print("\n-<_Evening Tempreatures:_>-\n")
                print("Heat when less than ")
                print(Evng_MaxTemp-2.0)
                print("Shoul Heat ? ")
                print(temp < Evng_MaxTemp-2.0)
                print("Cool when more than")
                print(Evng_MaxTemp+0.5)
                print("Should cool")
                print(temp > Evng_MaxTemp+0.5)
            if nightTemps == True:
                print("\n<_Night Tempreatures:_>-\n")
                print("Heat when less than :")
                print(Night_MaxTemp-2.0)  
                print("Shoul Heat ?")
                print(temp < Night_MaxTemp-2.0)
                print("Cool when more than :")
                print(Night_MaxTemp+0.5)
                print("Should cool ?")
                print(temp > Night_MaxTemp+0.5)      
            if GPIO.input(17):
                print("\nCooling ON!")
            elif GPIO.input(26):
                print("\nHeating ON!")
            else:
                print("\nCooling & Heating OFF!")
            if GPIO.input(27):
                print("LED bank 1 ON")
            if GPIO.input(22):
                print("LED bank 2 ON")
            if GPIO.input(23):
                print("LED bank 3 ON")
            if GPIO.input(24):
                print("LED bank 4 ON")
            if GPIO.input(25):
                print("LED bank 5 ON")    
            time.sleep(1.0)
            os.system('clear')
        except RuntimeError as error:
            print("\n"+error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            raise error

threading.Thread(target=Lighting_Timer).start()
threading.Thread(target=read_sensor).start()
threading.Thread(target=Temp_Control).start()
threading.Thread(target=data_log).start()
threading.Thread(target=out_put).start()