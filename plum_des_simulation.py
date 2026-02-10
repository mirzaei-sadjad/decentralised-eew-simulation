# -*- coding: utf-8 -*-
"""
Created on Fri May 23 15:23:48 2025

@author: 24018273
"""

import simpy
import math
import random
import pandas as pd
import numpy as np
import csv
import re
from pyproj import Proj, Transformer


TRANSMISSION_RANGE_KM: float() = 30 # Based on original PLUM algorithm
P_WAVE_SPEED_KM_PER_S: float() = 6  # Approximate speed of P-wave in km/s
S_WAVE_SPEED_KM_PER_S:float() = 3.5  # Approximate speed of S-wave in km/s
transmission_delay:float = 0.05 # Based on TCP protocol
waiting_window:float = 5 # Waiting window for confirming an event
sensor_id_len:int = 3 #lenth of the sensor IDs

false_detection_probability = 0.1 # chance for detecting a noise as earthquake
miss_probability = 0.2 # chance for missing a detection


# Function for calculating the distance between two sensors
# later on, this should be replaced by proper library
def calculate_distance(loc1, loc2):
    lat1, lon1 = loc1
    lat2, lon2 = loc2
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# Function for creating random number as peak displacement
# because at the moment, the simulation doesn't read a ground motion
# record directly from suitable file.
def simulate_displacement():
    return round(random.uniform(0.1, 10.0), 2)  # cm


# Defining a class for Messages and it's initial values
class Message:
    def __init__(self, msg_type, sender_id, timestamp, event_id=None,\
                 update_path=None, content=None, path=None ):
        self.type = msg_type
        self.sender = sender_id
        self.time = timestamp
        self.event_id = event_id
        self.update_path = update_path or []
        self.content = content or []
        self.path = path or []
        
'''
Here we define the network structure. each sensor has it's own known sensors
which are located with distances of less than TRANSMISSION_RANGE_KM.
So the sensor can communicate with them.
Based on the ID of known sensors, we define a dictionary which record the 
location, P_Value and S_Value of all known sensors for further analysis.

The transmission delay of the network had been simulated in here as well.
transmission_delay is applied to all communications. The sender sends the 
message to all known sensors at once, and all the recipients receive it 
after transmission_delay.
'''
class Network:
    def __init__(self, sensors):
        self.sensors = sensors

    def initialize_known_sensors(self):
        for sensor in self.sensors:
            sensor.known_sensors = {
                s.id: {
                    'location': s.location,
                    'P_Value': None,
                    'S_Value': None
                }
                for s in self.sensors if s.id != sensor.id
            }


    def broadcast(self, message, sender):
        for receiver in self.sensors:
            if receiver.id != sender.id:
                dist = calculate_distance(receiver.location, sender.location)
                if dist <= TRANSMISSION_RANGE_KM:
                    delay = transmission_delay
                    sender.env.process(self.deliver_with_delay(receiver, message, delay))
                    
    def deliver_with_delay(self, recipient, message, delay):
        yield recipient.env.timeout(delay)
        recipient.receive(message)                                               
        
        
