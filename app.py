import customtkinter as ctk
import requests
from PIL import Image, ImageTk, ImageDraw
from io import BytesIO
from datetime import datetime, timedelta
import os
import pywinstyles
from nltk.tokenize import sent_tokenize
import time
from winotify import Notification, audio

# Configure appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

weather_data = None
update_interval = 60000  # Default to 60 seconds
is_updating = False
unit_preference = 'metric'
default_summary = 'Weather summary for Delhi: The current temperature is 35.05℃ and it feels like 33.98C. Humidity is at 26%, with haze. The wind speed is 3.09 m/s. Rain volume in the last hour is 0 mm. The sky is 0% cloudy. The sun is set to rise by 06:24 AM and set by 05:47 PM.'


# OpenWeather API setup
API_KEY = 'e753f934016bc327f3515bcf5df23b14'
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'
AIR_QUALITY_URL = 'http://api.openweathermap.org/data/2.5/air_pollution'

# Function to fetch weather data
def fetch_weather(city, unit):
    try:
        params = {
            'q': city,
            'appid': API_KEY,
            'units': unit
        }
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        if data['cod'] == 200:
            return data
        else:
            return None
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

# Function to fetch air quality data
def fetch_air_quality(lat, lon):
    try:
        params = {
            'lat': lat,
            'lon': lon,
            'appid': API_KEY
        }
        response = requests.get(AIR_QUALITY_URL, params=params)
        data = response.json()
        if response.status_code == 200:
            return data['list'][0]['main']['aqi']  # Returns Air Quality Index (AQI)
        else:
            return None
    except Exception as e:
        print(f"Error fetching air quality data: {e}")
        return None

def format_unix_time(unix_time, timezone_offset):
    # Adjust time to the city's timezone using the timezone_offset (seconds)
    adjusted_time = datetime.utcfromtimestamp(unix_time) + timedelta(seconds=timezone_offset)
    return adjusted_time.strftime("%I:%M %p")

def get_local_date(timezone_offset):
    # Adjust the current UTC time to the city's timezone using the timezone_offset (seconds)
    local_time = datetime.utcnow() + timedelta(seconds=timezone_offset)
    return local_time.strftime("%A, %B %d, %Y")

# Function to update the temp_frame with weather data
def update_weather_display(data, unit_system='metric'):
    # Extract weather details
    temp = data['main']['temp']
    temp_min = data['main']['temp_min']
    temp_max = data['main']['temp_max']
    description = data['weather'][0]['description']
    icon_code = data['weather'][0]['icon']
    city = data['name']
    country = data['sys']['country']
    wind_speed = data['wind']['speed']  # Wind speed in m/s
    humidity = data['main']['humidity']  # Humidity in percentage
    visibility = data['visibility'] / 1000  # Visibility in km
    sunrise = format_unix_time(data['sys']['sunrise'], data['timezone'])  # Sunrise time
    sunset = format_unix_time(data['sys']['sunset'], data['timezone'])  # Sunset time
    local_date = get_local_date(data['timezone'])  # Get the date in the city's timezone
    
    # Fetch air quality data based on the coordinates
    lat = data['coord']['lat']
    lon = data['coord']['lon']
    air_quality = fetch_air_quality(lat, lon)
    
    # Round the temperature for display
    temp = round(temp, 1)

    # Update the labels with the fetched data
  
    
    # Download the weather icon
    icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
    icon_response = requests.get(icon_url)
    icon_image = Image.open(BytesIO(icon_response.content))
    icon_tk = ImageTk.PhotoImage(icon_image)
    
    
    if unit_system == 'metric':
        unit = 'C'
    if unit_system == 'imperial':
        unit = 'F'
    if unit_system == 'standard':
        unit = 'K'
        
    # Update the labels with the fetched data
    temp_label.configure(text=f"{temp}°{unit}")
    description_label.configure(text=description.capitalize())
    icon_label.configure(image=icon_tk)
    icon_label.image = icon_tk  # To keep a reference to avoid garbage collection
    min_max_label.configure(text=f"Min: {temp_min}°C, Max: {temp_max}°C")
    location_label.configure(text=f"{city}, {country}")
    
    wind_speed_value_label.configure(text=f"{wind_speed} m/s")
    humidity_value_label.configure(text=f"{humidity}%")
    visibility_value_label.configure(text=f"{visibility:.1f} km")
    
    # Update Air Quality based on AQI
    air_quality_description = {
        1: "Good",
        2: "Fair",
        3: "Moderate",
        4: "Poor",
        5: "Very Poor"
    }
    air_quality_value_label.configure(text=air_quality_description.get(air_quality, "Unknown"))
    
    # Update sunrise and sunset times
    sunrise_value_label.configure(text=sunrise)
    sunset_value_label.configure(text=sunset)
    
    # Update the current date based on location
    day_date.configure(text=local_date)
    check_temperature_alert(temp)
    

