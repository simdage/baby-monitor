import board
import digitalio
from adafruit_bme280 import basic as adafruit_bme280
import time
from google.cloud import bigquery
import os
from dotenv import load_dotenv

# Configuration
load_dotenv()

# Apply google credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

i2c = board.I2C()  # uses board.SCL and board.SDA
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
client = bigquery.Client()

def main():

    while True:
        # Record the temperature, humidity, and pressure
        print("\nTemperature: %0.1f C" % bme280.temperature)
        print("Humidity: %0.1f %%" % bme280.humidity)
        print("Pressure: %0.1f hPa" % bme280.pressure)


        temp = []
        hum = []
        press = []
        for i in range(5):
            temperature = bme280.temperature
            humidity = bme280.humidity
            pressure = bme280.pressure

            temp.append(temperature)
            hum.append(humidity)
            press.append(pressure)

            time.sleep(1)

        # Calculate the average
        temperature = sum(temp) / len(temp)
        humidity = sum(hum) / len(hum)
        pressure = sum(press) / len(press)

        # Send to BQ table
        table_id = os.getenv("BIGQUERY_TABLE_ID_ENV")
        rows_to_insert = [
            {
                "temperature": round(temperature, 4),
                "humidity": round(humidity, 4),
                "pressure": round(pressure, 4),
                "timestamp": time.time()
            }
        ]
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors == []:
            print("New rows have been added.")
        else:
            print("Encountered errors while inserting rows: {}".format(errors))

    
if __name__ == "__main__":
    main()

    

