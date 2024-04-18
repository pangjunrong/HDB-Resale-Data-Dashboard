#!/bin/env python3
from cassandra.cluster import Cluster
from cassandra import ConsistencyLevel

class HDBResaleDataApp:
    def __init__(self):
        self.cluster = Cluster(contact_points=["172.18.0.2", "172.18.0.3", "172.18.0.4"])
        self.session = self.cluster.connect(keyspace="catalog")
        self.session.default_consistency_level = ConsistencyLevel.QUORUM

        self.insert_ps = self.session.prepare(
            query =
                "INSERT INTO resale_data \
                (transaction_id, month, town, flat_type, block, street_name, storey_range, floor_area_sqm, flat_model, lease_commence_date, remaining_lease, resale_price) \
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )

        self.delete_ps = self.session.prepare(
            query =
                "DELETE FROM resale_data WHERE month = ? and town = ? and flat_type = ? and storey_range = ? and transaction_id = ?"
        )


    def show_resale_data(self):
        print("Data that we have in the catalog".center(50, "="))
        result = self.session.execute(query="SELECT * FROM resale_data")
        for row in result:
            print(row.transaction_id, row.month, row.block, row.street_name, row.storey_range, row.flat_type)

    def add_transaction(self, transaction_id, month, town, flat_type, block, street_name, storey_range, floor_area_sqm, flat_model, lease_commence_date, remaining_lease, resale_price):
        month = month + '-01'
        print(f"\nAdding Transaction ID: {transaction_id}...")
        self.session.execute(query=self.insert_ps, parameters=[transaction_id, month, town, flat_type, block, street_name, storey_range, floor_area_sqm, flat_model, lease_commence_date, remaining_lease, resale_price])
        print("Added.\n")

    def delete_transaction(self, month, town, flat_type, storey_range, transaction_id):
        month = month + '-01'
        print(f"\nDeleting Transaction ID: {transaction_id}...")
        self.session.execute(query=self.delete_ps, parameters=[month, town, flat_type, storey_range, transaction_id])
        print("Deleted.\n")

    def stop(self):
        self.cluster.shutdown()

if __name__ == "__main__":
    app = HDBResaleDataApp()
    app.show_resale_data()
    app.add_transaction(transaction_id=17681, month='2017-01', town='ANG MO KIO', flat_type='2 ROOM', block='406', street_name='ANG MO KIO AVE 10', storey_range='10 TO 12', floor_area_sqm=44, flat_model='Improved', lease_commence_date=1979, remaining_lease='61 years 04 months', resale_price=232000)
    app.show_resale_data()
    app.delete_transaction(month='2017-01', town='ANG MO KIO', flat_type='2 ROOM', storey_range='10 TO 12', transaction_id=1)
    app.show_resale_data()
    app.stop()