# Search button function
def search_weather():
    global weather_data
    city = entry_city.get()
    if city:
        weather_data = fetch_weather(city, unit_preference)
        if weather_data:
            update_weather_display(weather_data, unit_preference)
            get_summary(weather_data)
            start_weather_updates()
        else:
            print("City not found or API request failed")

def get_weather_forecast():
    url = f'http://api.openweathermap.org/data/2.5/forecast?q={search_weather()}&appid={API_KEY}&units=metric'
    response = requests.get(url)
    forecast_data = response.json()
    
    # Get the next 10 hourly forecasts
    next_10_hours = forecast_data['list'][:10]
    return next_10_hours

# Function to download weather icon from OpenWeatherMap and convert to CTkImage
def get_weather_icon(icon_code):   
    icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
    icon_response = requests.get(icon_url)
    icon_image = Image.open(BytesIO(icon_response.content))
    icon_tk = ImageTk.PhotoImage(icon_image)
    
    return icon_tk

# Displaying the 10-hour forecast in 2 rows inside graph_frame
def display_weather_forecast(forecast_data):
    for widget in graph_frame.winfo_children():
        widget.destroy()  # Clear previous content
    
    # First 5-hour forecast (Row 1)
    for i in range(5):
        time_label = ctk.CTkLabel(graph_frame, text=f"{forecast_data[i]['dt_txt'][11:16]}", compound='center')
        time_label.grid(row=1, column=i, padx=(30,30), pady=(10,40))
        
        
        icon_image = get_weather_icon(forecast_data[i]['weather'][0]['icon'])
        icon_label = ctk.CTkLabel(graph_frame, image=icon_image, text=f"")
        icon_label.place(relx=0.025+(i*0.2), rely=0.25, anchor="w") 
        pywinstyles.set_opacity(icon_label, value=0.5)
                                
        temp_label = ctk.CTkLabel(graph_frame, text=f"{forecast_data[i]['main']['temp']}°C")
        temp_label.grid(row=3, column=i, padx=(30,30), pady=5)

    # Next 5-hour forecast (Row 2)
    for j in range(5, 10):
        time_label = ctk.CTkLabel(graph_frame, text=f"{forecast_data[j]['dt_txt'][11:16]}", compound='center')
        time_label.grid(row=4, column=j-5, padx=(30,30), pady=(10,40))
        
        icon_image = get_weather_icon(forecast_data[j]['weather'][0]['icon'])
        icon_label = ctk.CTkLabel(graph_frame, image=icon_image, text="")
        icon_label.place(relx=0.025+((j-5)*0.2), rely=0.72, anchor="w") 
        pywinstyles.set_opacity(icon_label, value=0.5)
        
        temp_label = ctk.CTkLabel(graph_frame, text=f"{forecast_data[j]['main']['temp']}°C")
        temp_label.grid(row=6, column=j-5, padx=(30,30), pady=5)

def get_summary(data):
    
    city = data['name']
    temperature = data['main']['temp']
    feels_like = data['main']['feels_like']
    weather_description = data['weather'][0]['description']
    rain_volume = data.get('rain', {}).get('1h', 0)  # Default to 0 if no rain data
    cloudiness = data['clouds']['all']
    wind_speed = data['wind']['speed']  # Wind speed in m/s
    humidity = data['main']['humidity']  # Humidity in percentage
    visibility = data['visibility'] / 1000  # Visibility in km
    sunrise = format_unix_time(data['sys']['sunrise'], data['timezone'])  # Sunrise time
    sunset = format_unix_time(data['sys']['sunset'], data['timezone'])  # Sunset time

    # Step 2: Format the data into a structured input for the model
    summary_input = (
        f"Weather of {city}: "
        f"The current temperature is {temperature}°C and it feels like {feels_like}°C. "
        f"Humidity is at {humidity}%, with {weather_description}. "
        f"The wind speed is {wind_speed} m/s. "
        f"Rain volume in the last hour is {rain_volume} mm. "
        f"The sky is {cloudiness}% cloudy."
        f"The sun is set to rise by {sunrise} and set by {sunset}."
    )

    sentences = sent_tokenize(summary_input)
    
    # Select the first 'num_sentences' sentences as a summary
    summary = ' '.join(sentences[:10])
    

    # Display the generated summary in the summary frame
    summary_value_label.configure(text=summary)

            
