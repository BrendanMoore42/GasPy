import json
import time
import random
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

header = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

"""
Two steps: 
1. get gas prices from list in html with soup
2. get station info from requests
3. Combine and $$$
"""

def main(now, locations, temp_dfs):
    for loc in locations:
        url = f'https://www.gasbuddy.com/GasPrices/Ontario/{loc}'
        url_soup = requests.get(url)

        # Prices list
        soup = BeautifulSoup(url_soup.content, "html.parser")
        # Find prices
        prices = soup.text.split('p.a = ')[1].split(';\r')[0].replace('[', '').replace(']', '').split(',"')
        # Clean and remove 0's
        prices = [i.replace('"', '') for i in prices if len(i) > 1]

        # Stations dataframe
        r = requests.get(url, headers=header)
        # Set dataframe
        df = pd.read_html(r.text)[0]
        # Clean dataframe
        df = df[[1, 2, 3]].dropna().rename(columns={1: 'Station', 2: 'City', 3: 'Date'})

        # Find cities
        city = df.City.iloc[0]
        # Skips uninteresting rows
        df = df[df.index % 2 == 0]

        # Set values
        df['Prices'] = prices
        df['Address'] = df.Station.apply(lambda x: x.split(')  ')[1])
        df['Address'] = df.Address.apply(lambda x: x.split(city)[0])
        df['Station'] = df.Station.apply(lambda x: x.split(' (')[0])
        df['Date'] = df.Date.apply(lambda x: x.split(' ago')[0])

        # Create datetime
        for i, date in enumerate(df.Date):
            if date[-1] == 'h':
                delta = int(date[:-1])
                date = datetime.now() - timedelta(hours=delta)
            elif date[-1] == 'm':
                delta = int(date[:-1])
                date = datetime.now() - timedelta(minutes=delta)
            # Reset older dates to now
            if date == '1d':
                date = now

            df.Date.iloc[i] = date

        df.reset_index(drop=True, inplace=True)

        if loc in temp_dfs.keys():
            temp_dfs[loc].append(df.to_dict(orient='list'))
        else:
            temp_dfs[loc] = [df.to_dict(orient='list')]

    with open('root/Gaspy/Data/master_data.json', 'w') as f:
        json.dump(temp_dfs, f, indent=4, sort_keys=True, default=str)


if __name__ == '__main__':
    # Set time
    now = datetime.now()
    locations = ['Oakville', 'Burlington', 'Hamilton', 'Ancaster', 'Milton', 'Mississauga']

    try:
        with open('root/Gaspy/Data/master_data.json', 'r') as f:
            data_dfs = json.load(f)
        print('Loaded master')
    except:
        print('No master found')
        data_dfs = dict()

    print('Running:', now)
    main(now, locations, data_dfs)
    print('Complete')
    # wait_time = random.choice(range(14000, 14800))
    # print('Sleeping:', str(timedelta(seconds=wait_time)))
    # time.sleep(wait_time)
