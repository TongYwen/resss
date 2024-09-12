import streamlit as st
import googlemaps
import pandas as pd
import numpy as np
from streamlit_folium import st_folium
import folium

# Initialize the Google Maps client with your API key
API_KEY = 'AIzaSyDK7boLSVOjAK2lPx6NoOrBYPaXLpCAUoA'
gmaps = googlemaps.Client(key=API_KEY)

def get_autocomplete_suggestions(input_text):
    try:
        suggestions = gmaps.places_autocomplete(input_text)
        return [suggestion['description'] for suggestion in suggestions]
    except Exception as e:
        st.error(f"Error fetching autocomplete suggestions: {e}")
        return []

def get_lat_long(address):
    try:
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            lat = geocode_result[0]['geometry']['location']['lat']
            lng = geocode_result[0]['geometry']['location']['lng']
            return (lat, lng)
    except Exception as e:
        st.error(f"Error fetching latitude and longitude: {e}")
    return None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = np.sin(dphi/2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

def find_nearby_restaurants(lat, lng, df, max_distance_km=5):
    df['distance'] = df.apply(lambda row: haversine(lat, lng, row['latitude'], row['longitude']), axis=1)
    nearby_restaurants = df[df['distance'] <= max_distance_km]
    return nearby_restaurants

# Load your dataset with restaurant name, address, URL, latitude, and longitude
df_with_lat_lon = pd.read_excel('df_with_lat_lon.xlsx')

# Streamlit application interface
st.title("Nearby Restaurant Finder with Map")

# Step 1: Enter a location
user_input = st.text_input('Type a location')

if user_input:
    suggestions = get_autocomplete_suggestions(user_input)
    
    if suggestions:
        selected_address = suggestions[0] 
        
        if selected_address:
            coordinates = get_lat_long(selected_address)
            
            if coordinates:
                st.write(f"Selected Location: {selected_address}")
                st.write(f"Latitude: {coordinates[0]}, Longitude: {coordinates[1]}")
                
                # Step 3: Find nearby restaurants
                nearby_restaurants = find_nearby_restaurants(coordinates[0], coordinates[1], df_with_lat_lon)
                
                if not nearby_restaurants.empty:
                    st.write("Restaurants within 5 km:")
                    st.dataframe(nearby_restaurants[['name', 'latitude', 'longitude', 'distance', 'url']])
                    
                    # Displaying map using folium
                    m = folium.Map(location=[coordinates[0], coordinates[1]], zoom_start=13)
                    
                    # Add a marker for the selected location
                    folium.Marker([coordinates[0], coordinates[1]], tooltip='Selected Location').add_to(m)
                    
                    # Add markers for nearby restaurants
                    for idx, row in nearby_restaurants.iterrows():
                        folium.Marker(
                            [row['latitude'], row['longitude']], 
                            popup=row['name'],
                            tooltip=row['name']
                        ).add_to(m)
                    
                    # Display map using streamlit_folium
                    st_folium(m, width=700, height=500)
                else:
                    st.write("No restaurants found within 5 km.")
            else:
                st.error("Could not fetch coordinates for the selected location.")
    else:
        st.error("No suggestions found.")
