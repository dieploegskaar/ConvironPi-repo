#!/usr/bin/env python3
#Author Petrus Bronkhorst 2022
import threading
import time
from datetime import datetime
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

Mrng_MaxTemp = 8.0                      #Define Morning Tempreature
Day_MaxTemp = 15.0                      #Define Day Tempreature
Evng_MaxTemp = 8.0                      #Define Evening Tempreature
Night_MaxTemp = 5.0                     #Define Night Tempreature
Heat_Offset = 2.0                       #Heat when MaxTemp-Offset
Cool_Offset = 0.5                       #Cool when MaxTemp+Offset
CoolStop_Offset = 0.4                   #Cool from (MaxTemp+Cool_Offset) to (MaxTemp+CoolStop_Offset)
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
GPIO.output(16,True)                       #blower fan
GPIO.output(26,False)
time.sleep(3)

temp = 0.0                                 #declare global variables
pressure = 0.0
Rh = 0.0
averageTemp = 0.0
now = 0
onTime = 0
offTime = 0
alLedsOn = 0
isMrng = 0
isDay = 0
isEvng = 0
isNight = 0
LEDsOn = False
LEDsOff = False
LEDsallOn =  False
mrngTemps = False
dayTemps = False
evngTemps = False
nightTemps = False

# Create figure for plotting
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
xs = []
ys = []

