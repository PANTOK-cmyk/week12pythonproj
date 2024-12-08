import requests
import json
from flask import Flask, render_template, request

app = Flask(__name__)

def are_weather_conditions_bad(temperature: float, wind_speed: float, precipitation_probability: float) -> bool:
    """Проверяет, плохая ли погода."""
    if temperature < 0 or temperature > 35:
        return True
    if wind_speed > 50:
        return True
    if precipitation_probability > 70:
        return True
    return False

def get_current_conditions(location_key):
    """Получает текущие погодные условия."""
    try:
        url = f"http://dataservice.accuweather.com/forecasts/v1/daily/1day/{location_key}?apikey=R8ACGsNytrDVF8IF0pxx0GWCLwmBhiU6&details=True&metric=True"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Сохраняем данные в файл (для отладки или последующего использования)
        with open("weather_data.json", "w") as f:
            json.dump(data, f, indent=4)

        # Открываем файл weather_data.json для чтения
        with open("weather_data.json", "r") as f:
            data = json.load(f)


        daily_forecast = data.get("DailyForecasts", [{}])[0]
        if not daily_forecast:
            raise ValueError("DailyForecasts отсутствует или пуст в weather_data.json.")

        temperature = daily_forecast.get("Temperature", {}).get("Maximum", {}).get("Value")
        wind_speed = daily_forecast.get("Day", {}).get("Wind", {}).get("Speed", {}).get("Value")
        rain_probability = daily_forecast.get("Day", {}).get("RainProbability")
        snow_probability = daily_forecast.get("Day", {}).get("SnowProbability")
        precipitation_probability = max(rain_probability or 0, snow_probability or 0)

        if temperature is not None and wind_speed is not None:
            return are_weather_conditions_bad(temperature, wind_speed, precipitation_probability)
        else:
            return "Не удалось получить все необходимые данные о погоде."

    except requests.exceptions.RequestException as e:
        return f"Ошибка подключения к API: {e}"
    except (KeyError, IndexError, TypeError, ValueError) as e:
        return f"Ошибка обработки данных: {e}"
    except Exception as e:
        return f"Непредвиденная ошибка: {e}"


def get_weather_data(latitude: float, longitude: float):
    """Получает данные о погоде по координатам."""
    try:
        url = f"http://dataservice.accuweather.com/locations/v1/cities/geoposition/search?apikey=R8ACGsNytrDVF8IF0pxx0GWCLwmBhiU6&q={latitude},{longitude}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and data:
            location_key = data[0].get("Key")
        elif isinstance(data, dict) and data.get("Key"):
            location_key = data.get("Key")
        else:
            return "Неверно введены координаты или не удалось найти локацию."

        if location_key:
            weather_result = get_current_conditions(location_key)
            return weather_result
        else:
            return "Ключ локации не найден."

    except requests.exceptions.RequestException as e:
        return f"Ошибка подключения к API: {e}"
    except Exception as e:
        return f"Непредвиденная ошибка: {e}"



@app.route("/", methods=["GET", "POST"])
def index():
    """Обрабатывает GET и POST запросы."""
    if request.method == "POST":
        try:
            start_lat = float(request.form.get("latitude_start"))
            start_lon = float(request.form.get("longitude_start"))
            end_lat = float(request.form.get("latitude_finish"))
            end_lon = float(request.form.get("longitude_finish"))
        except ValueError:
             return render_template("index.html", start_weather="Неверный формат координат", end_weather="")


        data = {
            "latitude_start": start_lat,
            "longitude_start": start_lon,
            "latitude_finish": end_lat,
            "longitude_finish": end_lon
        }
        try:
            with open("data.json", "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("Ошибка сохранения в JSON:", e)

        start_weather = get_weather_data(start_lat, start_lon)
        end_weather = get_weather_data(end_lat, end_lon)


        start_message = start_weather if isinstance(start_weather, str) else ("В начале маршрута погода плохая" if start_weather else "В начале маршрута погода хорошая")
        end_message = end_weather if isinstance(end_weather, str) else  ("В конце маршрута погода плохая" if end_weather else "В конце маршрута погода хорошая")

        return render_template("index.html", start_weather=start_message, end_weather=end_message)

    return render_template("index.html", start_weather="", end_weather="")

if __name__ == "__main__":
    app.run(debug=True)
