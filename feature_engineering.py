import pandas as pd
import configparser
import mapbox
from cassandra.cluster import Cluster

class HDBResaleFeatureEngineeringPipeline:
    def __init__(self):

        self.config = configparser.ConfigParser()
        self.config.read(r'app.conf')

        def init_connection():
            cluster = Cluster(["localhost"])
            return cluster.connect(keyspace="catalog")
        self.session = init_connection()

        def pandas_factory(colnames, rows):
            return pd.DataFrame(rows, columns=colnames)
        self.session.row_factory = pandas_factory
        self.session.default_fetch_size = None

        def fetch_data():
            return pd.DataFrame(self.session.execute("SELECT * FROM resale_data")._current_rows)
        self.dataset = fetch_data().astype(str)

        self.dataset['address'] = self.dataset['block'] + ' ' + self.dataset['street_name']
        print("Done!")

        print(len(self.dataset['address'].unique()))

        self.geocoder = mapbox.Geocoder(access_token=self.config.get('tokens', 'mapbox'))

        self.count = 0
        def get_lat_lon(address):
            self.count = self.count + 1
            response = self.geocoder.forward(address + ", SINGAPORE")
            lat = response.geojson()['features'][0]['geometry']['coordinates'][1]
            lon = response.geojson()['features'][0]['geometry']['coordinates'][0]
            print(self.count)
            return lat, lon
        
        unique_addresses = self.dataset['address'].drop_duplicates()

        lat_lon_df = unique_addresses.str.split(expand=True, n=1)

        lat_lon_df.to_csv("waddresses.csv")

        # lat_long_df = unique_addresses.apply(lambda x: pd.Series(get_lat_lon(x)))
        # lat_long_df.to_csv("wcoordinates.csv")

        # lat_long_df[['block', 'street_name']] = unique_addresses['address'].str.split(expand=True, n=1)

        # lat_long_df.to_csv("wcoordinates.csv")

if __name__ == "__main__":
    app = HDBResaleFeatureEngineeringPipeline()