import RPi.GPIO as GPIO
import os
import time
from datetime import datetime
from datetime import timedelta
import paho.mqtt.client as mqtt
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

host_name = '192.168.0.16' #replace with raspberry pi webserver IP as required
host_port = 8000

# set up the to use the board numbers
GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)

# allocate the pins
# define the colours/labels and their pins
pins = {'red':14,'orange':15,'yellow':18,'buzzer':23,
        'indigo':16,'blue':20,'green':21}

# set up the GPIO pins
for pin in pins.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# set up the pwm object
pwm = GPIO.PWM(pins['buzzer'], 100)
pwm.start(0)
GPIO.output(pins['indigo'], GPIO.HIGH) # buzzer/audible alarm is enabled by default

topics = {'Motion':'','Proximity':'','Light':'','Temperature':'','Humidity':'','msgReceived':datetime.now()}

clients = [
{'broker':'test.mosquitto.org','port':1883,'name':'Motion','Topic':'Motion'},
{'broker':'test.mosquitto.org','port':1883,'name':'Proximity','Topic':'Proximity'},
{'broker':'test.mosquitto.org','port':1883,'name':'Light','Topic':'Light'},
{'broker':'test.mosquitto.org','port':1883,'name':'Temperature','Topic':'Temperature'},
{'broker':'test.mosquitto.org','port':1883,'name':'Humidity','Topic':'Humidity'}
]

nclients = len(clients)

def msg_handle():
    # Red Led
    if (topics['Motion'] == 'Active'):
        GPIO.output(pins['red'], GPIO.HIGH)
    else:
        GPIO.output(pins['red'], GPIO.LOW)
    # Orange Led
    if (float(topics['Proximity']) < 50):
        GPIO.output(pins['orange'], GPIO.HIGH)
    else:
        GPIO.output(pins['orange'], GPIO.LOW)
    # Yellow Led
    if (float(topics['Light']) > 5):
        GPIO.output(pins['yellow'], GPIO.HIGH)
    else:
        GPIO.output(pins['yellow'], GPIO.LOW)
    # Indigo Led
        #is used for Enabling and/or Disabling the buzzer
    # Blue Led
        #is used for showing whether a resident is home, on means someone is home
    # Green Led
    if (GPIO.input(pins['red']) == 0 and GPIO.input(pins['orange']) == 0):
        GPIO.output(pins['green'], GPIO.HIGH)
    else:
        GPIO.output(pins['green'], GPIO.LOW)
    # Buzzer - pwm load
    if (GPIO.input(pins['indigo']) == 0):
        x = 0
        pwm.ChangeDutyCycle(x)
    elif (GPIO.input(pins['indigo']) == 1):
        if (float(topics['Proximity']) > 100):
            x = 0
            pwm.ChangeDutyCycle(x)
        else:
            x = 100 - float(topics['Proximity']) / 1.0
            pwm.ChangeDutyCycle(x)
        
def pins_low():
    for pin in pins.values():
        GPIO.output(pin, GPIO.LOW)

def messageFunction (client, userdata, message):
    topic = str(message.topic)
    message = str(message.payload.decode("utf-8"))
    if ( message != 'nan' and message != '-1'):
        topics[topic] = message
        topics[msgReceived] = datetime.now()
    msg_handle()

def clientSubscribe(client, clientName):
    clientName = mqtt.Client(client['name'])                # Create a MQTT client object
    clientName.connect(client['broker'], client['port'])    # Connect to the test MQTT broker
    clientName.subscribe(client['Topic'])                   # Subscribe to the topic
    clientName.on_message = messageFunction                 # Attach the messageFunction to subscription
    clientName.loop_start()                                 # Start the MQTT client

threads = []
for i in range(nclients):
    t = threading.Thread(target=clientSubscribe, args = (clients[i],clients[i]['name'],))
    threads.append(t)
    t.start()

class MyServer(BaseHTTPRequestHandler):
    """ A special implementation of BaseHTTPRequestHander for reading data from
        and control GPIO of a Raspberry Pi
    """
    def do_HEAD(self):
        """ do_HEAD() can be tested use curl command
            'curl -I http://server-ip-address:port'
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _redirect(self, path):
        self.send_response(303)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()

    def do_GET(self):
        """ do_GET() can be tested using curl command
            'curl http://server-ip-address:port'
        """
        html = '''
            <html>
            <head>
            <meta http-equiv="refresh" content="10" />
            </head>
            <body style="width:960px; margin: 20px auto;">
            <title>SIT210 Task 11.2P</title>
            <h1>SIT210 Task 11.2P</h1>
            <h2>Project Artefact - Small Footprint Home Security and Alert System</h2>
            <hr />
            <p>Temperature (oC) : {}<br>
               Humidity (%) &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp: {}<br>
               Light (lx) &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp: {}<br>
               Proximity (cm) &nbsp&nbsp&nbsp: {}<br>
               Motion &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp: {}</p>
            <form action="/" method="POST">
                Audible Alarm :<br>
                <input type="radio" name="alarm" value="On" onclick="this.form.submit();" > Enable
                <br>
                <input type="radio" name="alarm" value="Off" onclick="this.form.submit();"> Disable
                <br>
            </form>
               <form action="/" method="POST">
                Someone Home? :<br>
                <input type="radio" name="home" value="Yes" onclick="this.form.submit();" > Yes
                <br>
                <input type="radio" name="home" value="No" onclick="this.form.submit();"> No
            </form>
            <hr />
            </body>
            </html>
        '''
        temp = str(topics['Temperature'])
        hum = str(topics['Humidity'])
        lux = str(topics['Light'])
        prox = str(topics['Proximity'])
        motn = str(topics['Motion'])
        self.do_HEAD()
        self.wfile.write(html.format(temp, hum, lux, prox, motn).encode("utf-8"))

    def do_POST(self):
        """ do_POST() can be tested using curl command
            'curl -d "submit=On" http://server-ip-address:port'
        """
        content_length = int(self.headers['Content-Length'])    # Get the size of data
        post_data = self.rfile.read(content_length).decode("utf-8")   # Get the data
        post_data = post_data.split("=")[1]    # Only keep the value

        if post_data == 'On':
            GPIO.output(pins['indigo'], GPIO.HIGH)
        elif post_data == 'Off':
            GPIO.output(pins['indigo'], GPIO.LOW)
        elif post_data == 'Yes':
            GPIO.output(pins['blue'], GPIO.HIGH)
        elif post_data == 'No':
            GPIO.output(pins['blue'], GPIO.LOW)
        print("Led is {}".format(post_data))
        self._redirect('/')    # Redirect back to the root url
       
if __name__ == '__main__':
    http_server = HTTPServer((host_name, host_port), MyServer)
    print("Server Starts - %s:%s" % (host_name, host_port))

    # If no messages have been received for 5 minutes blink the green led (need to move this section to a thread)
    #while true:
    #    t = datetime.now() - topics['msgReceived']
    #    if (t.total_seconds() > 300):
    #        GPIO.output(pins['green'], GPIO.HIGH)
    #        time.sleep(1)
    #        GPIO.output(pins['green'], GPIO.LOW)
    #        time.sleep(1)
                
    try:
        http_server.serve_forever()
                
    except KeyboardInterrupt:
        http_server.server_close()
        pwm.stop()
        pins_low()
        GPIO.cleanup()
