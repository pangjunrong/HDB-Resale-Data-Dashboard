import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import json
import re

import datetime
import configparser
from cassandra.cluster import Cluster

class HDBResaleDashboardApp:
    def __init__(self):
        with open('MasterPlan2019PlanningAreaBoundaryNoSea.geojson', 'r', encoding="utf-8") as f:
            self.geojson_data = json.load(f)

        def clean_geojson_description(geojson_data):
            # Loop through each feature in the GeoJSON data
            for feature in geojson_data['features']:
                # Extract the description field from the properties
                description = feature['properties']['Description']
                # Use regular expression to find the town name after "PLN_AREA_N"
                match = re.search(r'PLN_AREA_N<\/th> <td>(.*?)<\/td>', description)
                if match:
                    # Extract the matched town name and update the description
                    town_name = match.group(1)
                    feature['properties']['Description'] = town_name

                ### Cleaning of coordinates is not necessary
                # coordinates = feature["geometry"]["coordinates"]
                # for i in range(len(coordinates)):
                #     if isinstance(coordinates[i][0][0], list):  # Check if it's a list of coordinates
                #         for j in range(len(coordinates[i])):
                #             coordinates[i][j] = [coord[:2] for coord in coordinates[i][j]]
                #     else:  # It's a list of coordinates
                #         coordinates[i] = [coord[:2] for coord in coordinates[i]]
            return geojson_data
        
        self.geojson_data = clean_geojson_description(self.geojson_data)
        
        st.set_page_config(
            page_title="HDB Resale Flats Dashboard",
            page_icon="🏙️",
            layout="wide",
            initial_sidebar_state="expanded")

        self.config = configparser.ConfigParser()
        self.config.read(r'app.conf')

        @st.cache_resource
        def init_connection():
            cluster = Cluster(["localhost"])
            return cluster.connect(keyspace="catalog")
        self.session = init_connection()

        def pandas_factory(colnames, rows):
            return pd.DataFrame(rows, columns=colnames)
        self.session.row_factory = pandas_factory
        self.session.default_fetch_size = None

        @st.cache_data
        def fetch_data():
            return pd.DataFrame(self.session.execute("SELECT * FROM resale_data")._current_rows)
        self.dataset = fetch_data().astype(str)

        @st.cache_resource
        def fetch_towns():
            return pd.DataFrame(self.session.execute("SELECT * FROM towns")._current_rows)
        self.towns = fetch_towns().astype(str)

        @st.cache_resource
        def fetch_planning_areas():
            return pd.DataFrame(self.session.execute("SELECT * FROM planning_areas")._current_rows)
        self.planning_areas = fetch_planning_areas().astype(str)

        with st.sidebar:
            st.title('🏙️ HDB Resale Flats Dashboard')
            
            # year_list = list(self.dataset.year.unique())[::-1]
            
            # selected_year = st.selectbox('Select a year', year_list, index=len(year_list)-1)
            # df_selected_year = df_reshaped[df_reshaped.year == selected_year]
            # df_selected_year_sorted = df_selected_year.sort_values(by="population", ascending=False)

            self.selected_period = st.select_slider(
                'How recent do you want to visualize?',
                options=['Past 1 Month', 'Past 3 Months', 'Past 1 Year', 'Past 3 Years', 'From 2017'])

            @st.cache_resource
            def fetch_flat_types():
                df_types = pd.DataFrame(self.session.execute("SELECT flat_type FROM resale_data")._current_rows)
                df_types = df_types['flat_type'].unique()
                return list(df_types)
            self.flat_types = st.multiselect(
                'What flat types are you interested in?',
                fetch_flat_types(),
                fetch_flat_types())

            st.write('You selected:', self.flat_types)

        def date_filter(selected_period, reference_date=datetime.datetime.today()):
            match selected_period:
                case 'Past 1 Month':
                    time_delta = pd.offsets.DateOffset(months=1)
                case 'Past 3 Months':
                    time_delta = pd.offsets.DateOffset(months=3)
                case 'Past 1 Year':
                    time_delta = pd.offsets.DateOffset(years=1)
                case 'Past 3 Years':
                    time_delta = pd.offsets.DateOffset(years=3)
                case 'From 2017':
                    time_delta = pd.offsets.DateOffset(years=99)
            return reference_date - time_delta

        @st.cache_data
        def filter_data(flat_types, selected_period):
                df_filtered = self.dataset[pd.to_datetime(self.dataset['month']) > date_filter(selected_period)]
                df_filtered = df_filtered[df_filtered['flat_type'].isin(flat_types)]
                return df_filtered

        self.df_period = filter_data(self.flat_types, self.selected_period)
        self.df_transactions = self.df_period.groupby('town').agg({
                    'transaction_id': 'count'
                }).reset_index().rename(columns={'transaction_id': 'units_sold'})

        col = st.columns((1.5, 4.5, 2), gap='medium')

        def transaction_delta(self):
            df_current = self.df_transactions
            df_previous_period = self.dataset[(pd.to_datetime(self.dataset['month']) <= date_filter(self.selected_period)) & (pd.to_datetime(self.dataset['month']) > date_filter(self.selected_period, pd.to_datetime(self.df_period['month']).min()))].groupby('town').agg({
                    'transaction_id': 'count'
                }).reset_index().rename(columns={'transaction_id': 'units_sold'})
            df_current['units_sold_delta'] = df_current.units_sold.sub(df_previous_period.units_sold, fill_value=0)
            return df_current.sort_values(by="units_sold_delta", ascending=False)

        with col[0]:
            st.markdown('#### Biggest Gains/Losses')

            if self.selected_period != "From 2017":
                df_delta_metric = transaction_delta(self)
                first_town_name = df_delta_metric.town.iloc[0]
                first_units_sold = int(df_delta_metric.units_sold.iloc[0])
                first_units_sold_delta = int(df_delta_metric.units_sold_delta.iloc[0])
            else:
                first_town_name = '-'
                first_units_sold = '-'
                first_units_sold_delta = ''
            st.metric(label=first_town_name, value=first_units_sold, delta=first_units_sold_delta)

            if self.selected_period != "From 2017":
                df_delta_metric = transaction_delta(self)
                last_town_name = df_delta_metric.town.iloc[-1]
                last_units_sold = int(df_delta_metric.units_sold.iloc[-1])
                last_units_sold_delta = int(df_delta_metric.units_sold_delta.iloc[-1])
            else:
                last_town_name = '-'
                last_units_sold = '-'
                last_units_sold_delta = ''
            st.metric(label=last_town_name, value=last_units_sold, delta=last_units_sold_delta)



        if len(self.df_period.index) == 0:
            with col[1]:
                st.write("Please reselect your timeframe!")
        else:
            def make_choropleth(self, df_transactions, geojson):
                st.markdown('#### Units Sold')
                show_all = st.checkbox('Show All Planning Areas?')
                if show_all:
                    df_transactions = pd.merge(df_transactions, self.planning_areas, left_on='town', right_on='name', how='right')
                else:
                    df_transactions = pd.merge(df_transactions, self.towns, left_on='town', right_on='name', how='right')
                df_transactions['units_sold'] = df_transactions['units_sold'].fillna(0)
                choropleth = px.choropleth_mapbox(df_transactions, locations='name', color='units_sold',
                                color_continuous_scale="blues",
                                range_color=(0, max(df_transactions['units_sold'])),
                                geojson=geojson,
                                featureidkey='properties.Description',
                                labels={'name': 'Name', 'units_sold':'Unit Sold'},
                                mapbox_style="dark",
                                zoom=10,
                                center={"lat": 1.3521, "lon": 103.8198}
                                )
                choropleth.update_layout(
                    mapbox_accesstoken=self.config.get('tokens', 'mapbox'),
                    template='plotly_dark',
                    plot_bgcolor='rgba(0, 0, 0, 0)',
                    paper_bgcolor='rgba(0, 0, 0, 0)',
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=350,
                )
                choropleth.update_geos(
                    resolution=50,
                    fitbounds='locations',
                    # visible=False
                )
                return choropleth
            
            with col[1]:
                choropleth = make_choropleth(self, self.df_transactions, self.geojson_data)
                st.plotly_chart(choropleth, use_container_width=True)

                st.markdown('#### Most Recent Transactions')
                self.df_period['month'] = pd.to_datetime(self.df_period['month'])
                self.df_period.month = self.df_period.month.dt.strftime('%B %Y')
                st.dataframe(self.df_period.sort_values(by='transaction_id', ascending=False)[:100], hide_index=True)

            with col[2]:
                st.markdown('#### Highest No. of Transactions')

                st.dataframe(self.df_transactions.sort_values(by='units_sold', ascending=False),
                            column_order=("town", "units_sold"),
                            hide_index=True,
                            width=None,
                            column_config={
                                "town": st.column_config.TextColumn(
                                    "Towns",
                                ),
                                "units_sold": st.column_config.ProgressColumn(
                                    "Units Sold",
                                    format="%f",
                                    min_value=0,
                                    max_value=max(self.df_transactions.units_sold),
                                )},
                            use_container_width=True
                            )
                
                with st.expander('About', expanded=True):
                    st.write('''
                        - Data: [Housing & Dev. Board](<https://beta.data.gov.sg/collections/189/datasets/d_ebc5ab87086db484f88045b47411ebc5/view>).
                        - :orange[**Gains/Losses**]: states with high inbound/ outbound migration for selected year
                        - :orange[**States Migration**]: percentage of states with annual inbound/ outbound migration > 50,000
                        ''')

if __name__ == "__main__":
    app = HDBResaleDashboardApp()