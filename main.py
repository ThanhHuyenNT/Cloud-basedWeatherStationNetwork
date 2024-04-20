import time
from machine import I2C,Pin
from machine import ADC
from bmp import BMP180
import network
import urequests
import json
from machine import Pin
from machine import PWM
from uthingsboard.client import TBDeviceMqttClient

# connect ESP32 to wifi
def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        count = 0
        while (sta_if.isconnected()== False) and count <= 3:
           try:
               sta_if.connect('WIFI', 'PASSWORD')   
           except OSError:
               time.sleep(1)
           count+=1
    if sta_if.isconnected():
        print('network config:', sta_if.ifconfig())
        return True
    else:
        return False

def get_location():
    locationinfo = urequests.get('http://ipinfo.io/json').json()
    loc = locationinfo['loc'].split(",")
    return(loc)

def light():
        adc=ADC(Pin(32))
        x = adc.read()
        return((x/4095)*100)

if __name__ == "__main__":
    client = TBDeviceMqttClient('demo.thingsboard.io', access_token='')     #connect to Thingsboard
    led= Pin(23,Pin.OUT)
        
    if do_connect() == False:
        print(do_connect())
    if do_connect() == True:
        i2c = I2C(scl=Pin(22), sda=Pin(21)) #you need to change the pins according to your own wiring. 
        bmp = BMP180(i2c)
        temp = bmp.temperature
        pressure = bmp.pressure
        altitude = bmp.altitude
        
        def callback(req_id,method,params):
            print(params)
            if params == 'True':
                led.on()
                buzzer = PWM(Pin(18, Pin.OUT))
                buzzer.freq(1047)
            else:
                led.off()
                buzzer = PWM(Pin(18, Pin.OUT))
                buzzer.deinit()
                
        client.set_server_side_rpc_request_handler(callback)
        client.connect()
        x= location()
        # humidity không đo được bằng BMP180 nên dùng giá trị ảo
        telemetry = {'temperature': temp,'pressure':pressure,'light': light(),"humidity": 60 , "latitude": x[0], "longitude": x[1]}
        while True:
            client.send_telemetry(telemetry)
            temp =  bmp.temperature
            pressure = bmp.pressure
            altitude =  bmp.altitude
            telemetry = {'temperature': temp,'pressure':pressure,'light': light(),"humidity": 60 , "latitude": x[0], "longitude": x[1]}
            client.check_msg()
            client.set_server_side_rpc_request_handler(callback)
            time.sleep(3)
        
        # Disconnecting from ThingsBoard
        client.check_msg()
        client.disconnect()