# Defining a class for Sensors withing the network
class Sensor:
    def __init__(self, env, sensor_id, location, network):
        self.env = env
        self.id = sensor_id
        self.location = location
        self.network = network
        self.status = 'Observation'
        self.first_detection = None
        self.second_detection = None
        self.third_detection = None
        self.fourth_detection = None
        self.p_detection = None
        self.s_detection = None
        self.received_detection = False
        self.received_confirmed = False
        self.received_updates = []
        self.event_id = None
        self.peak_displacement = None #######
        self.known_sensors = {}
        self.previous_update_timestamp = None
        
        self.P_peak = None
        self.S_peak = None
        self.p_update = False
        self.s_update = False
        
        self.event_location = None
        self.event_origin = None
        
        
    # The function for P phase detection. It might happen while the sensors
    # have different statuses [Observation, Detection, Alerted, Decision]
    def detect_p_wave(self, timestamp):
        # msg = Message("Detection", self.id, timestamp, event_id='NaN', content = self.P_peak)
        # self.network.broadcast(msg, self)
        
        # log_event(self.env.now, self.id, self.status, 'Produce', 'P_Wave_Detection', 'NaN', 'WaitForConfirmation', self.P_peak)
        
        if self.status == 'Observation':
            print(f"{timestamp:.3f}s - Sensor {self.id} DETECTED earthquake (P-wave).")
            self.status = 'Detection'
            self.first_detection = (self.id, timestamp)
            self.P_peak= simulate_displacement()
            msg = Message("Detection", self.id, timestamp, event_id='NaN', content = self.P_peak)
            self.network.broadcast(msg, self)
            
            log_event(self.env.now, self.id, self.status, 'Produce', 'P_Wave_Detection', 'NaN', 'WaitForConfirmation', self.P_peak)
            self.start_detection_timer()
            
        
        elif self.status == 'Detection':
            print(f"{timestamp:.3f}s - Sensor {self.id} DETECTED earthquake (P-wave).")
            self.status = 'Alerted'
            self.second_detection = (self.id, timestamp)
            self.received_confirmed = True
            s1_id, t1 = self.first_detection
            s2_id, t2 = (self.id, timestamp)
            event_id = f"{s1_id}{self.format_time(t1)}{s2_id}{self.format_time(t2)}"

            self.event_id = event_id
            msg = Message("Detection", self.id, timestamp, event_id='NaN', content = self.P_peak)
            self.network.broadcast(msg, self)
            log_event(self.env.now, self.id, self.status, 'Produce', 'P_Wave_Detection', 'NaN', 'StatusToAlerted', self.P_peak)
           
            
            # msg = Message("Confirmed", self.id, timestamp, event_id=event_id)
            self.p_detection = timestamp
            log_event(self.env.now, self.id, self.status, 'ChangeStatus', 'ConfirmedAlert', 'NaN', 'StatusToAlerted', 'NaN')
            
            
            
            # Producing the Update message rirht after the Confirmed Alert
            # self.P_peak= simulate_displacement()
            # self.status = 'Decision'
            # msg = Message('Update', self.id, timestamp, event_id=event_id, content = self.P_peak)
            # print(f"{timestamp:.3f}s - Sensor {self.id} PRODUCED an Update (P-wave).")
            # log_event(self.env.now, self.id, self.status, 'Produce', 'P_Wave_Update', 'NaN', 'NaN', self.P_peak)
            # self.network.broadcast(msg, self)
            # self.p_update = True
        
        elif self.status == 'Alerted':
            print(f"{timestamp:.3f}s - Sensor {self.id} DETECTED earthquake (P-wave).")
            msg = Message("Detection", self.id, timestamp, event_id='NaN', content = self.P_peak)
            self.network.broadcast(msg, self)
            
            log_event(self.env.now, self.id, self.status, 'Produce', 'P_Wave_Detection', 'NaN', 'WaitForConfirmation', self.P_peak)
        # else:
        #     print(f"{timestamp:.3f}s - Sensor {self.id} received P-wave but cannot produce Detection message (Status: {self.status})")
            # log_event(self.env.now, self.id, self.status, 'Error1', 'NaN', 'NaN', 'NaN', 'NaN')
            
        
    def start_detection_timer(self):
        self.env.process(self.wait_for_confirmation())


    def wait_for_confirmation(self):
        yield self.env.timeout(waiting_window)
        if self.status == 'Detection' and not self.received_confirmed:
            self.first_detection = None
            self.status = 'Observation'
            print(f"{self.env.now:.3f}s - Sensor {self.id} timed out waiting for confirmation.")
            log_event(self.env.now, self.id, self.status, 'EventCancelation', 'NaN', 'NaN', 'BackToObservation', 'NaN')
            
    
    def receive(self, msg):
        # the first two If can be merged
        if msg.type == "Detection" and self.status == "Observation":
            self.status = 'Detection'
            self.first_detection = (msg.sender, msg.time)
            self.start_detection_timer()
            log_event(self.env.now, self.id, self.status, 'Receive', 'P_Wave_Detection', msg.sender, 'WaitForConfirmation', 'NaN')
            # log_event(self.env.now, self.id, "ReceivedDetection", f"From{msg.sender}")
            
        elif msg.type == "Detection" and self.status == 'Detection':
            log_event(self.env.now, self.id, self.status, 'Receive', 'P_Wave_Detection', msg.sender, 'StatusToAlerted', 'NaN')
            # log_event(self.env.now, self.id, "ReceivedDetection", f"From{msg.sender}")
            self.received_confirmed = True
            self.second_detection = (msg.sender, msg.time)
            s1_id, t1 = self.first_detection
            s2_id, t2 = (msg.sender, msg.time)
            event_id = f"{s1_id}{self.format_time(t1)}{s2_id}{self.format_time(t2)}"
            # print('2', event_id)
            self.event_id = event_id
            # msg = Message("Confirmed", self.id, self.env.now, event_id=event_id)
            self.status = 'Alerted'
            log_event(self.env.now, self.id, self.status, 'ChangeStatus', 'ConfirmedAlert', msg.sender, 'StatusToAlerted', 'NaN')
            # log_event(self.env.now, self.id, self.status, 'Produce', 'ConfirmedAlert', 'NaN', 'StatusToAlerted', 'NaN')
            # log_event(self.env.now, self.id, "ProducedConfirmationMessage", "StatusToAlerted")
            #self.p_detection = (self.id, timestamp)
            # self.network.broadcast(msg, self)
            # print(f"{self.env.now:.3f}s - Sensor {self.id} produced a Confirmed message.")
            
                        
        # elif msg.type == "Confirmed":
        #     if self.status in ['Observation', 'Detection']:
        #         self.status = 'Alerted'
        #         self.received_confirmed = True
        #         self.event_id = msg.event_id
                
        #         '''
        #         When a sensors receives a Confirmed message for the first time,
        #         it should update the first_detection and second_detection
        #         variables. as follow:
        #         '''
                
        #         if self.first_detection == None:
        #             pattern = r"(?P<s1>[a-zA-Z0-9]{3})(?P<t1_h>\d{2})(?P<t1_m>\d{2})(?P<t1_s>\d{2}\.\d{3})(?P<s2>[a-zA-Z0-9]{3})(?P<t2_h>\d{2})(?P<t2_m>\d{2})(?P<t2_s>\d{2}\.\d{3})"
        #             matched = re.fullmatch(pattern, msg.event_id)
        #             t1_timestamp = int(matched.group('t1_h')) * 3600 + int(matched.group('t1_m')) * 60 + float(matched.group('t1_s'))
        #             self.first_detection = (matched.group('s1'), t1_timestamp)
        #             # print('First_Detection Updated!')
                    
        #         elif self.second_detection == None:
        #             pattern = r"(?P<s1>[a-zA-Z0-9]{3})(?P<t1_h>\d{2})(?P<t1_m>\d{2})(?P<t1_s>\d{2}\.\d{3})(?P<s2>[a-zA-Z0-9]{3})(?P<t2_h>\d{2})(?P<t2_m>\d{2})(?P<t2_s>\d{2}\.\d{3})"
        #             matched = re.fullmatch(pattern, msg.event_id)
        #             t2_timestamp = int(matched.group('t2_h')) * 3600 + int(matched.group('t2_m')) * 60 + float(matched.group('t2_s'))
        #             self.second_detection = (matched.group('s2'), t2_timestamp)
        #             # print('Second_Detection Updated!')
                    
        #         '''
        #         Here, the sensor should be able to fill self.first_detection
        #         and self.second_detection based on received event_id
        #         All done on 2025-04-22
        #         '''
        #         print(f"{self.env.now:.3f}s - Sensor {self.id} is now ALERTED by Confirmed message.")
        #         log_event(self.env.now, self.id, self.status, 'Receive', 'ConfirmedAlert', msg.sender, 'StatusToAlerted', 'NaN')
                
        #         # log_event(self.env.now, self.id, self.status, 'Rebroadcast', 'ConfirmedAlert', 'NaN', 'NaN', 'NaN')
        #         # msg = Message("Confirmed", self.id, self.env.now, event_id=self.event_id)
        #         # self.network.broadcast(msg, self)
                
            # else:
            #     # print(f"{self.env.now:.3f}s - Sensor {self.id} is already ALERTED by Confirmed message. (Ignore)")
            #     log_event(self.env.now, self.id, self.status, 'Receive', 'ConfirmedAlert', msg.sender, 'Ignore', 'NaN')
                
    def format_time(self, t):
        h, rem = divmod(float(t), 3600)
        m, s = divmod(rem, 60)
        
        return f"{h:02.0f}{m:02.0f}{s:06.3f}"
    
