Welcome to climate control with Python on Rasberri Pi 3b+
NB! This is a very custome script due its relation to a very spesific project.
What the realys are controlling via GPIO pins is set up for this spesific machinery.

Visual feedbac via a graph plotting Tempreature values in real time.
To indicate when Cooling, Heating or the main Blower is on, 
  fixed values are appended to these lists and those GPIO pins go high,
  plotting 3 straight lines for those controls with peaks indicating activity.
The main Tempreature over time plot is "dawn" over the previous plots.

5 Banks of LED Growlights are controlled on a day/night cycle and Terminal output shows what LED banks are on
Terminal output also indcated Heatin/cooling activity.

If the sensor fails or no reading is received, the script will outo-restart.

Values are logged to a .csv file called Log.csv.


