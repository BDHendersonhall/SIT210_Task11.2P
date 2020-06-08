// This #include statement was automatically added by the Particle IDE.
#include <MQTT.h>
#include "Particle.h"
#include <BH1750Lib.h>
#include <Adafruit_DHT.h>
#include <HC_SR04.h>

#define DHTPIN D5
#define DHTTYPE DHT22       // note sensing period is ~2s

#define TRIGGER A5
#define ECHO D13
#define MOTIONPIN D8

SYSTEM_MODE(AUTOMATIC);

// Create an MQTT client
MQTT client("test.mosquitto.org", 1883, callback);

double temperature = 0;     // temperature measurement
double humidity = 0;        // humidity measurement
double light = 0;           // light measurement
double proximity = 0;       // proximity measurement

char activeMotion [] = "Active";
char inactiveMotion [] = "Inactive";
char* motion;               //Stores the motion as Active or Inactive

// .publish() requires a char and not an int we make a char variable to put the measurement in
char temperatureStr[15];     
char humidityStr[15];
char lightStr[15];
char proximityStr[15];

DHT dht(DHTPIN, DHTTYPE);
BH1750Lib lightMeter;
HC_SR04 proximityMeter = HC_SR04(TRIGGER, ECHO);

// This is called when a message is received. However, we do not use this feature in
// this project so it will be left empty
void callback(char* topic, byte* payload, unsigned int length) 
{
}

void setup()
{
    // Connect to the server and call ourselves "photonDev"
    client.connect("argonDev");
    
	Serial.begin();
	lightMeter.begin(BH1750LIB_MODE_ONETIMEHIGHRES);
	
	delay(10000);

	pinMode(MOTIONPIN, INPUT);
	motion = inactiveMotion;
}

void loop()
{
    temperature = dht.getTempCelcius();
    humidity = dht.getHumidity();
    light = lightMeter.lightLevel();
    proximity = proximityMeter.getDistanceCM();
    
    sprintf(temperatureStr, "%.1f", temperature);    // assign temperature as a char to temperatureStr
    sprintf(humidityStr, "%.1f", humidity);          // assign humidity as a char to humidityStr
    sprintf(lightStr, "%.1f", light);                // assign light as a char to lightStr
    sprintf(proximityStr, "%.1f", proximity);        // assign proximity as a char to proximityStr
    
    if (client.isConnected())
    {
        client.publish("Temperature", temperatureStr);
        client.publish("Humidity", humidityStr);
        client.publish("Light", lightStr);
        client.publish("Proximity", proximityStr);
        
        if (digitalRead(MOTIONPIN) == HIGH and motion == inactiveMotion) 
        {
            motion = activeMotion;
            client.publish("Motion", "Active");
            delay(1000);
        }
        else if (digitalRead(MOTIONPIN) == LOW and motion == activeMotion) 
        {
            motion = inactiveMotion;
            client.publish("Motion", "Inactive");
            delay(1000);
        }
        
        //Particle.publish("Temperature", temperatureStr, PRIVATE);   // Publish the temperature as an event
        //Particle.publish("Humidity", humidityStr, PRIVATE);         // Publish the humidity as an event
        //Particle.publish("Light", lightStr, PRIVATE);               // Publish the light as an event
        //Particle.publish("Proximity", proximityStr, PRIVATE);       // Publish the proximity as an event
        Particle.publish("Motion", motion, PRIVATE);                // Publish the motion as an event
        // CALL THIS at the end of your loop
        client.loop();
    }
    
	delay(4000);           // wait 5 seconds for next scan
}