def simulate_earthquake(env, epicenter, sensors):
    print(f"{env.now:.3f}s - Earthquake Simulation Started.")
    distances = [(sensor, calculate_distance(sensor.location, epicenter)) for sensor in sensors]
    for sensor, dist in distances:
        p_delay = dist / P_WAVE_SPEED_KM_PER_S
        s_delay = dist / S_WAVE_SPEED_KM_PER_S
        env.process(trigger_p_wave(env, sensor, p_delay))
        # env.process(trigger_s_wave(env, sensor, s_delay))

def trigger_p_wave(env, sensor, delay):
    yield env.timeout(delay)
    sensor.detect_p_wave(env.now)
    
'''
In here we load the data regarding to each senor
'''
def load_sensors_from_csv(env, filename):
    sensors = []
    sensor_file = pd.read_csv(filename)
    for row in range(len(sensor_file)):
        sensor_id = sensor_file.id[row]
        lat = sensor_file.latitude[row]
        lon = sensor_file.longitude[row]
        sensors.append(Sensor(env, sensor_id, (lat, lon), None))
    return sensors


'''
The log file of the simulation. All events are recorded here.
'''
def log_event(time, sensor_id, sensor_status, action, event_type, sender_id, reaction, value):
    simulation_log.append({
        'time': round(time, 4),
        'sensor_id': sensor_id,
        'status':sensor_status,
        'action': action,
        'event': event_type,
        'sender_id': sender_id,
        'reaction': reaction,
        'value': value
    })

def save_log_to_csv(filename='./outputs/simulation_log.csv'):
    keys = ['time', 'sensor_id','status', 'action', 'event', 'sender_id', 'reaction', 'value']
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(simulation_log)
        
if __name__ == "__main__":
    # simulation_log = []
    log_file = pd.DataFrame()
    randomness_log_file = pd.DataFrame()
    earthquake_df = pd.read_csv('./data/earthquake.csv')
    simulation_duration = 120
    # Without Randomness in P-phase Detection
    for _, earthquake in earthquake_df.iterrows():
        env = simpy.Environment()
        sensor_list = load_sensors_from_csv(env, './data/sensors.csv')
        network = Network(sensor_list)
        for sensor in sensor_list:
            sensor.network = network
        network.initialize_known_sensors()
        simulation_log = []
        simulate_earthquake(env, (earthquake.latitude, earthquake.longitude), sensor_list)
        env.run(simulation_duration)
        log = pd.DataFrame.from_dict(simulation_log)
        log['eq_id'] = earthquake.id
        log_file = pd.concat([log_file, log])
    log_file.to_csv('./outputs/log_file.csv')