# Main app window
root = ctk.CTk()
root.title("WeatherApp")
root.geometry("1000x610")





# Header frame (for search bar and buttons)
header_frame = ctk.CTkFrame(master=root, fg_color="transparent")
header_frame.pack(pady=10, padx=10, fill="x")

# Configure grid columns for header frame
header_frame.columnconfigure(0, weight=1)  # Make the first column take up available space
header_frame.columnconfigure(1, weight=0)  # For the title
header_frame.columnconfigure(2, weight=0)  # For input
header_frame.columnconfigure(3, weight=0)  # For search button
header_frame.columnconfigure(4, weight=0)  # For location button

# "Weather" label
label_title = ctk.CTkLabel(header_frame, text="Weather", font=("Calibri", 24))
label_title.grid(row=0, column=0, padx=(10, 10), sticky="w")  # Align left

# City input field
entry_city = ctk.CTkEntry(header_frame, placeholder_text="Enter City name / Zip code", width=250, corner_radius=20, font=("Calibri", 16),height=35)
entry_city.grid(row=0, column=1, padx=10, sticky="e")

# Search button
button_search = ctk.CTkButton(header_frame, text="Search", width=100, fg_color="white", text_color="black", corner_radius=20, font=("Calibri", 20), command=search_weather)
button_search.grid(row=0, column=2, padx=5, sticky="e")

# Current Location button
button_location = ctk.CTkButton(header_frame, text="Current Location", width=150, fg_color="#F76B1C", corner_radius=20, font=("Calibri", 20))
button_location.grid(row=0, column=3, padx=10, sticky="e")





# Main content frame for weather data
content_frame = ctk.CTkFrame(master=root, fg_color="transparent")
content_frame.pack(pady=0, padx=10, fill="both", expand=True)

# Configure grid layout for the weather content
content_frame.columnconfigure(0, weight=1)  # Temperature
content_frame.columnconfigure(1, weight=1)  # Air Quality, Wind Speed
content_frame.columnconfigure(2, weight=1)  # Humidity, Visibility
content_frame.columnconfigure(3, weight=1)  # Sunrise, Sunset

# Temperature frame (left side) - now inside content_frame
temp_frame = ctk.CTkFrame(master=content_frame, width=400, height=200, corner_radius=12)
temp_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")

# Configure grid layout inside temp_frame
temp_frame.columnconfigure(0, weight=1)  # Left content (temp, description, etc.)

# Temperature label (left side)
temp_label = ctk.CTkLabel(temp_frame, text="Temp °C", font=("Arial", 28))
temp_label.grid(row=0, column=0, padx=(20, 0), pady=(15,0), sticky="w")

# Weather description (aligned left, now directly below temp)
description_label = ctk.CTkLabel(temp_frame, text="Weather Description", font=("Arial", 16))
description_label.grid(row=1, column=0, padx=20, pady=0, sticky="w")  # Directly below temp

# Min-Max temperature (aligned left)
min_max_label = ctk.CTkLabel(temp_frame, text="Min - Max", font=("Arial", 16))
min_max_label.grid(row=2, column=0, padx=20, pady=0, sticky="w")

# Get current date and day
current_date = datetime.now().strftime("%A, %B %d, %Y")  # Example format: "Thursday, October 18, 2024"
day_date = ctk.CTkLabel(temp_frame, text=current_date, font=("Arial", 16))
day_date.grid(row=3, column=0, padx=20, pady=0, sticky="w") 

# Location (aligned left)
location_label = ctk.CTkLabel(temp_frame, text="Location", font=("Arial", 18))
location_label.grid(row=4, column=0, padx=20, pady=(0,15), sticky="w")

