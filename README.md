# Weather Application ![Weather Icon](https://github.com/Kowshik-R-2026/Weather_Application/blob/main/weatherapp_icon.ico)

This Weather Application is a user-friendly tool built with Python and CustomTkinter that provides real-time weather forecasts, temperature alerts, and notifications. It allows users to select their preferred temperature units, update intervals, and notification settings while also displaying weather data in a visually appealing manner.

## Features

- Real-time weather data fetching from the OpenWeatherMap API
- Customizable temperature unit selection (Metric, Imperial, SI)
- Adjustable weather update intervals
- Temperature alerts with customizable lower and upper limits
- Notification system that displays weather updates and alerts
- Intuitive UI using CustomTkinter for enhanced aesthetics

## Prerequisites

- Python 3.7 or higher
- Required libraries:
  - [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
  - [requests](https://docs.python-requests.org/en/master/)
  - [Pillow](https://python-pillow.org/)
  - [winotify](https://pypi.org/project/winotify/)
  - [nltk](https://www.nltk.org/)

- You can install the required libraries using pip:

```bash
pip install -r requirements.txt
or
pip install CustomTkinter requests Pillow winotify nltk
```
## Set up your OpenWeatherMap API Key:

- Sign up for an account at OpenWeatherMap.
- Obtain your API key.
- Replace the placeholder in the code with your actual API key.
- Run the application:

1. Ensure you are in the project directory.
2. Execute the following command:
```bash
python app.py
```

# User Interface:
- Launch the application to open the GUI.
- Enter a city name in the input field to fetch the weather data.
- Use the sliders to set temperature alert limits.
- Choose your preferred temperature units (°C, °F, K).
- Adjust the update frequency for real-time weather data.
- Enable or disable alerts using the toggle switch.
- Set notification intervals to receive timely updates.
  
## Real-time Weather Updates:
The application will periodically fetch and display the weather information based on the selected interval.

## Temperature Alerts:
If the current temperature goes below or above the specified limits, you will receive a notification alerting you of the situation.
