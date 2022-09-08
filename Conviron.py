#!/usr/bin/env python3
import threading
import time
import datetime
import RPi.GPIO as GPIO
import adafruit_dht
import psutil
import csv

GPIO.cleanup()
#If there ara any other processes using the GPIO pins , Kill it firs
for proc in psutil.process_iter():
    if proc.name() == 'libgpiod_pulsein' or proc.name() == 'libgpiod_pulsei':
        proc.kill()

GPIO.setmode(GPIO.BCM)                    #Setup use to use GPIO port numbers
sensor = adafruit_dht.DHT22(4, GPIO.IN)   #GPIO4 inpuit from DHT22 sensor physical pin7
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

time.sleep(10)

def Lighting_Timer():
    while True:
        try:      
            now = datetime.datetime.now()
            onTime = now.replace(hour = 6, minute = 0, second  = 0, microsecond = 0)    # set hours to start turning on leds
            offTime = now.replace(hour = 18, minute = 0, second  = 0, microsecond = 0)  # set time to start turnomg leds off
            LEDsOn = now > onTime and now < offTime
            LEDsOff = now > offTime or now < onTime
            if(LEDsOn == True):
                GPIO.output(27,True)
                time.sleep(1200)          #wait 5 minutes before turning on next LED bank(cascaded to simulate sunrise/sunset)
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
        except RuntimeError as error:
            print("\n"+error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            sensor.exit()
            raise error
        
def out_put():
    while True:
        try:
            now = datetime.datetime.now()
            temp = sensor.temperature         
            humidity = sensor.humidity
            print("\nE6, B17 EnviroPi climate data:", now.strftime("%c"))
            print("\nTemp: {}*C \nRH: {}% ".format(temp, (humidity)))
            time.sleep(10.0)
        except RuntimeError as error:
            print("\n"+error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            sensor.exit()
            raise error
        
def Temp_Control(): #Tempreature sensing and control
    while True:
        try:
            now = datetime.datetime.now()
            isDay = now.replace(hour = 6, minute = 0, second  = 0, microsecond = 0)    #Day start
            isNight = now.replace(hour = 18, minute = 0, second  = 0, microsecond = 0)  #Night starts
            dayTemps = now > isDay and now < isNight
            nighTemps = now > isNight or now < isDay        
            temp = sensor.temperature         
            humidity = sensor.humidity                     
            #Day Tempreatue scenario
            if(dayTemps == True):
                print('Day Tempreatures scenario')
                if temp > 25.0:
                    GPIO.output(26,False)   #Heating OFF
                    GPIO.output(17,True)    #cooling ON
                    print("Cooling ON")
                    time.sleep(8.0)
                    GPIO.output(17,False)
                    time.sleep(30.0)
                elif temp < 23.0:
                    GPIO.output(17,False)   #Cooling OFF
                    GPIO.output(26,True)    #Heating ON
                    print("Heating ON")
                    time.sleep(12.0)
                    GPIO.output(26,False)
                    time.sleep(25.0)
                else:
                    GPIO.output(17,False)   #Cooling OFF
                    GPIO.output(26,False)   #Heating OFF
                    print("Cooling & Heating OFF")
                    time.sleep(5.0)                    
            #Night Tempreature scenario
            if(nighTemps == True):
                print("\nBuilding E6, room B17 EnviroPi climate data:",now.strftime("%c") )
                print('Night Tempreatures scenaio')
                if temp > 8.0:
                    GPIO.output(26,False)   #Heating OFF
                    GPIO.output(17,True)    #cooling ON
                    print("\nCooling ON")
                    time.sleep(8.0)
                    GPIO.output(17,False)
                    time.sleep(25.0)
                elif temp < 6.0:
                    GPIO.output(17,False)   #cooling OFF
                    GPIO.output(26,True)    #Heating ON
                    print("\nHeating ON") 
                    time.sleep(10.0)
                    GPIO.output(26,False)
                    time.sleep(30.0)
                else:
                    GPIO.output(26,False)   #Heating OFF
                    GPIO.output(17,False)   #Cooling OFF
                    print("Cooling & Heating OFF")
                    time.sleep(5.0)                                              
        except RuntimeError as error:
            print("\n"+error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            sensor.exit()
            raise error
        
def data_log():
    while True:
        try:
            now = datetime.datetime.now()
            temp = sensor.temperature       
            humidity = sensor.humidity
            fieldnames = ["Date_Time", "Temp", "RH"]
            with open("/home/pi/Desktop/PY_scripts/Conviron/Log.csv", "a", newline="") as log:
                writer = csv.DictWriter(log, delimiter='-',fieldnames=fieldnames)
                writer.writerow({"Date_Time" : now.strftime("%c ") , "Temp" : " {} *C ".format(temp) , "RH" : " {} % ".format(humidity)})    
                time.sleep(60)
        except RuntimeError as error:
            print("\n"+error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            sensor.exit()
            raise error
     
threading.Thread(target=Lighting_Timer).start()
threading.Thread(target=Temp_Control).start()
threading.Thread(target=data_log).start()
threading.Thread(target=out_put).start()