# Weather icon (absolute positioning)
icon_code = '01d'
icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
icon_response = requests.get(icon_url)
icon_image = Image.open(BytesIO(icon_response.content))
icon_tk = ImageTk.PhotoImage(icon_image)

icon_label = ctk.CTkLabel(temp_frame, image=icon_tk, text="")
icon_label.image = icon_tk  
icon_label.place(relx=0.65, rely=0.02, anchor="nw") 





# Air Quality frame (middle top)
air_quality_frame = ctk.CTkFrame(master=content_frame, width=200, height=75, corner_radius=12)
air_quality_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Load the air quality icon
air_quality_icon_path = "icons/air_quality_icon.png"  # Update with the correct path
air_quality_icon_image = Image.open(air_quality_icon_path)  # Load the image
air_quality_icon_image = air_quality_icon_image.resize((64, 39))
air_quality_icon_tk = ImageTk.PhotoImage(air_quality_icon_image)  # Convert to PhotoImage

# Create the icon label
air_quality_icon_label = ctk.CTkLabel(air_quality_frame, image=air_quality_icon_tk, text="")
air_quality_icon_label.image = air_quality_icon_tk  # Keep a reference to avoid garbage collection
air_quality_icon_label.place(relx=0.08, rely=0.65, anchor="w")  # Place the icon

# Create the air quality label
air_quality_label = ctk.CTkLabel(air_quality_frame, text="Air Quality", font=("Calibri", 14), text_color='grey')
air_quality_label.place(relx=0.08, rely=0.02, anchor="nw")  # Center the label in the frame

air_quality_value_label = ctk.CTkLabel(air_quality_frame, text="Clean", font=("Calibri", 24), text_color='white')
air_quality_value_label.place(relx=0.5, rely=0.4, anchor="nw")



# Wind Speed frame (middle bottom)
wind_speed_frame = ctk.CTkFrame(master=content_frame, width=200, height=75, corner_radius=12)
wind_speed_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

wind_speed_icon_path = "icons/wind_speed_icon.png"  # Update with the correct path
wind_speed_icon_image = Image.open(wind_speed_icon_path)  # Load the image
wind_speed_icon_image = wind_speed_icon_image.resize((40, 40))
wind_speed_icon_tk = ImageTk.PhotoImage(wind_speed_icon_image)  # Convert to PhotoImage

# Create the icon label
wind_speed_icon_label = ctk.CTkLabel(wind_speed_frame, image=wind_speed_icon_tk, text="")
wind_speed_icon_label.image = wind_speed_icon_tk  # Keep a reference to avoid garbage collection
wind_speed_icon_label.place(relx=0.08, rely=0.6, anchor="w") 

wind_speed_label = ctk.CTkLabel(wind_speed_frame, text="Wind Speed", font=("Calibri", 14), text_color='grey')
wind_speed_label.place(relx=0.08, rely=0.01, anchor="nw")

wind_speed_value_label = ctk.CTkLabel(wind_speed_frame, text="0 m/s", font=("Calibri", 24), text_color='white')
wind_speed_value_label.place(relx=0.5, rely=0.4, anchor="nw")



# Humidity frame (left bottom)
humidity_frame = ctk.CTkFrame(master=content_frame, width=200, height=75, corner_radius=12)
humidity_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

humidity_icon_path = "icons/humidity_icon.png"  # Update with the correct path
humidity_icon_image = Image.open(humidity_icon_path)  # Load the image
humidity_icon_image = humidity_icon_image.resize((50, 50))
humidity_icon_tk = ImageTk.PhotoImage(humidity_icon_image)  # Convert to PhotoImage

# Create the icon label
humidity_icon_label = ctk.CTkLabel(humidity_frame, image=humidity_icon_tk, text="")
humidity_icon_label.image = humidity_icon_tk  # Keep a reference to avoid garbage collection
humidity_icon_label.place(relx=0.08, rely=0.65, anchor="w") 

humidity_label = ctk.CTkLabel(humidity_frame, text="Humidity", font=("Calibri", 14), text_color='grey')
humidity_label.place(relx=0.08, rely=0.02, anchor="nw")
humidity_value_label = ctk.CTkLabel(humidity_frame, text="0 %", font=("Calibri", 24), text_color='white')
humidity_value_label.place(relx=0.6, rely=0.4, anchor="nw")




