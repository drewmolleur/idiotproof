# Import libraries (board and busio are for i2c) 
import board
import busio
import os                       # To play .wav files
from digitalio import DigitalInOut
from adafruit_pn532.i2c import PN532_I2C

import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
from gpiozero import Button, Buzzer, MotionSensor
#from picamera import PiCamera

from time import sleep          # To easily use sleep function
from time import time           # To measure time in seconds
from datetime import datetime   # To get current date and time
from twilio.rest import Client

# Modify this if you have a different sized Character LCD
lcd_columns = 16
lcd_rows = 2

# Initialize I2C bus 
i2c = busio.I2C(board.SCL, board.SDA)

# With I2C, we recommend connecting RSTPD_N (reset) to a digital pin for manual
# harware reset
reset_pin = DigitalInOut(board.D6)
# On Raspberry Pi, you must also connect a pin to P32 "H_Request" for hardware
# wakeup! this means we don't need to do the I2C clock-stretch thing
req_pin = DigitalInOut(board.D12)
pn532 = PN532_I2C(i2c, debug=False, reset=reset_pin, req=req_pin)

ic, ver, rev, support = pn532.get_firmware_version()
print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))
# Configure PN532 to communicate with MiFare cards
pn532.SAM_configuration()
print('Waiting for RFID/NFC card...')

# Initialize the LCD class
lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)

#RPi pin configuration
buzzer = Buzzer(12)
pir = MotionSensor(23)
#camera = PiCamera()

# Replace button with door sensor and doorbell
magnet = Button(13)
bell = Button(26)

# Your Account Sid and Auth Token from twilio.com/console
account_sid = 'ACd818b6719b2120eeb32ac1c008188357'
auth_token = '9ecbeea82145a8b06536f9d464fd4aa4'
client = Client(account_sid, auth_token)

# Audio files
on          = "alarmOn.wav"
off         = "alarmOff.wav"
select      = "select.wav"
welcome     = "welcome.wav"
armed       = "armed.wav"
disarmed    = "disarmed.wav"
doorbell    = "doorbell.wav"
#door        = "door.wav"
Liam        = "liam.wav"
police      = "police.wav"
watching    = "watching.wav"

# Color variables
red = [100, 0, 0]
green = [0, 100, 0]
white = [100, 100, 100]
backlight_off = [0, 0, 0]

# Text variables
armedMsg = "Alarm is on"
disarmedMsg = "Alarm is off"
selectMsg = "Press select\nto turn on."
motionMsg = "Motion Detected!"
bellMsg = "Doorbell\nactivated"
doorMsg = "Door opened"

#control variables
armed = False
sensorTriggered = False
lcd.clear()
lcd.color = white
start = time()
#camera.rotation = 180
buzzer.off()
nfcId = ['0x37', '0x1f', '0xee', '0x64']

def alarm_on():
    # To change the initialized variable above, must redefine it here as 'global'
    global armed
    armed = True
    lcd.clear()
    lcd.color = green
    lcd.message = armedMsg
    os.system('aplay ' + on)
    # Give user time to leave the home
    #time.sleep(5)
    
def alarm_off():
    global armed
    global sensorTriggered
    armed = False
    sensorTriggered = False
    start = time()
    buzzer.off()
    lcd.clear()
    lcd.color = white
    lcd.message = disarmedMsg
    os.system('aplay ' + off)
    lcd.message = selectMsg
    os.system('aplay ' + select)
    
def sensors_triggered(sensor):
    global sensorTriggered
    sensorTriggered = True
    lcd.clear()
    lcd.color = red
# we need to add a photo capture before the code below to replace the recent.jpg
# we also need to let it sleep to allow time to upload to azure
# code is commented out to save funds on twilio account
    message = client.messages \
    .create(
         body='http://76.231.19.50:8081',
         from_='+14243227334',
         media_url='http://idiotproof.live/recent.jpg',
         to='+13109059209',         
    )

    print(message.sid)
    if sensor == 'motion':
        start = time()
        lcd.message = motionMsg
        os.system('aplay ' + watching)
        lcd.clear()
        lcd.color = green
        lcd.message = armedMsg
        sensorTriggered = False
    elif sensor == 'magnet':
        lcd.message = doorMsg
        buzzer.blink()  #insert audio output code
        os.system('aplay ' + police)
    elif sensor == 'bell':
        start = time()
        lcd.message = bellMsg
        os.system('aplay ' + doorbell)
        lcd.clear()
        lcd.color = green
        lcd.message = armedMsg
        sensorTriggered = False
            
os.system('aplay ' + welcome)
lcd.message = selectMsg
os.system('aplay ' + select)
nfcuid = None
while True:
    # Check if a card is available to read
    uid = pn532.read_passive_target(timeout=1)
    print('.', end="", flush=True)
    if uid is not None:
        nfcuid = [hex(i) for i in uid]
    # Wait for a button press or NFC card
    # button press has to be held for at least 1 second to work with nfcuid
    if (nfcuid == nfcId or lcd.select_button == True):
        end = time()
        elapsed = end - start
        if armed:
            alarm_off()
        else:
            alarm_on()
        nfcuid = None
    # Define actions that occur if the alarm is on
    if armed:
        end = time()
        elapsed = end - start
        # If alarm has not yet been triggered, check the sensors
        if (sensorTriggered == False):
            if (magnet.is_pressed == False):
                sensors_triggered('magnet')
            elif bell.is_pressed:
                sensors_triggered('bell')
            elif pir.motion_detected:
                sensors_triggered('motion')
                #if elapsed >= 10:
                 #   lcd.color = backlight_off
        # If door was triggered, it will continue to sound until user
        # turns it off
        else:
            if lcd.select_button:
                alarm_off()
        #if elapsed >= 10:
         #   if (camera.recording):
          #      camera.stop_recording()
           #     start = time()
            #    lcd.color = backlight_off
            
    

    
