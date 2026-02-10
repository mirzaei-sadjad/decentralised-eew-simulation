# -*- coding: utf-8 -*-
"""
Created on Fri Apr 11 12:29:14 2025

@author: 24018273
"""

import os
import geopandas as gpd
import pandas as pd
import numpy as np
import pygmt
from pyproj import Transformer, CRS
from shapely.geometry import Point, Polygon
from shapely.ops import transform, unary_union
from datetime import datetime



'''
Defining constants for visualisation
'''
lat_padding = 0.2
lon_padding = 0.3
p_phase_speed = 6
s_phase_speed = 3.5
sensor_radius = 30
t = 0



'''
For calculating and visualising the radius of communication, based on the
pyproj library, I defined a projection system with the origin of lon and lat,
and buffer points around the origin with distance of km.
The the points are transfered to global projection system.
'''
def geodesic_point_buffer(lon, lat, km):
    # Azimuthal equidistant projection
    aeqd_proj = CRS.from_proj4(
        f"+proj=aeqd +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0")
    tfmr = Transformer.from_proj(aeqd_proj, aeqd_proj.geodetic_crs)
    buf = Point(0, 0).buffer(km * 1000)  # distance in metres
    return transform(tfmr.transform, buf).exterior.coords[:]

'''
I use this function to plot the main elements of the figure at the specific
time.
'''
def base_fig(second):
    fig = pygmt.Figure()
    # UTM Zone is set to 52R
    fig.coast(
        region=[lon_min, lon_max, lat_min, lat_max],
        projection="M12c",
        frame="afg",
        land="gray80",
        water="steelblue",
        )
    
    p_phase = geodesic_point_buffer(earthquake_gdf['longitude'][0],
                                    earthquake_gdf['latitude'][0],
                                    p_phase_speed*second)
    s_phase = geodesic_point_buffer(earthquake_gdf['longitude'][0],
                                    earthquake_gdf['latitude'][0],
                                    s_phase_speed*second)
    
    fig.plot(p_phase, pen='1p,red,-', close=True)
    fig.plot(s_phase, pen='1p,red', close=True)
    
    # ploting each sensor seperately based on status of the sensor
    for i in range(len(sensors_gdf)):
        lon = sensors_gdf['longitude'].iloc[i]
        lat = sensors_gdf['latitude'].iloc[i]
        color = get_color(sensors_gdf['status'].iloc[i])
        if sensors_gdf['status'].iloc[i] == 'Decision':
            fig.plot(x = lon, y = lat, style='i0.3c', fill=color, pen='black')
        else:
            fig.plot(x = lon, y = lat, style='t0.3c', fill=color, pen='black')
            
    fig.text(x = sensors_df.longitude, y = sensors_df.latitude, 
             text=sensors_df.id, offset="0.2c/0.2c")
    fig.plot(earthquake_gdf, style = 'a0.5c', fill = 'red', pen = 'black')
    
    # I can use fig.timestamp for ploting the time as well
    fig.text(text = f'Time: {second} s', position = 'TR', 
             font = '18p,Helvetica-Bold', 
             justify = 'TR', offset = 'j0.5c/0.5c')
    return fig

# Defining a color for each status
def get_color(status):
    if status == 'Observation':
        return 'green'
    elif status == 'Detection':
        return 'yellow'
    elif status == 'Alerted':
        return 'red'
    elif status == 'Decision':
        return 'purple'
    elif status == 'S_Detection':
        return 'black'
    else:
        return 'blue'
    
    

sensors_filename = './data/sensors.csv'
# earthquake_filename = 'scenarios/earthquake_scenario.xlsx'
earthquake_filename = './data/earthquake.csv'

log_filename = './outputs/log_file.csv'

sensors_df = pd.read_csv(sensors_filename)
sensors_df['status'] = 'Observation'
sensors_gdf = gpd.GeoDataFrame(sensors_df, 
                               geometry=gpd.points_from_xy(sensors_df.longitude, sensors_df.latitude), 
                               crs="EPSG:4326"
                               )
earthquake_df = pd.read_csv(earthquake_filename)
earthquake_gdf = gpd.GeoDataFrame(earthquake_df, 
                                  geometry=gpd.points_from_xy(earthquake_df.longitude, earthquake_df.latitude), 
                                  crs="EPSG:4326"
                                  )

log_df = pd.read_csv(log_filename)


alerted_zone = gpd.GeoDataFrame(columns=['geometry'], 
                                geometry='geometry', 
                                crs='epsg:4326')


# Creating a folder for figures based on Date and Time

# folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# try:
#     os.makedirs(os.path.join('./pygmt_export', folder_name))
#     print(f"Folder '{folder_name}' created successfully.")
# except FileExistsError:
#     print(f"Folder '{folder_name}' already exists.")
# except Exception as e:
#     print(f"An error occurred: {e}")
    

    
lat_max = np.max([sensors_df['latitude'].max(), earthquake_df['latitude'].max()]) + lat_padding
lat_min = np.min([sensors_df['latitude'].min(), earthquake_df['latitude'].min()]) - lat_padding
lon_max = np.max([sensors_df['longitude'].max(), earthquake_df['longitude'].max()]) + lon_padding
lon_min = np.min([sensors_df['longitude'].min(), earthquake_df['longitude'].min()]) - lon_padding

fig = base_fig(second=0)
fig.show()

# fig_name = "file_000.jpg"
# fig_path = os.path.join('./pygmt_export', folder_name, fig_name)
# fig.savefig(fig_path)

fig_name = './outputs/pygmt_figures/fig_000.jpg'
fig.savefig(fig_name)
print("N00")

grouped = log_df.groupby('time')
i = 1
for t in sorted(grouped.groups.keys()):
    logs = grouped.get_group(t).query('action == "Produce"')
    if not logs.empty:
        for _, row in logs.iterrows():
            
            '''
            This section needs to be revised
            maybe I should add a loop for each event.
            for example, there might be two detections exactly at the same time
            '''
            
            if row['event'] == 'P_Wave_Detection':
                idx = sensors_gdf[sensors_gdf['id'] == row['sensor_id']].index[0]
                lon = sensors_gdf.iloc[idx]['longitude']
                lat = sensors_gdf.iloc[idx]['latitude']
                sensors_gdf.loc[idx, "status"] = row['status']

                fig = base_fig(row['time'])
                                
                buf = geodesic_point_buffer(lon, lat, sensor_radius)
                actives = row['sensor_id']
                fig.plot(buf, pen='1p,grey', close=True)
                
                fig.basemap(frame='+t' + f'{actives} PRODUCES P-Wave Detection Message')
                fig_name = f"file_00{i}.jpg"
                fig_path = os.path.join('./outputs/pygmt_figures', fig_name)
                fig.savefig(fig_path)
                del fig
                print("#################################################################################################")
                print("N01")
                i=i+1
                
            if row['event'] == 'ConfirmedAlert':
                idx = sensors_gdf[sensors_gdf['id'] == row['sensor_id']].index[0]
                
                # Should be careful about this line:
                sensors_gdf.loc[idx, "status"] = 'Decision'
                # sensors_gdf['status'].iloc[idx] = row['status']
                lon = sensors_gdf.iloc[idx]['longitude']
                lat = sensors_gdf.iloc[idx]['latitude']
                buf = Polygon(geodesic_point_buffer(lon, lat, sensor_radius))
                buf = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[buf])
                alerted_zone = pd.concat([alerted_zone, buf])
                
                # continue;
                
            if row['event'] == 'P_Wave_Update':
                
                idx = sensors_gdf[sensors_gdf['id'] == row['sensor_id']].index[0]
                lon = sensors_gdf.iloc[idx]['longitude']
                lat = sensors_gdf.iloc[idx]['latitude']
                # sensors_gdf['status'].iloc[idx] = row['status']
                actives = row['sensor_id']
                fig = base_fig(row['time'])
                buf = geodesic_point_buffer(lon, lat, sensor_radius)
                
                fig.plot(buf, pen='1p,grey', close=True)
                fig.basemap(frame='+t' + f'{actives} PRODUCED P-Update Message')
                fig_name = f"file_00{i}.jpg"
                fig_path = os.path.join('./outputs/pygmt_figures', fig_name)
                fig.savefig(fig_path)
                del fig
                print("#################################################################################################")
                print("N02")
                i=i+1
    
    
    logs = grouped.get_group(t).query('action == "Receive" and event == "P_Wave_Detection" and reaction != "Ignore"')
    if not logs.empty:
        actives = ''
        for _, row in logs.iterrows():
            idx = sensors_gdf[sensors_gdf['id'] == row['sensor_id']].index[0]
            sensors_gdf.loc[idx, "status"] = row['status']
            actives = actives + ', ' + row['sensor_id']
        
        fig = base_fig(row['time'])
        if len(actives)>=20:
            fig.basemap(frame='+t' + 'Many Sensors RECEIVED P-Wave Detection Message')
        else:
            fig.basemap(frame='+t' + f'{actives} RECEIVED P-Wave Detection Message')
        fig_name = f"file_00{i}.jpg"
        fig_path = os.path.join('./outputs/pygmt_figures', fig_name)
        fig.savefig(fig_path)
        del fig
        print("#################################################################################################")
        print("N03")
        i=i+1
        
    logs = grouped.get_group(t).query('action == "Receive" and event == "ConfirmedAlert" and reaction != "Ignore"')
    if not logs.empty:
        actives = ''
        for _, row in logs.iterrows():
            idx = sensors_gdf[sensors_gdf['id'] == row['sensor_id']].index[0]
            sensors_gdf.loc[idx, "status"] = row['status']
            actives = actives + row['sensor_id'] +', '
            
        fig = base_fig(row['time'])
        
        if len(actives)>=20:
            fig.basemap(frame='+t' + 'Many Sensors RECEIVED Confirmed Message')
        else:
            fig.basemap(frame='+t' + f'{actives} RECEIVED Confirmed Message')
            
        fig_name = f"file_00{i}.jpg"
        fig_path = os.path.join('./outputs/pygmt_figures', fig_name)
        fig.savefig(fig_path)
        del fig
        print("#################################################################################################")
        print("N04")
        i=i+1
    
    logs = grouped.get_group(t).query('action == "Receive" and event == "P_Wave_Update" and reaction != "Ignore"')
    if not logs.empty:
        actives = ''
        for _, row in logs.iterrows():
            idx = sensors_gdf[sensors_gdf['id'] == row['sensor_id']].index[0]
            sensors_gdf.loc[idx, "status"] = row['status']
            # sensors_gdf['status'].iloc[idx] = row['status']
            actives = actives + row['sensor_id'] +', '
        fig = pygmt.Figure()
        fig.coast(
            region=[lon_min, lon_max, lat_min, lat_max],
            projection="M12c",
            frame="afg",
            land="gray80",
            water="steelblue",
        )
        
        p_phase = geodesic_point_buffer(earthquake_gdf['longitude'][0],
                                        earthquake_gdf['latitude'][0],
                                        p_phase_speed*row['time'])
        s_phase = geodesic_point_buffer(earthquake_gdf['longitude'][0],
                                        earthquake_gdf['latitude'][0],
                                        s_phase_speed*row['time'])
        
        fig.plot(p_phase, pen='1p,red,-', close=True)
        fig.plot(s_phase, pen='1p,red', close=True)
        
        for _, row in sensors_gdf.iterrows():
            idx = sensors_gdf[sensors_gdf['id'] == row['id']].index[0]
            lon = sensors_gdf['longitude'].iloc[idx]
            lat = sensors_gdf['latitude'].iloc[idx]
            color = get_color(sensors_gdf['status'].iloc[idx])
            
            if row['status'] == 'Decision':
                fig.plot(x = lon, y = lat, style='i0.3c', fill=color, pen='black')
            else:
                fig.plot(x = lon, y = lat, style='t0.3c', fill=color, pen='black')
                
        fig.text(x = sensors_df.longitude, y = sensors_df.latitude, text=sensors_df.id, offset="0.2c/0.2c")
        fig.plot(earthquake_gdf, style='a0.5c', fill='red', pen='black')
        fig.text(text = f'Time: {t} s', position = 'TR', font = '18p,Helvetica-Bold', justify = 'TR', offset = 'j0.5c/0.5c')
        
        if len(actives)>=20:
            fig.basemap(frame='+t' + 'Many Sensors RECEIVED P-Update Message')
        else:
            fig.basemap(frame='+t' + f'{actives} RECEIVED P-Update Message')
        # fig.basemap(frame='+t' + f'{actives} Recieved P-Update Message')
        fig_name = f"file_00{i}.jpg"
        fig_path = os.path.join('./outputs/pygmt_figures', fig_name)
        fig.savefig(fig_path)
        del fig
        print("#################################################################################################")
        print("N05")
        i=i+1
        
        
    logs = grouped.get_group(t).query('action == "Rebroadcast" and event == "ConfirmedAlert"')
    if not logs.empty:
        active = ''
        for _, row in logs.iterrows():
            idx = sensors_gdf[sensors_gdf['id'] == row['sensor_id']].index[0]
            lon = sensors_gdf['longitude'].iloc[idx]
            lat = sensors_gdf['latitude'].iloc[idx]
            buf = Polygon(geodesic_point_buffer(lon, lat, sensor_radius))
            buf = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[buf])
            alerted_zone = pd.concat([alerted_zone, buf])
            actives + row['sensor_id'] +', '
        
        merged_zone = unary_union(alerted_zone['geometry'])
        merged_gdf = gpd.GeoDataFrame({'geometry': [merged_zone]}, crs='epsg:4326')
        fig = base_fig(row['time'])
        fig.plot(merged_gdf, pen='1p,orange', close=True)
        if len(actives)>=20:
            fig.basemap(frame='+t' + 'Many Sensors REBROADCASTED Confirmed Message')
        else:
            fig.basemap(frame='+t' + f'{actives} REBROADCASTED Confirmed Message')
        fig_name = f"file_00{i}.jpg"
        fig_path = os.path.join('./outputs/pygmt_figures', fig_name)
        fig.savefig(fig_path)
        del fig
        print("#################################################################################################")
        print("N06")
        i=i+1
    
