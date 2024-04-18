import configparser
from pyspark.sql import SparkSession

class HDBResaleDataBulkUpload():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(r'upload.conf')

        self.spark = SparkSession.builder \
            .appName("HDBResaleDataBulkUpload") \
            .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.2.0") \
            .config("spark.cassandra.connection.host", "172.20.0.2") \
            .config("spark.cassandra.connection.port", "9042") \
            .getOrCreate()
        
    def initiate_upload(self):
        df = self.spark.read.csv(self.config.get('file', 'filename'), header=True, inferSchema=True)
        self.load_data(df, self.config.get('scylladb', 'keyspace'), self.config.get('scylladb', 'table_name'))
        self.spark.stop()

    def load_data(self, df, keyspace, table):
        df.write \
            .format("org.apache.spark.sql.cassandra") \
            .options(table=table, keyspace=keyspace) \
            .mode("append") \
            .save()

if __name__ == '__main__':
    app = HDBResaleDataBulkUpload()
    app.initiate_upload()