def read_sensor():
    while True:
        try:
            global temp, ambient_temp, pressure, Rh, now, onTime, offTime, isMrng, alLedsOn,isDay, isEvng, isNight, LEDsOn, LEDsOff, LEDsallOn,mrngTemps, dayTemps, evngTemps, nightTemps
            temp = round(bme280.temperature,2)
            pressure = round(bme280.pressure,3)
            Rh = round(bme280.relative_humidity,2)
            now = datetime.now()
            onTime = now.replace(hour = SunRse, minute = 0, second  = 0, microsecond = 0)    # set hours to start turning on leds
            offTime = now.replace(hour = SunSet, minute = 0, second  = 0, microsecond = 0)
            alLedsOn = now.replace(hour = SunRse+1, minute = 0, second  = 0, microsecond = 0)
            isMrng = now.replace(hour = 10, minute = 0, second = 0, microsecond = 0)
            isDay = now.replace(hour = 11, minute = 0, second  = 0, microsecond = 0)    #Day start
            isEvng =now.replace(hour = 16, minute = 0, second = 0, microsecond = 0)
            isNight = now.replace(hour = 18, minute = 0, second  = 0, microsecond = 0)  #Night start
            LEDsOn = now > onTime and now < alLedsOn
            LEDsOff = now > offTime or now < onTime
            LEDsallOn = now > alLedsOn and now < offTime
            mrngTemps = now > isMrng and now < isDay
            dayTemps = now > isDay and now < isEvng
            evngTemps = now > isEvng and now < isNight
            nightTemps = now > isNight or now < isMrng
            time.sleep(1.0)             
        except RuntimeError as error:
            print("\n"+error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            sys.stdout.flush()                  #this will restart the sctipt automaticalle 
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
    GPIO.output(17,False)   #Cooling OFF
    GPIO.output(26,True)    #Heating ON
    time.sleep(30.0)
    GPIO.output(26,False)    #Heating OFF
    time.sleep(10.0)     

def In_Range():
    GPIO.output(17,False)   #Cooling OFF
    GPIO.output(26,False)   #Heating OFF   
     
def Temp_Control(): #Tempreature sensing and control
    while True:
        try:           
            if mrngTemps == True:               #Morning Tempreatire Scenario
                if temp < Mrng_MaxTemp-Heat_Offset:
                    Heating()
                elif temp > Mrng_MaxTemp+Cool_Offset:
                    while temp > Mrng_MaxTemp+CoolStop_Offset:
                        GPIO.output(26,False)   #Heating OFF
                        GPIO.output(17,True)	#Cooling ON
                    GPIO.output(17,False)		#Cooling OFF
                elif temp < Mrng_MaxTemp:
                    while temp < Mrng_MaxTemp:
                        GPIO.output(16,False)
                        time.sleep(2)
                    GPIO.output(16,True)
                    time.sleep(5)
                else:
                    In_Range()
            if dayTemps == True:                #Day Tempreatue scenario
                if temp < Day_MaxTemp-Heat_Offset:
                    Heating()
                elif temp > Day_MaxTemp+Cool_Offset:
                    while temp > Day_MaxTemp+CoolStop_Offset:
                        GPIO.output(26,False)   #Heating OFF
                        GPIO.output(17,True)	#Cooling ON
                    GPIO.output(17,False)		#Cooling OFF
                elif temp < Day_MaxTemp:
                    while temp < Day_MaxTemp:
                        GPIO.output(16,False)
                        time.sleep(2)
                    GPIO.output(16,True)
                    time.sleep(5)
                else:
                    In_Range()
            if evngTemps == True:               #Evening Tempreature scenario  
                if temp < Evng_MaxTemp-Heat_Offset:
                    Heating()
                elif temp > Evng_MaxTemp+Cool_Offset:
                    while temp > Evng_MaxTemp+CoolStop_Offset:
                        GPIO.output(26,False)   #Heating OFF 
                        GPIO.output(17,True)	#Cooling ON
                    GPIO.output(17,False)		#Cooling OFF
                elif temp < Evng_MaxTemp:
                    while temp < Evng_MaxTemp:
                        GPIO.output(16,False)
                        time.sleep(2)
                    GPIO.output(16,True)
                    time.sleep(5)
                else:
                    In_Range()
            if nightTemps == True:              #Night Tempreature scenario     
                if temp < Night_MaxTemp-Heat_Offset:
                    Heating()
                elif temp > Night_MaxTemp+Cool_Offset:
                    while temp > Night_MaxTemp+CoolStop_Offset:
                        GPIO.output(26,False)   #Heating OFF
                        GPIO.output(17,True)	#Cooling ON
                    GPIO.output(17,False)		#Cooling OFF
                elif temp < Night_MaxTemp:
                    while temp < Night_MaxTemp:
                        GPIO.output(16,False)
                        time.sleep(2)
                    GPIO.output(16,True)
                    time.sleep(5)
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
                writer.writerow({"Date_Time" : now , "Temp" : str(temp) + degree_sign + 'C ' , "TempAvr" : str(averageTemp) + degree_sign + 'C ', "Pressure" : str(pressure) + ' hPa ', "Rh" : str(Rh) + ' % ' ,"Cooling" : GPIO.input(17), "Heating" : GPIO.input(26)})
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
            print("\nTempreature:			" + str(temp) + degree_sign + 'C')
            print("\nAverage hourly Tempreature:	" + str(averageTemp) + degree_sign + 'C\n')
            print("Atmospheric Pressure:		" + str(pressure) + ' hPa')
            print("Relative Humidity:		" + str(Rh) + ' % \n')  
            print("Is temp less than 0 ? ")
            print(temp < 0)
            if mrngTemps == True:
                print("\n-----------<_Morning Tempreatures:_>-----------\n")
                print("Heat when less than:		" + str(Mrng_MaxTemp-Heat_Offset))
                print("Shoul Heat ?     " + str(temp < Mrng_MaxTemp-Heat_Offset))
                print("Cool when more than:		" + str(Mrng_MaxTemp+Cool_Offset))
                print("Stop cooling @			" + str(Mrng_MaxTemp+CoolStop_Offset))
                print("Should cool ?    "+  str(temp > Mrng_MaxTemp+Cool_Offset))
            if dayTemps == True:
                print("\n-----------<_Day Tempreatures:_>---------------\n")
                print("Heat when less than:     " + str(Day_MaxTemp-Heat_Offset))
                print("Shoul Heat ?         " + str(temp < Day_MaxTemp-Heat_Offset) + "\n")
                print("Cool when more than:     " + str(round(Day_MaxTemp+Cool_Offset,2)))
                print("Stop cooling @           " + str(round(Day_MaxTemp+CoolStop_Offset,2)))
                print("\nShould cool ?      " + str(temp > Day_MaxTemp+Cool_Offset))
            if evngTemps == True:
                print("\n-<_Evening Tempreatures:_>-\n")
                print("Heat when less than:		" + str(Evng_MaxTemp-Heat_Offset))
                print("Shoul Heat ?				" + str(temp < Evng_MaxTemp-Heat_Offset))
                print("Cool when more than:		" + str(Evng_MaxTemp+Cool_Offset))
                print("Stop cooling @			" + str(Evng_MaxTemp+CoolStop_Offset))
                print("Should cool ?			" + str(temp > Evng_MaxTemp+Cool_Offset))
            if nightTemps == True:
                print("\n<_Night Tempreatures:_>-\n")
                print("Heat when less than:		" + str(Night_MaxTemp-Heat_Offset))
                print("Shoul Heat ?         " + str(temp < Night_MaxTemp-Heat_Offset) + "\n")
                print("Cool when more than:		" + str(Night_MaxTemp+Cool_Offset))
                print("Stop cooling @			" + str(Night_MaxTemp+CoolStop_Offset))
                print("Should cool ?        " + str(temp > Night_MaxTemp+Cool_Offset))
            if GPIO.input(4):
                print("\n Sensor on")
            if GPIO.input(16):
                print("\nBlower ON")
            else:
                print("\nBlower OFF")         
            if GPIO.input(17):
                print("\nCooling ON!")
            elif GPIO.input(26):
                print("\nHeating ON!")
            else:
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
def animate(i, xs, ys):
    # Add x and y to lists
    xs.append(now)
    ys.append(temp)
    # Limit x and y lists to 20 items
    #xs = xs[-20:]
    #ys = ys[-20:]
    # Draw x and y lists
    ax.clear()
    ax.plot(xs, ys)
    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('BME280 Temperature over Time')
    plt.ylabel('Temperature (deg C)')

threading.Thread(target=Lighting_Timer).start()
threading.Thread(target=read_sensor).start()
threading.Thread(target=Temp_Control).start()
threading.Thread(target=data_log).start()
threading.Thread(target=temp_average).start()
threading.Thread(target=out_put).start()

# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=1000)
plt.show()