# Visibility frame (middle bottom)
visibility_frame = ctk.CTkFrame(master=content_frame, width=150, height=75, corner_radius=12)
visibility_frame.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")

visiblity_icon_path = "icons/visibility_icon.png"  # Update with the correct path
visiblity_icon_image = Image.open(visiblity_icon_path)  # Load the image
visiblity_icon_image = visiblity_icon_image.resize((64, 64))
visiblity_icon_tk = ImageTk.PhotoImage(visiblity_icon_image)  # Convert to PhotoImage

# Create the icon label
visiblity_icon_label = ctk.CTkLabel(visibility_frame, image=visiblity_icon_tk, text="")
visiblity_icon_label.image = visiblity_icon_tk  # Keep a reference to avoid garbage collection
visiblity_icon_label.place(relx=0.08, rely=0.65, anchor="w") 

visibility_label = ctk.CTkLabel(visibility_frame, text="Visibility", font=("Calibri", 14), text_color='grey')
visibility_label.place(relx=0.08, rely=0.02, anchor="nw")
visibility_value_label = ctk.CTkLabel(visibility_frame, text="0 km", font=("Calibri", 24), text_color='white')
visibility_value_label.place(relx=0.6, rely=0.4, anchor="nw")




# Sunrise and Sunset frame (right side)
sun_frame = ctk.CTkFrame(master=content_frame, width=200, height=150, corner_radius=12)
sun_frame.grid(row=0, column=3, rowspan=2, padx=10, pady=10, sticky="nsew")

sunrise_icon_path = "icons/sunrise_icon.png"  # Update with the correct path
sunrise_icon_image = Image.open(sunrise_icon_path)  # Load the image
sunrise_icon_image = sunrise_icon_image.resize((64, 64))
sunrise_icon_tk = ImageTk.PhotoImage(sunrise_icon_image)  # Convert to PhotoImage

# Create the icon label
sunrise_icon_label = ctk.CTkLabel(sun_frame, image=sunrise_icon_tk, text="")
sunrise_icon_label.image = sunrise_icon_tk  # Keep a reference to avoid garbage collection
sunrise_icon_label.place(relx=0.06, rely=0.35, anchor="w")

sunset_icon_path = "icons/sunset_icon.png"  # Update with the correct path
sunset_icon_image = Image.open(sunset_icon_path)  # Load the image
sunset_icon_image = sunset_icon_image.resize((64, 64))
sunset_icon_tk = ImageTk.PhotoImage(sunset_icon_image)  # Convert to PhotoImage

# Create the icon label
sunset_icon_label = ctk.CTkLabel(sun_frame, image=sunset_icon_tk, text="")
sunset_icon_label.image = sunset_icon_tk  # Keep a reference to avoid garbage collection
sunset_icon_label.place(relx=0.06, rely=0.75, anchor="w")

sun_label = ctk.CTkLabel(sun_frame, text="Sunrise & Sunset", font=("Calibri", 14), text_color='grey')
sun_label.place(relx=0.06, rely=0.02, anchor="nw")

sunrise_value_label = ctk.CTkLabel(sun_frame, text="00:00 AM", font=("Calibri", 24), text_color='white')
sunrise_value_label.place(relx=0.4, rely=0.25, anchor="nw")

sunset_value_label = ctk.CTkLabel(sun_frame, text="00:00 PM", font=("Calibri", 24), text_color='white')
sunset_value_label.place(relx=0.4, rely=0.65, anchor="nw")






center_frame = ctk.CTkFrame(master=root, fg_color="transparent")
center_frame.pack(pady=0, padx=10, fill="x", expand=True,side='top')

center_frame.columnconfigure(0, weight=1)
center_frame.columnconfigure(1, weight=15)
center_frame.columnconfigure(2, weight=1)

# Variables to store slider values
lower_value = ctk.IntVar(value=20)
upper_value = ctk.IntVar(value=80)

# Callback functions to keep the sliders constrained
def update_lower(value):
    value = int(float(value))
    if value >= upper_value.get():
        lower_slider.set(upper_value.get() - 1)  # Ensure lower handle can't exceed upper handle
    else:
        lower_value.set(value)
    lower_value_label.configure(text=str(lower_value.get()))  # Update label with the current value


