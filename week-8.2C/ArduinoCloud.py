from arduino_iot_cloud import ArduinoCloudClient
from datetime import datetime
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import threading
import logging
from collections import deque


# --------------------------------------------------
# Q2 - Reusable live data API
# --------------------------------------------------

def create_live_stream(app,sensor_names,buffer_size=100,interval_ms=500,title="Live Sensor Data"):
    
    timestamps = deque(maxlen=buffer_size)

    buffers = {
        name: deque(maxlen=buffer_size)
        for name in sensor_names
    }

    pending_values = {
        name: None
        for name in sensor_names
    }


    def add_value(sensor_name, value):

        if sensor_name not in buffers:
            raise ValueError(f"Unknown sensor: {sensor_name}")

        pending_values[sensor_name] = value

        if all(
            pending_values[name] is not None
            for name in sensor_names
        ):
            timestamps.append(datetime.now())

            for name in sensor_names:
                buffers[name].append(
                    pending_values[name]
                )

                pending_values[name] = None


    app.layout = html.Div([
        html.H2(title),

        dcc.Graph(id="live-sensor-graph"),

        dcc.Interval(id="live-sensor-update",interval=interval_ms,n_intervals=0)
    ])


    @app.callback(Output("live-sensor-graph", "figure"),Input("live-sensor-update", "n_intervals"))
    
    
    def update_graph(n):

        fig = go.Figure()

        for name in sensor_names:
            fig.add_trace(go.Scatter(x=list(timestamps),y=list(buffers[name]),mode="lines",name=name))

        fig.update_layout(title=title,xaxis_title="Time",yaxis_title="Sensor value")
        return fig


    return add_value


# --------------------------------------------------
# Arduino setup
# --------------------------------------------------

logging.basicConfig(datefmt="%H:%M:%S",format="%(asctime)s.%(msecs)03d %(message)s",level=logging.INFO)

DEVICE_ID = b"01212861-b8d3-4303-ba87-aed9a5d26260"
SECRET_KEY = b"Fq4lc!sK8YirZ6I2ndPMBvYfo"


# --------------------------------------------------
# Dash application
# --------------------------------------------------

app = Dash(__name__)


add_sensor_value = create_live_stream(app=app,sensor_names=["X", "Y", "Z"],buffer_size=100,interval_ms=500,title="Smartphone Accelerometer")


# --------------------------------------------------
# Arduino callbacks
# --------------------------------------------------

def on_x_changed(client, value):
    add_sensor_value("X", value)


def on_y_changed(client, value):
    add_sensor_value("Y", value)


def on_z_changed(client, value):
    add_sensor_value("Z", value)


# --------------------------------------------------
# Arduino Cloud
# --------------------------------------------------

client = ArduinoCloudClient(device_id=DEVICE_ID,username=DEVICE_ID,password=SECRET_KEY)

client.register("acceleration_x",value=None,on_write=on_x_changed)
client.register("acceleration_y",value=None,on_write=on_y_changed)
client.register("acceleration_z",value=None,on_write=on_z_changed)


def run_arduino():
    client.start()


arduino_thread = threading.Thread(target=run_arduino,daemon=True)

arduino_thread.start()


if __name__ == "__main__":
    app.run(debug=False)