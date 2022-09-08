#!/usr/bin/env python3
#Author Petrus Bronkhorst 2022
import threading
import time
import datetime
import RPi.GPIO as GPIO
import psutil
import csv
import os
import sys
import board
import matplotlib.pyplot as plt         
import matplotlib.animation as animation
from adafruit_bme280 import basic as adafruit_bme280
#import tkinter as tk

Mrng_MaxTemp = 20.0                        #Define Morning Tempreature
Day_MaxTemp = 28.0                          #Define Day Tempreature
Evng_MaxTemp = 20.0                         #Define Evening Tempreature
Night_MaxTemp = 15.0                        #Define Night Tempreature
Heat_Offset = 0.5                           #Heat when MaxTemp-Offset
Cool_Offset = 0.5                          #Cool when MaxTemp+Offset
CoolStop_Offset = 0.4                       #Cool from (MaxTemp+Cool_Offset) to (MaxTemp+CoolStop_Offset)
SunRse = 5                                 #LEDs start switching ON @
SunSet = 16                                 #LEDs start switching OFF @

GPIO.cleanup()
#If there ara any other processes using the GPIO pins , Kill it firs
for proc in psutil.process_iter():
    if proc.name() == 'libgpiod_pulsein' or proc.name() == 'libgpiod_pulsei':
        proc.kill()
        
# Create sensor object, using the board's default I2C bus.
i2c = board.I2C()  # uses board.SCL and board.SDA (I2c Serial Data pin3 and Serial Clock pin5)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)                    #Setup to use GPIO port naming scheme
GPIO.setup(4, GPIO.OUT)
GPIO.setup(17, GPIO.OUT)                  #GPIO17 contols compressor solenoid valve physical pin11
GPIO.setup(27, GPIO.OUT)                  #LED Bank 1
GPIO.setup(22, GPIO.OUT)                  #LED Bank 2
GPIO.setup(23, GPIO.OUT)                  #LED Bank 3
GPIO.setup(24, GPIO.OUT)                  #LED Bank 4
GPIO.setup(25, GPIO.OUT)                  #LED Bank 5
GPIO.setup(16, GPIO.OUT)                  #Blower Fans
GPIO.setup(26, GPIO.OUT)                  #Heating elemts
GPIO.output(4,True)                       #powering BME280 sensor
GPIO.output(17,False)                     #At startup first turn all outputs/relays off
GPIO.output(27,False)
GPIO.output(22,False)
GPIO.output(23,False)
GPIO.output(24,False)
GPIO.output(25,False)
GPIO.output(16,True)                       #ecept blower fan
GPIO.output(26,False)
time.sleep(3)

temp = 0.0                                 #declare global variables
pressure = 0.0
Rh = 0.0
averageTemp = 0.0
PartofDay_MaxTemp = 20.0
now = 0
onTime = 0
offTime = 0
alLedsOn = 0
isMrng = 0
isDay = 0
isEvng = 0
isNight = 0
coolOn = 0
heatOn = 0
blowOn = 0
labelString = ""
LEDsOn = False
LEDsOff = False
LEDsallOn =  False
mrngTemps = False
dayTemps = False
evngTemps = False
nightTemps = False

fig = plt.figure()                      # Create figure for plotting
ax = fig.add_subplot(1, 1, 1)
xs = []                                 
ys = []
bs = []
cs = []
hs = []

