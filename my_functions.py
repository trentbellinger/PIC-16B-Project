import pandas as pd
import re
import string
from datetime import datetime
import plotly.express as px
import string
import numpy as np

def add_zero(string):
    for i in range(0, 4-len(string)):
        string = '0' + string
    return string

def clean_data(df):
    # Get rid of cancelled flights
    df = df[df['CANCELLED'] == 0]
    df = df[df['ARR_TIME'].notna() & df['ARR_DELAY'].notna()]
    # Deal with NA's 
    df.fillna(0, inplace=True)
    
    # Assign target outcome
    df['target'] = (df['ARR_DELAY'] > 0).astype(int)

    # only keep >750 flights
    origin_counts = df.groupby('ORIGIN').size().reset_index(name='counts')
    df = df.merge(origin_counts, on='ORIGIN', how='left')
    df = df[df['counts']> 750]
    
    # Convert Time 
    df.loc[:, 'DEP_TIME'] = df['DEP_TIME'].astype(int).astype(str)
    df.loc[:,'DEP_TIME'] = df['DEP_TIME'].apply(add_zero)
    df.loc[:,'DEP_TIME'] = df['DEP_TIME'].str.slice(start=0, stop=-2) + ':' + df['DEP_TIME'].str.slice(start=-2)
    df.loc[:,'DEP_TIME'] = df['DEP_TIME'].apply(lambda x: '00' + x[2:] if x.startswith('24') else x)
    df.loc[:,'DEP_TIME'] = pd.to_datetime(df['DEP_TIME'], format='%H:%M').dt.time
    df['DEP_TIME'] = pd.to_datetime(df['DEP_TIME'], format='%H:%M:%S')
    # Cyclical engineering for time
    df['hour'] = df['DEP_TIME'].dt.hour
    df['sin_hour'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['cos_hour'] = np.cos(2 * np.pi * df['hour'] / 24)
    # Cyclical engineering for day of week 
    df['sin_day'] = np.sin(2 * np.pi * df['DAY_OF_WEEK'] / 7)
    df['cos_day'] = np.cos(2 * np.pi * df['DAY_OF_WEEK'] / 7)
    return df
