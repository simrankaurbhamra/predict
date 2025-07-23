import streamlit as st
import pandas as pd
import plotly.express as px
import json

with open("dist.geojson", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

census_df = pd.read_csv("census.csv")
census_df.columns = census_df.columns.str.strip()

# funtion to align map
def get_center(feature):
    coords = feature["geometry"]["coordinates"]
    if feature["geometry"]["type"] == "Polygon":
        flat = [pt for polygon in coords for pt in polygon]
    elif feature["geometry"]["type"] == "MultiPolygon":
        flat = [pt for multi in coords for polygon in multi for pt in polygon]
    else:
        return {"lat": 22.5, "lon": 80}
    lats = [pt[1] for pt in flat]
    lons = [pt[0] for pt in flat]
    return {"lat": sum(lats) / len(lats), "lon": sum(lons) / len(lons)}
#style
st.title("📍 Indian District Map")

states = sorted({f["properties"]["st_nm"] for f in geojson_data["features"]})
selected_state = None
selected_district = None

col1, col2 = st.columns(2)

with col1:
    selected_state = st.selectbox("Select State", states)

with col2:
    state_features = [f for f in geojson_data["features"] if f["properties"]["st_nm"] == selected_state]
    districts = sorted({f["properties"]["district"] for f in state_features})
    selected_district = st.selectbox("Select District", districts)

# Prepare data
state_geojson = {"type": "FeatureCollection", "features": state_features}
state_districts = [f["properties"]["district"] for f in state_features]
df_state = pd.DataFrame({"district": state_districts, "metric": [1] * len(state_districts)})

# Merge population data
merged_state = df_state.merge(
    census_df.rename(columns={
        "District name": "district",
        "State name": "state"
    })[["district", "state", "Male", "Female"]],
    how="left",
    left_on="district",
    right_on="district"
)
merged_state.rename(columns={"Male": "Male Population", "Female": "Female Population"}, inplace=True)

col1, col2 = st.columns(2)

# state map
with col1:
    st.subheader(f"🗺️ State Map: {selected_state}")
    center = get_center(state_features[0])
    fig_state = px.choropleth_mapbox(
        merged_state,
        geojson=state_geojson,
        locations="district",
        featureidkey="properties.district",
        color="metric",
        hover_data={"Male Population": True, "Female Population": True, "metric": False},
        color_continuous_scale=["#3498DB", "#3498DB"],
        range_color=(1, 1),
        mapbox_style="carto-positron",
        center=center,
        zoom=5,
        opacity=0.6,
        height=500
    )
    fig_state.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig_state.update_coloraxes(showscale=False)
    st.plotly_chart(fig_state)
#distrcit map
with col2:
    st.subheader(f"📌 District Map: {selected_district}")
    district_feature = [f for f in state_features if f["properties"]["district"] == selected_district]
    if district_feature:
        district_geojson = {"type": "FeatureCollection", "features": district_feature}
        center_district = get_center(district_feature[0])

        pop_row = census_df[
            (census_df["State name"].str.lower() == selected_state.lower()) &
            (census_df["District name"].str.lower() == selected_district.lower())
        ]

        male = int(pop_row.iloc[0]["Male"]) if not pop_row.empty else None
        female = int(pop_row.iloc[0]["Female"]) if not pop_row.empty else None

        df_district = pd.DataFrame({
            "district": [selected_district],
            "value": [1],
            "Male Population": [male],
            "Female Population": [female]
        })

        fig_district = px.choropleth_mapbox(
            df_district,
            geojson=district_geojson,
            locations="district",
            featureidkey="properties.district",
            color="value",
            hover_data={"Male Population": True, "Female Population": True, "value": False},
            color_continuous_scale=["#F39C12", "#F39C12"],
            range_color=(1, 1),
            mapbox_style="carto-positron",
            center=center_district,
            zoom=7,
            opacity=0.8,
            height=400
        )
        fig_district.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fig_district.update_coloraxes(showscale=False)
        st.plotly_chart(fig_district)
    else:
        st.warning("District not found in GeoJSON.")