def update_upper(value):
    value = int(float(value))
    if value <= lower_value.get():
        upper_slider.set(lower_value.get() + 1)  # Ensure upper handle can't go below lower handle
    else:
        upper_value.set(value)
    upper_value_label.configure(text=str(upper_value.get()))  # Update label with the current value


# Slider frame (vertical)
slider_frame = ctk.CTkFrame(master=center_frame, corner_radius=12)
slider_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Lower value slider setup
lower_frame = ctk.CTkFrame(master=slider_frame)
lower_frame.pack(side='left', padx=(10, 10))  # Add padding to the right for spacing

lower_value_label = ctk.CTkLabel(master=lower_frame, text=str(lower_value.get()), font=("Arial", 12))
lower_value_label.pack(pady=(5, 0))  # Add padding below the label

lower_slider = ctk.CTkSlider(master=lower_frame, from_=-20, to=50, command=update_lower, variable=lower_value, orientation='vertical', corner_radius=12)
lower_slider.pack()  # Pack to fill the frame

lower_slider.set(20)  # Default starting position

# Upper value slider setup
upper_frame = ctk.CTkFrame(master=slider_frame)
upper_frame.pack(side='left', padx=(10, 0))  # Add padding to the left for spacing

upper_value_label = ctk.CTkLabel(master=upper_frame, text=str(upper_value.get()), font=("Arial", 12))
upper_value_label.pack(pady=(5, 0))  # Add padding below the label

upper_slider = ctk.CTkSlider(master=upper_frame, from_=-20, to=50, command=update_upper, variable=upper_value, orientation='vertical', corner_radius=12)
upper_slider.pack()  # Pack to fill the frame

upper_slider.set(30)  # Default starting position



# Graph frame
graph_frame = ctk.CTkFrame(master=center_frame, corner_radius=12,width=300)
graph_frame.grid(row=0, column=1,padx=10, pady=10, sticky="nsew")

graph_label = ctk.CTkLabel(graph_frame, text="Graph", font=("Arial", 16))
graph_label.pack(padx=20, pady=20)
display_weather_forecast(get_weather_forecast())


# Summary frame
summary_frame = ctk.CTkFrame(master=center_frame, corner_radius=12, width=250)
summary_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

summary_label = ctk.CTkLabel(summary_frame, text="Summary", font=("Calibri", 18), text_color='grey')
summary_label.place(relx=0.05, rely=0.02, anchor="nw")

summary_value_label = ctk.CTkLabel(summary_frame, text=default_summary, font=("Calibri", 20), text_color='white', wraplength=300, justify='left')
summary_value_label.pack(padx=(20,10), pady=(30,10), anchor='nw',expand=False)





def change_mode(selected_mode):
    ctk.set_appearance_mode(selected_mode)

# Function to show "Refreshing..." while updating the UI
def show_refreshing_label():
    refresh_label.grid(row=0, column= 0, padx=120, pady=(5,0), sticky="w")
    refresh_label.update()

# Function to hide the "Refreshing..." label after the update is done
def hide_refreshing_label():
    refresh_label.grid_forget()
    
# Function to update frequency based on user selection
def update_frequency(selected_frequency):
    global update_interval
    global is_updating
    if selected_frequency == "10s":
        update_interval = 10000  # after() method uses milliseconds
    elif selected_frequency == "30s":
        update_interval = 30000
    elif selected_frequency == "1min":
        update_interval = 60000
    elif selected_frequency == "5min":
        update_interval = 300000
    elif selected_frequency == "15min":
        update_interval = 900000
    
    # If the updating is already running, cancel the previous one and restart
    if is_updating:
        root.after_cancel(start_weather_updates)  # Cancel any previous update
    start_weather_updates()

# Function to start periodic updates
def start_weather_updates():
    global is_updating
    is_updating = True
    
    # Show the "Refreshing..." label
    show_refreshing_label()
    
    if weather_data:
        update_weather_display(weather_data)  # Update display with new data
    
    # Hide the "Refreshing..." label after the update is complete
    hide_refreshing_label()

    # Schedule the next update based on the selected interval
    root.after(update_interval, start_weather_updates)
        