def read_sensor():                      #function for redaing BME280 sensor data every second
    while True:
        try:
            global temp, pressure, Rh, now, onTime, offTime, isMrng, alLedsOn,isDay, isEvng, isNight, LEDsOn, LEDsOff, LEDsallOn,mrngTemps, dayTemps, evngTemps, nightTemps
            temp = round(bme280.temperature,2)
            pressure = round(bme280.pressure,3)
            Rh = round(bme280.relative_humidity,2)           
            now = datetime.datetime.now()
            onTime = now.replace(hour = SunSet, minute = 0, second  = 0, microsecond = 0)    # set hours to start turning on leds
            offTime = now.replace(hour = SunRse, minute = 0, second  = 0, microsecond = 0)
            alLedsOn = now.replace(hour = SunSet+1, minute = 0, second  = 0, microsecond = 0)
            isMrng = now.replace(hour = 16, minute = 0, second = 0, microsecond = 0)
            isDay = now.replace(hour = 18, minute = 0, second  = 0, microsecond = 0)    #Day start
            isEvng =now.replace(hour = 6, minute = 0, second = 0, microsecond = 0)
            isNight = now.replace(hour = 8, minute = 0, second  = 0, microsecond = 0)  #Night start
            LEDsOn = now > onTime or now < offTime
            LEDsOff = now > offTime and now < onTime
            LEDsallOn = now > alLedsOn or now < offTime
            mrngTemps = now > isMrng and now < isDay
            dayTemps = now > isDay or now < isEvng
            evngTemps = now > isEvng and now < isNight
            nightTemps = now > isNight and now < isMrng
            time.sleep(1.0)             
        except RuntimeError as error:
            print("\n"+error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            sys.stdout.flush()                  #this will restart the sctipt automatically if sensor fails
            os.execv(sys.argv[0], sys.argv)  

def Lighting_Timer():
    while True:
        if LEDsallOn == True:           #if past sunrise cycle - turn all leds banks on
            GPIO.output(27,True)
            GPIO.output(22,True)
            GPIO.output(23,True)
            GPIO.output(24,True)
            GPIO.output(25,True)
        if LEDsOn == True:              #Start turning on lesds at Snrs time
            GPIO.output(27,True)
            time.sleep(1200)            #wait 20 minutes before turning on next LED bank(cascaded to simulate sunrise/sunset)
            GPIO.output(22,True)
            time.sleep(1200)
            GPIO.output(23,True)
            time.sleep(1200)
            GPIO.output(24,True)
            time.sleep(1200)
            GPIO.output(25,True)
        if LEDsOff == True:             #Start turning Off lesds at Snset time
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
    GPIO.output(16,True)    #Blower on!
    GPIO.output(17,False)   #Cooling OFF
    GPIO.output(26,True)    #Heating ON
    time.sleep(10.0)
    GPIO.output(26,False)    #Heating OFF
    time.sleep(10.0)     

def In_Range():
    GPIO.output(17,False)   #Cooling OFF
    GPIO.output(26,False)   #Heating OFF  

def Day_Blower_control():
    if temp > PartofDay_MaxTemp:
        while temp > PartofDay_MaxTemp and temp < PartofDay_MaxTemp+Cool_Offset:
            GPIO.output(16,False)
            time.sleep(10)           
        GPIO.output(16,True)
    elif temp < PartofDay_MaxTemp:
        while temp < PartofDay_MaxTemp and temp > PartofDay_MaxTemp-Heat_Offset:
            GPIO.output(16,False)
            time.sleep(10)
        GPIO.output(16,True)
    else:
        GPIO.output(16,True)

def Temp_Control(): #Tempreature sensing and control
    while True:
        try:
            global PartofDay_MaxTemp                    
            if mrngTemps == True:               #Morning Tempreatire Scenario
                PartofDay_MaxTemp = Mrng_MaxTemp
                Day_Blower_control()
                if temp < Mrng_MaxTemp-Heat_Offset:
                    Heating()
                elif temp > Mrng_MaxTemp+Cool_Offset:
                    while temp > Mrng_MaxTemp+CoolStop_Offset:
                        GPIO.output(26,False)   #Heating OFF
                        GPIO.output(17,True)	#Cooling ON
                    GPIO.output(17,False)		#Cooling OFF
                else:
                    In_Range()
            if dayTemps == True:                #Day Tempreatue scenario
                PartofDay_MaxTemp = Day_MaxTemp
                Day_Blower_control()
                if temp < Day_MaxTemp-Heat_Offset:
                    Heating()
                elif temp > Day_MaxTemp+Cool_Offset:
                    while temp > Day_MaxTemp+CoolStop_Offset:
                        GPIO.output(26,False)   #Heating OFF
                        GPIO.output(17,True)	#Cooling ON
                    GPIO.output(17,False)		#Cooling OFF
                else:
                    In_Range()
            if evngTemps == True:               #Evening Tempreature scenario 
                PartofDay_MaxTemp = Evng_MaxTemp
                Day_Blower_control() 
                if temp < Evng_MaxTemp-Heat_Offset:
                    Heating()
                elif temp > Evng_MaxTemp+Cool_Offset:
                    while temp > Evng_MaxTemp+CoolStop_Offset:
                        GPIO.output(26,False)   #Heating OFF 
                        GPIO.output(17,True)	#Cooling ON
                    GPIO.output(17,False)		#Cooling OFF
                else:
                    In_Range()
            if nightTemps == True:              #Night Tempreature scenario
                PartofDay_MaxTemp = Night_MaxTemp
                Day_Blower_control()     
                if temp < Night_MaxTemp-Heat_Offset:
                    Heating()
                elif temp > Night_MaxTemp+Cool_Offset:
                    while temp > Night_MaxTemp+CoolStop_Offset:
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

def temp_average():                             #Averaged over an hour
    while True:
        global averageTemp
        tempMinute = temp
        for i in range(60):
            tempMinute = tempMinute + temp
            time.sleep(60)   
        averageTemp = round(tempMinute/60,2)
        time.sleep(1.0)
     
def data_log():
    while True:
        try:
            degree_sign = u"\N{DEGREE SIGN}"
            fieldnames = ["Date_Time","Temp","TempAvr","Pressure","Rh","Cooling","Heating"]
            with open("/home/pi/Desktop/PY_scripts/Conviron/Log.csv", "a", newline="") as log:
                writer = csv.DictWriter(log, delimiter=',',fieldnames=fieldnames)
                writer.writerow({"Date_Time" : time.strftime("%Y-%m-%d %H:%M:%S ") , "Temp" : str(temp) + degree_sign + 'C ' , "TempAvr" : str(averageTemp) + degree_sign + 'C ', "Pressure" : str(pressure) + ' hPa ', "Rh" : str(Rh) + ' % ' ,"Cooling" : GPIO.input(17), "Heating" : GPIO.input(26)})
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
            global labelString, blowOn, coolOn, heatOn
            degree_sign = u"\N{DEGREE SIGN}"
            titleString = "Building E6, room B17 EnviroPi climate data:   " + time.strftime("%Y-%m-%d %H:%M:%S") + "          Tempreature: " + str(temp) + degree_sign + 'C' + "\nAtmospheric Pressure: " + str(pressure) + ' hPa' + "      Relative Humidity: " + str(Rh) + ' %' + "        Average hourly Tempreature: " + str(averageTemp) + degree_sign + 'C'
            if mrngTemps == True:
                labelString = titleString + "\n---------< Morning Tempreatures >---------" + "\nHeat when less than: " + str(Mrng_MaxTemp-Heat_Offset) + degree_sign + 'C' + "       Shoul Heat ? " + str(temp < Mrng_MaxTemp-Heat_Offset) + "\nCool when more than: " + str(Mrng_MaxTemp+Cool_Offset) + degree_sign + 'C' + "        Should cool ? " +  str(temp > Mrng_MaxTemp+Cool_Offset) + "\nStop cooling @" + str(Mrng_MaxTemp+CoolStop_Offset) + degree_sign + 'C'
            if dayTemps == True:
                labelString = titleString + "\n---------<_Day Tempreatures:_>---------" + "\nHeat when less than: " + str(Day_MaxTemp-Heat_Offset) + degree_sign + 'C' + "       Shoul Heat ? " + str(temp < Day_MaxTemp-Heat_Offset) + "\nCool when more than: " + str(Day_MaxTemp+Cool_Offset) + degree_sign + 'C' + "        Should cool ? " + str(temp > Day_MaxTemp+Cool_Offset) + "\nStop cooling @" + str(Day_MaxTemp+CoolStop_Offset) + degree_sign + 'C'
            if evngTemps == True:
                labelString = titleString + "\n---------<_Evening Tempreatures:_>---------" + "\nHeat when less than: " + str(Evng_MaxTemp-Heat_Offset) + degree_sign + 'C' + "       Shoul Heat ? " + str(temp < Evng_MaxTemp-Heat_Offset) + "\nCool when more than: " + str(Evng_MaxTemp+Cool_Offset) + degree_sign + 'C' + "        Should cool ? " + str(temp > Evng_MaxTemp+Cool_Offset) + "\nStop cooling @"  + str(Evng_MaxTemp+CoolStop_Offset) + degree_sign + 'C'
            if nightTemps == True:
                labelString = titleString + "\n---------< Night Tempreatures >---------" + "\nHeat when less than: " + str(Night_MaxTemp-Heat_Offset) + degree_sign + 'C' + "        Shoul Heat ? " + str(temp < Night_MaxTemp-Heat_Offset) + "\nCool when more than: " + str(Night_MaxTemp+Cool_Offset) + degree_sign + 'C' + "        Should cool ? " + str(temp > Night_MaxTemp+Cool_Offset) + "\nStop cooling @" + str(Night_MaxTemp+CoolStop_Offset) + degree_sign + 'C'
            if GPIO.input(16):
                blowOn = PartofDay_MaxTemp+0.55
                print("Blower on!")
            else:
                blowOn = PartofDay_MaxTemp      
            if GPIO.input(17):
                coolOn = PartofDay_MaxTemp+0.54
                print("\nCooling ON!")
            else:
                coolOn = PartofDay_MaxTemp
            if GPIO.input(26):
                heatOn = PartofDay_MaxTemp+0.53
                print("\nHeating ON!")
            else:
                heatOn = PartofDay_MaxTemp
                print("\nCooling & Heating OFF!\n")
            if GPIO.input(27):
                print(" LED bank 1 ON")
            if GPIO.input(22):
                print("  LED bank 2 ON")
            if GPIO.input(23):
                print("   LED bank 3 ON")
            if GPIO.input(24):
                print("    LED bank 4 ON")
            if GPIO.input(25):
                print("     LED bank 5 ON") 
            time.sleep(1.1)
            os.system('clear')
        except RuntimeError as error:
            print("\n"+error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            raise error

# This function is called periodically from FuncAnimation
def animate(i, xs, ys, bs, cs, hs):
    degree_sign = u"\N{DEGREE SIGN}"
    # Add x and y to lists
    xs.append(now)
    ys.append(temp)
    bs.append(blowOn)
    cs.append(coolOn)
    hs.append(heatOn)

    # Limit x and y lists to 20 items
    #xs = xs[-20:]
    #ys = ys[-20:]
    # Draw x and y lists
    ax.clear()
    ax.plot(xs, cs)
    ax.plot(xs, hs)
    ax.plot(xs, bs)
    ax.plot(xs, ys)
    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(top=0.82)
    plt.subplots_adjust(bottom=0.12)
    plt.title(labelString) 
    plt.ylabel('Temperature in ' + degree_sign + 'C')

threading.Thread(target=Lighting_Timer).start()
threading.Thread(target=read_sensor).start()
threading.Thread(target=Temp_Control).start()
threading.Thread(target=data_log).start()
threading.Thread(target=temp_average).start()
threading.Thread(target=out_put).start()

# Set up plot to call animate() function - set resolution via interval
ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys, bs, cs, hs), interval=1000)
plt.show()
