import configparser
import requests

from cassandra.cluster import Cluster

class HDBResaleDataSourcePipeline:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(r'pipeline.conf')

        self.cluster = Cluster(self.config.get('scylladb', 'contact_points').split(", "))
        self.session = self.cluster.connect(keyspace="catalog")

        # This logic gets the latest transaction ID from DB and finds the hundredth floor, which is used in the pagination offset.
        self.latest_id = list(self.session.execute("SELECT MAX(transaction_id) as transaction_id FROM resale_data"))[0].transaction_id
        if self.latest_id is None:
            self.latest_id = 0
        self.starting_offset = (self.latest_id // 100) * 100

        self.insert_ps = self.session.prepare(
            query =
                "INSERT INTO resale_data \
                (transaction_id, month, town, flat_type, block, street_name, storey_range, floor_area_sqm, flat_model, lease_commence_date, remaining_lease, resale_price) \
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )


    def extract(self, offset):
        # This fetches the correct pagination and extracts the new transactions.
        raw_data = requests.get(self.config.get('api', 'api_url')+ '&offset=' + str(offset)).json()
        if offset == self.starting_offset:
            filtered_data = list(filter(lambda item: item['_id'] > self.latest_id, raw_data['result']['records']))
        else:
            filtered_data = list(raw_data['result']['records'])

        print(raw_data['result']['_links']['next'])
        print(raw_data['result']['records'])
        print(offset)
        print(type(raw_data['result']['records']))
        if len(raw_data['result']['records']) > 0:
            offset += 100
            filtered_data.extend(self.extract(offset))

        return filtered_data

    def transform(json_data):
        
        return

    def load(self, data_to_load):
        for row_entry in data_to_load:
            transaction_id = int(row_entry['_id'])
            month = row_entry['month'] + '-01'
            town = row_entry['town']
            flat_type = row_entry['flat_type']
            block = row_entry['block']
            street_name = row_entry['street_name']
            storey_range = row_entry['storey_range']
            floor_area_sqm = float(row_entry['floor_area_sqm'])
            flat_model = row_entry['flat_model']
            lease_commence_date = int(row_entry['lease_commence_date'])
            remaining_lease = row_entry['remaining_lease']
            resale_price = float(row_entry['resale_price'])
            self.session.execute(query=self.insert_ps, parameters=[transaction_id, month, town, flat_type, block, street_name, storey_range, floor_area_sqm, flat_model, lease_commence_date, remaining_lease, resale_price])
        return True

if __name__ == "__main__":
    app = HDBResaleDataSourcePipeline()
    # raw_data = app.extract()
    # transformed_data = app.transform(raw_data)
    # status_code = app.load(transformed_data)
    # app.stop()
    json_data = app.extract(app.starting_offset)
    print(json_data)
    print(app.load(json_data))