# Timer and Notification Trigger
def set_notification_timer(interval):
    global notification_enabled
    while notification_enabled:
        if weather_data:  # Ensure weather_data is not None
            send_weather_notification(weather_data)  # Assuming weather_data is the latest fetched weather data
        else:
            print("Error: Weather data is not available for notifications.")
        time.sleep(interval)

# Create the notification function
def send_weather_notification(data):
    # Check if data is None
    if data is None:
        print("No weather data available.")
        return  # Exit the function if data is None


    city = data['name']
    temperature = data['main']['temp']
    feels_like = data['main']['feels_like']
    weather_description = data['weather'][0]['description']
    rain_volume = data.get('rain', {}).get('1h', 0)
    cloudiness = data['clouds']['all']
    wind_speed = data['wind']['speed']
    humidity = data['main']['humidity']
    
    icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
    icon_response = requests.get(icon_url)
    icon_image = Image.open(BytesIO(icon_response.content))
    icon_tk = ImageTk.PhotoImage(icon_image)

    # Convert PIL Image to CTkImage
    icon_path = os.path.join("icons", f"current_weather_icon.png")
    #icon_tk.save(icon_path)
    
    summary_input = (
            f"{city} "
            f"feels like {feels_like}°C. "
            f"Humidity is at {humidity}%, with {weather_description}. "
            f"The wind speed is {wind_speed} m/s. "
            f"Rain volume in the last hour is {rain_volume} mm. "
            f"The sky is {cloudiness}% cloudy."
    )

    sentences = sent_tokenize(summary_input)

    # Select the first 'num_sentences' sentences as a summary
    summary = ' '.join(sentences[:3])
            
    # Create the notification
    t = str(temperature)+'°C - '+weather_description
    toast = Notification(app_id='WeatherApp',
                        title=t,
                        msg=summary,
                        duration="long",
                        icon=r"D:/zeotap/weatherapp/icons/current_weather_icon.png")


    # Set notification sound
    toast.set_audio(audio.Default, loop=False)  # Play default sound once
    
    # Display the notification
    toast.show()
    


# Dropdown Menu for Notification Timing
def update_notification_interval(selected_time):
    global notification_enabled
    global notification_interval

    # Stop any ongoing notifications if "Off" is selected
    if selected_time == "Off":
        notification_enabled = False
        return  # Exit the function, stopping notifications
    
    # Otherwise, continue as normal and set the interval
    notification_enabled = True
    if selected_time == "10min":
        notification_interval = 60  # 10 minutes
    elif selected_time == "30min":
        notification_interval = 1800  # 30 minutes
    elif selected_time == "1hr":
        notification_interval = 3600  # 1 hour
    elif selected_time == "3hrs":
        notification_interval = 10800  # 3 hours
    elif selected_time == "now":
        notification_interval = 1
    
    set_notification_timer(notification_interval)

def update_units(selected_unit):
    global unit_system
    
    # Update unit_system based on selection
    if selected_unit == "metric":
        unit_system = "metric"
    elif selected_unit == "imperial":
        unit_system = "imperial"
    elif selected_unit == "SI":
        unit_system = "standard"  # OpenWeatherMap uses 'standard' for Kelvin
    
    # Fetch the weather data again with the new unit
    city = entry_city.get()
    if city:
        weather_data = fetch_weather(city, unit_system)
        if weather_data:
            update_weather_display(weather_data, unit_system)


def update_units(selected_unit):
    global unit_system
    
    # Update unit_system based on selection
    if selected_unit == "Metric (°C)":
        unit_system = "metric"
    elif selected_unit == "Imperial (°F)":
        unit_system = "imperial"
    elif selected_unit == "SI (K)":
        unit_system = "standard"  # OpenWeatherMap uses 'standard' for Kelvin
    
    # Fetch the weather data again with the new unit
    city = entry_city.get()
    if city:
        weather_data = fetch_weather(city, unit_system)
        if weather_data:
            update_weather_display(weather_data, unit_system)

def check_temperature_alert(current_temp):
    global alert_triggered  # To track if the alert has been sent

    # Only check for alerts if the feature is enabled
    if not alert_enabled.get():
        return  # Exit if alert is not enabled

    lower_limit = lower_value.get()
    upper_limit = upper_value.get()

    # If temperature is outside the set range and no alert has been triggered yet
    if (current_temp < lower_limit or current_temp > upper_limit) and not alert_triggered:
        if current_temp < lower_limit:
            alert_message = f"Temperature is too low! {current_temp}°C is below the limit of {lower_limit}°C."
        else:
            alert_message = f"Temperature is too high! {current_temp}°C is above the limit of {upper_limit}°C."

        # Trigger the notification
    send_alert_notification(current_temp, alert_message)

    # Reset the alert trigger if temperature returns to the safe range
    if lower_limit <= current_temp <= upper_limit:
        alert_triggered = False
        
