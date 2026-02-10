# -*- coding: utf-8 -*-
"""
Created on Mon May 26 12:28:08 2025

@author: 24018273
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from manim import *
from shapely.geometry import Polygon as shapely_polygon
import utm
import pyproj as proj
# from statistics import mean
from shapely.geometry import Point, box
from shapely.geometry import Polygon as polyg
from shapely import unary_union, intersection_all #coverage_union, union_all, normalize
from shapely.geometry import MultiPolygon as shapely_multipolygon
import matplotlib.pyplot as plt
# from pyproj import Transformer


p_velocity = 6
s_velocity = 3.5

sensors_df = pd.read_csv("./data/sensors.csv")
log_df = pd.read_csv("outputs/log_file.csv")
eq_df = pd.read_csv("./data/earthquake.csv")
nz_borders = gpd.read_file("./data/nz_borders_multipolygon_2.shp")

# areas=[]
# for i, row in shapefile.iterrows():
#     areas.append(row.geometry.area)
# sorted_areas = np.argsort(areas)[::-1]
# area = []
# for i in range(10):
#     area.append(shapefile.loc[sorted_areas[i], 'geometry'])


def lonlat_to_xy(lon, lat, origin_lon = eq_df.longitude[0], origin_lat = eq_df.latitude[0]):
    # Azimuthal equidistant projection
    crs_wgs = proj.Proj(init='epsg:4326')
    cust = proj.Proj(proj="aeqd", lat_0=origin_lat, lon_0=origin_lon, datum="WGS84", units="m")
    x, y = proj.transform(crs_wgs, cust, lon, lat)
    return [x, y]


all_x = 0
all_y = 0
min_x = 0
max_x = 0
min_y = 0
max_y = 0

for _, row in sensors_df.iterrows():
    x, y = lonlat_to_xy(row.longitude, row.latitude)#, eq_df.longitude[0], eq_df.latitude[0])
    min_x = min(min_x, x)
    max_x = max(max_x, x)
    min_y = min(min_y, y)
    max_y = max(max_y, y)
    
    all_x = all_x + x
    all_y = all_y + y
sensors_x = all_x / len(sensors_df)
sensors_y = all_y / len(sensors_df)

def update_waves(timestamp, p_wave, s_wave):
    wave_animation=[]
    p_wave.generate_target()
    current_time = p_wave.width / (2*p_velocity*1000)
    p_wave.target.set(width = 2*p_velocity*timestamp*1000) # I should convert km to m, because the unit in my map is meter
    wave_animation.append(MoveToTarget(p_wave,rate_func=rate_functions.linear, run_time = timestamp - current_time))#)
    
    s_wave.generate_target()
    s_wave.target.set(width = 2*s_velocity*timestamp*1000) # I should convert km to m, because the unit in my map is meter
    wave_animation.append(MoveToTarget(s_wave,rate_func=rate_functions.linear, run_time = timestamp - current_time))
    return p_wave, s_wave, wave_animation
        
def get_color(status):
    if status == 'Observation':
        return GREEN
    elif status == 'Detection':
        return YELLOW
    elif status == 'Alerted':
        return RED
    elif status == 'Decision':
        return PURPLE
    elif status == 'P_Wave_Experienced':
        return PURPLE
    elif status == 'S_Detection':
        return BLACK
    else:
        return BLUE
    
class original_plum(MovingCameraScene):
        
    def construct(self):
        
        '''Showing the map on the background'''
        lat_min = np.min([np.min(sensors_df['latitude']), eq_df.latitude[0]])-1
        lat_max = np.max([np.max(sensors_df['latitude']), eq_df.latitude[0]])+1
        lon_min = np.min([np.min(sensors_df['longitude']), eq_df.longitude[0]])-1
        lon_max = np.max([np.max(sensors_df['longitude']), eq_df.longitude[0]])+1

        area_of_interest = nz_borders.intersection(box(lon_min, lat_min, lon_max, lat_max))
        mp = shapely_multipolygon(area_of_interest[0])
        polygons_of_interest = list(mp.geoms)
        animation=[]
        for row in polygons_of_interest:
            coords=[]
            # poly = shapely_polygon(row)
            # print(poly.exterior.coords[:])
            for lon, lat in row.exterior.coords[:]:
                # print(lon, lat)
                x, y = lonlat_to_xy(lon, lat)
                coords.append([x, y, 0])
            nz = Polygon(*coords, 
                         color = GOLD_E, 
                         stroke_width = 10000,
                         stroke_color = BLACK,
                         fill_color = GOLD_E, 
                         fill_opacity=0.5)
            animation.append(Add(nz, run_time=0.01))
        self.play(AnimationGroup(*animation, lag_ratio = 0.0))
        
        '''
        An initial oppening scene, drawing a triangle and moving it to the
        corner and ...
        It was omitted before version 1.5
        '''
        # temp = Triangle().scale(10000).set_fill(BLUE, opacity=60)
        # temp = Triangle().set(width=10000).set_fill(BLUE, opacity=60)
        # self.play(DrawBorderThenFill(temp), run_time=2)
        # self.wait(1)
        # temp.generate_target()
        # temp.target.scale(0.25)
        # temp.target.to_edge(DR, buff=10000)
        # self.play(MoveToTarget(temp), run_time = 2)
        # self.wait(1)
        
        # animation=[]
        # # animation.append(FadeOut(temp, scale=0.001))
        # # self.play(FadeOut(temp), scale=0.25)#, run_time=len(sensors)*0.1)
        # for _, row in self.sensors.items():
        #     animation.append(row['marker'].animate.move_to([row['x'], row['y'],0]))
        
        # self.play(AnimationGroup(*animation, lag_ratio=0.1))
        # self.wait(2)
        
        '''Preparing the Sensors and their symbols'''
        self.sensors={}
        animation = []
        sensors_list = []
        
        for i, row in sensors_df.iterrows():
            x, y = lonlat_to_xy(row.longitude, row.latitude)#, eq_df.longitude[0], eq_df.latitude[0])
            triangle = Triangle().set(height=4000).set_color(BLUE).set(stroke_width=50000).set_stroke(BLUE, opacity=1).set_fill(BLUE, opacity=1).move_to([x, y, 0])#.scale(2500)
            sensors_list.append(triangle)
            sensor_name = Text(row.id).match_height(sensors_list[i]).next_to(sensors_list[i], RIGHT)
            # Text('Missed', color=RED)
            animation.append(DrawBorderThenFill(triangle, run_time=2))
            animation.append(Write(sensor_name))
            
            self.sensors[row['id']] = {
                'lat': row.latitude,
                'lon': row.longitude,
                # 'alt': alt,
                'y': y,
                'x': x,
                # 'z': z,
                'status': 'Observation',
                'marker': triangle,
                'p_value':None
                }
        
        '''Changing the camera zoom and position'''
        self.play(self.camera.auto_zoom(sensors_list, margin=20*1000))

        '''Animation command to display the sensors on screen'''
        self.play(AnimationGroup(*animation, lag_ratio = 0.1))
   
        '''Animation command to change the color of the sensors to GREEN'''
        animation=[]
        for _, row in self.sensors.items(): animation.append(row['marker'].animate.set_color(GREEN))
        self.play(AnimationGroup(*animation, lag_ratio=0.1))
        
        '''Defining the earthquake symbol and changing the zoom'''
        eq = Star(n=8, density=2, outer_radius=10000, inner_radius=3000).set_color(YELLOW).set_fill(RED, opacity=60)#.scale(10000)
        self.play(self.camera.auto_zoom([*sensors_list, eq], margin=20*1000))
        self.play(DrawBorderThenFill(eq), run_time=2)
        eq.generate_target()
        eq.target.scale(0.4)
        eq.target.move_to([0,0,0])
        self.play(MoveToTarget(eq, run_time = 2))
        
        '''Defining the P and S waves'''
        p_wave = Circle(radius=1.0, stroke_width = 40000, stroke_color = ORANGE, )
        s_wave = Circle(radius=1.0, stroke_width = 65000, stroke_color = RED, )
        self.play(FadeIn(p_wave, s_wave))
        
        '''Using ValueTracker for showing the time on the screen'''
        tracker = ValueTracker(0)
        time = always_redraw(lambda: DecimalNumber(tracker.get_value(), num_decimal_places = 2, unit=r"\text{ Sec}").set_color(BLACK).set(height=0.07*self.camera.frame_height).move_to([self.camera.frame_center[0]+0.35*self.camera.frame_width, self.camera.frame_center[1]+0.45*self.camera.frame_height, 0]))
        self.add(time)
        
        '''Focusing on the sensors and ignoring the Epicenter'''
        self.play(self.camera.auto_zoom(sensors_list, margin=20*1000))#, run_time = first_event_time)
        
        '''Initialising some variables and starting the loop'''
        grouped = log_df.groupby('time')
        last_time = 0
        first_event_time = log_df.loc[0, 'time']
        
        for t in sorted(grouped.groups.keys()):
            '''
            Updating P and S waves in the scene and the Time idicator
            '''
            p_wave, s_wave, wave_animation = update_waves(t, p_wave, s_wave)
            wave_animation.append(tracker.animate(run_time=t-last_time, rate_func=rate_functions.linear).set_value(t))
            self.play(AnimationGroup(*wave_animation, lag_ratio=0.0))
            
            animation = []
            
            '''
            Produce
            '''
            actions = log_df.query(f'time=={t} and action=="Produce"')
            if not actions.empty:
                
                ''' Produce P_Wave_Detection'''
                action = actions.query('event=="P_Wave_Detection"')
                if not action.empty:
                    # circle_list = []
                    for _, act in action.iterrows():
                        self.sensors[act['sensor_id']].update(p_value=act.get('value'))
                        
                        # find the symbol of sender
                        symbol = self.sensors[act['sensor_id']].get('marker')
                        status = self.sensors[act['sensor_id']].get('status')
                        if status == 'Observation':
                            self.sensors[act['sensor_id']].update(status='Detection')
                            status = self.sensors[act['sensor_id']].get('status')
                        
                        # change the color of the sender
                        symbol_color = get_color(status)
                        symbol.generate_target()
                        symbol.target.set_color(symbol_color)
                        symbol.target.set_fill(symbol_color)
                        # animation1.append(Wiggle(symbol, scale_value=1.5, n_wiggles=3,run_time=1))
                        animation.append(MoveToTarget(symbol, run_time = 1))
                        
                        
                    
                        # # draw the circle with radius of 30 km
                        # x = self.sensors[act['sensor_id']].get('x')
                        # y = self.sensors[act['sensor_id']].get('y')
                        # c = Circle(radius= 30 * 1000,
                        #            stroke_width = 10000, 
                        #            color = symbol_color, 
                        #            fill_color = symbol_color, 
                        #            stroke_color = symbol_color, 
                        #            fill_opacity = 0.1)
                        
                        # # move the circle over the sender befor showing on scene
                        # c.set_x(x)
                        # c.set_y(y)
                        
                        # # save the list of all circles for adjusting the camera zoom
                        # circle_list.append(c)
                        
                        # # record the animation
                        # animation.append(Succession(DrawBorderThenFill(c, run_time=1, rate_func=rate_functions.linear), Wait(0.5), FadeOut(c, run_time=0.5)))
                        '''
                        5. figure a way to show the message transmission
                        I can use arrows and moving objects later
                        '''
            
            '''
            Receive
            '''
            actions = log_df.query(f'time=={t} and action=="Receive"')
            if not actions.empty:
                
                ''' Recieve P_Wave_Detection'''
                action = actions.query('event=="P_Wave_Detection"')
                if not action.empty:
                    circle_list = []
                    for _, act in action.iterrows():
                        
                        # find the symbol of sensor
                        symbol = self.sensors[act['sensor_id']].get('marker')
                        if self.sensors[act['sensor_id']].get('status') != 'Alerted':
                            self.sensors[act['sensor_id']].update(status='Detection')
                        status = self.sensors[act['sensor_id']].get('status')
                        
                        
                        sender_symbol = self.sensors[act['sender_id']].get('marker')
                        arrow = Line(start = sender_symbol.get_center(), 
                                      end = symbol.get_center(), 
                                      buff = symbol.get_height(), 
                                      stroke_width = 5*symbol.get_height(), 
                                      color = BLACK,)
                                      # max_stroke_width_to_length_ratio=100)
                        animation.append(Succession(Write(arrow, run_time=1, rate_func=rate_functions.linear), Wait(0.5), Unwrite(arrow, run_time=0.5, rate_func=rate_functions.linear)))
                        
                        # change the color of the sender
                        symbol_color = get_color(status)
                        symbol.generate_target()
                        symbol.target.set_color(symbol_color)
                        symbol.target.set_fill(symbol_color)
                        # animation1.append(Wiggle(symbol, scale_value=1.5, n_wiggles=3,run_time=1))
                        
                        
                        # draw the circle with radius of 30 km
                        x = self.sensors[act['sensor_id']].get('x')
                        y = self.sensors[act['sensor_id']].get('y')
                        c = Circle(radius= 30 * 1000,
                                   stroke_width = 10000, 
                                   color = symbol_color, 
                                   fill_color = symbol_color, 
                                   stroke_color = symbol_color, 
                                   fill_opacity = 0.1).move_to([x, y, 0])
                        
                        # move the circle over the sender befor showing on scene
                        # c.set_x(x)
                        # c.set_y(y)
                        
                        # save the list of all circles for adjusting the camera zoom
                        circle_list.append(c)
                        
                        # record the animation
                        animation.append(Succession(DrawBorderThenFill(c, run_time=1, rate_func=rate_functions.linear), Wait(0.5), FadeOut(c, run_time=0.5)))
                        animation.append(MoveToTarget(symbol, run_time = 1))            
            
            '''
            ChangeStatus
            '''
            actions = log_df.query(f'time=={t} and action=="ChangeStatus"')
            if not actions.empty:
                
                # ''' Produce P_Wave_Detection'''
                action = actions.query('event=="ConfirmedAlert"')
                if not action.empty:
                    # circle_list = []
                    for _, act in action.iterrows():
                        # self.sensors[act['sensor_id']].update(p_value=act.get('value'))
                        
                        # find the symbol of sensor
                        symbol = self.sensors[act['sensor_id']].get('marker')
                        self.sensors[act['sensor_id']].update(status='Alerted')
                        status = self.sensors[act['sensor_id']].get('status')
                        
                        # change the color of the sender
                        symbol_color = get_color(status)
                        symbol.generate_target()
                        symbol.target.set_color(symbol_color)
                        symbol.target.set_fill(symbol_color)
                        # animation1.append(Wiggle(symbol, scale_value=1.5, n_wiggles=3,run_time=1))
                        animation.append(MoveToTarget(symbol, run_time = 1))
            
            
            '''
            Event Cancelation
            '''    
            actions = log_df.query(f'time=={t} and action=="EventCancelation"')
            if not actions.empty:
                symbol_list = []
                for _, act in actions.iterrows():
                    
                    symbol = self.sensors[act['sensor_id']].get('marker')
                    self.sensors[act['sensor_id']].update(status='Observation')
                    self.sensors[act['sensor_id']].update(p_value=None)
                    symbol_list.append(symbol)
                    x = self.sensors[act['sensor_id']].get('x')
                    y = self.sensors[act['sensor_id']].get('y')
                    status = self.sensors[act['sensor_id']].get('status')
                    
                    # change the color of the sensor
                    symbol_color = get_color(status)
                    symbol.generate_target()
                    symbol.target.set_color(symbol_color)
                    symbol.target.set_fill(symbol_color)
                    # animation1.append(Wiggle(symbol, scale_value=1.5, n_wiggles=3,run_time=1))
                    animation.append(MoveToTarget(symbol, run_time = 1))
                        
            '''Running the animation command for this iteration of the loop'''
            last_time = t
            if animation:
                self.play(AnimationGroup(*animation, lag_ratio=0.0))
                
with tempconfig({"frame_height": 2 * max(abs(min_y), abs(max_y)),
                 "frame_width" : 2 * max(abs(min_x), abs(max_x)),
                 # "disable_caching" : True,
                 "preview": True,
                 "max_files_cached": 500,
                 "quality": "medium_quality", 
                 "background_color" : BLUE_B}):
    scene = original_plum()
    scene.render()    