# Function to send the alert notification
def send_alert_notification(temp, message):
    toast = Notification(app_id='WeatherApp',
                         title=f"Temperature Alert: {temp}°C",
                         msg=message,
                         duration="long",
                         icon=r"D:/zeotap/weatherapp/icons/alert_icon.png")

    # Set notification sound
    toast.set_audio(audio.Default, loop=True)  # Play default sound once

    # Display the notification
    toast.show()


# Main content frame for weather data
footer_frame = ctk.CTkFrame(master=root, fg_color="transparent")
footer_frame.pack(pady=0, padx=10, fill="both", expand=True)

# Configure grid layout for the weather content
footer_frame.columnconfigure(0, weight=1)  # Temperature
footer_frame.columnconfigure(1, weight=1)  # Air Quality, Wind Speed
footer_frame.columnconfigure(2, weight=1)  # Humidity, Visibility
footer_frame.columnconfigure(3, weight=1)  
footer_frame.columnconfigure(4, weight=1)

# Update Interval frame
theme_frame = ctk.CTkFrame(master=footer_frame, width=100, height=100, corner_radius=12)
theme_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
modes = ["Dark", "Light", "system"]
theme_menu = ctk.CTkOptionMenu(master=theme_frame, values=modes, command=change_mode,font=("Calibri", 20), width=100, height=60)
#theme_menu.set("Dark")
theme_menu.pack(padx=10, pady=10, fill='both')


# Update Interval Frame for changing the weather update interval
update_frame = ctk.CTkFrame(master=footer_frame, width=100, height=100, corner_radius=12)
update_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Dropdown menu for update intervals
update_options = ["10s", "30s", "1min", "5min", "15min",]
update_menu = ctk.CTkOptionMenu(master=update_frame, values=update_options, command=update_frequency, font=("Calibri", 20), width=100, height=60)
update_menu.set("1min")  # Default interval
update_menu.pack(pady=10, padx=10, fill='both')

# "Refreshing..." Label to show during updates
refresh_label = ctk.CTkLabel(master=header_frame, text="Refreshing...", font=("calibri", 16))
refresh_label.grid_forget()


# Notification Interval frame
notification_frame = ctk.CTkFrame(master=footer_frame, width=100, height=100, corner_radius=12)
notification_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

# Dropdown menu for notification intervals with an "Off" option
notification_options = ["Off", "10min", "30min", "1hr", "3hrs"]
notification_menu = ctk.CTkOptionMenu(master=notification_frame, values=notification_options, command=update_notification_interval, font=("Calibri", 20), width=100, height=60)
notification_menu.set("Off")  # Default selection to disable notifications
notification_menu.pack(pady=10, padx=10, fill='both')


# Units frame (metric/imperial/Kelvin)
units_frame = ctk.CTkFrame(master=footer_frame, width=100, height=100, corner_radius=12)
units_frame.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")

# Dropdown menu for units
units_options = ["Metric (°C)", "Imperial (°F)", "SI (K)"]
units_menu = ctk.CTkOptionMenu(master=units_frame, values=units_options, command=update_units, font=("Calibri", 20), width=100, height = 60)
units_menu.set("Metric (°C)")  # Default selection
units_menu.pack(pady=10, padx=10, fill='both')


alert_triggered = False
alert_enabled = ctk.BooleanVar(value=True)

# Alert Temperature frame with toggle switch for enabling/disabling alerts
alert_frame = ctk.CTkFrame(master=footer_frame, width=100, height=100, corner_radius=12)
alert_frame.grid(row=0, column=4, padx=10, pady=10, sticky="nsew")

# Toggle switch for enabling/disabling alerts
alert_toggle = ctk.CTkSwitch(alert_frame, text="Alert", variable=alert_enabled, font=("Calibri", 20), width=100, height = 60)
alert_toggle.pack(padx=10, pady=10)

root.mainloop()