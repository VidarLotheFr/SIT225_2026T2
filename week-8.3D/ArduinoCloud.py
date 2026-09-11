from arduino_iot_cloud import ArduinoCloudClient
from datetime import datetime
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
from collections import deque
import threading, time, os, base64, cv2
import pandas as pd

DATA_FOLDER = "captured_data"
SAMPLE_INTERVAL = 0.5
CAPTURE_INTERVAL = 10

os.makedirs(DATA_FOLDER, exist_ok=True)


def create_live_stream(app, sensors, buffer_size=100):

    times = deque(maxlen=buffer_size)
    buffers = {s: deque(maxlen=buffer_size) for s in sensors}
    latest = {s: None for s in sensors}

    capture_times = []
    capture_data = {s: [] for s in sensors}

    latest_image = None
    sequence = 1
    lock = threading.Lock()


    def add_value(name, value):
        print(
            f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]} "
            f"{name} = {value}"
        )

        with lock:
            latest[name] = value


    def sample_loop():
        while True:
            time.sleep(SAMPLE_INTERVAL)

            with lock:
                if not all(latest[s] is not None for s in sensors):
                    continue

                now = datetime.now()
                times.append(now)
                capture_times.append(now)

                for s in sensors:
                    buffers[s].append(latest[s])
                    capture_data[s].append(latest[s])


    def capture_loop():
        nonlocal sequence, latest_image

        while True:
            time.sleep(CAPTURE_INTERVAL)

            with lock:
                if not capture_times:
                    continue

                t = list(capture_times)
                values = {s: list(capture_data[s]) for s in sensors}

                capture_times.clear()
                for s in sensors:
                    capture_data[s].clear()

            stamp = datetime.now().strftime("%Y%m%d%H%M%S")
            name = f"{sequence}_{stamp}"

            csv_path = os.path.join(DATA_FOLDER, name + ".csv")
            img_path = os.path.join(DATA_FOLDER, name + ".jpg")

            data = {"timestamp": t, **values}
            pd.DataFrame(data).to_csv(csv_path, index=False)

            cam = cv2.VideoCapture(0)
            time.sleep(0.3)
            ok, frame = cam.read()
            cam.release()

            if ok:
                cv2.imwrite(img_path, frame)
                with lock:
                    latest_image = img_path

            print(f"Saved {name} ({len(t)} samples)")
            sequence += 1


    threading.Thread(target=sample_loop, daemon=True).start()
    threading.Thread(target=capture_loop, daemon=True).start()


    app.layout = html.Div([
        html.H2("Smartphone Accelerometer"),
        dcc.Graph(id="graph"),

        html.H3("Latest Activity Image"),
        html.Img(id="image", style={"width": "500px"}),

        dcc.Interval(id="update", interval=500, n_intervals=0)
    ])


    @app.callback(
        Output("graph", "figure"),
        Input("update", "n_intervals")
    )
    def update_graph(_):

        with lock:
            fig = go.Figure()

            for s in sensors:
                fig.add_trace(go.Scatter(
                    x=list(times),
                    y=list(buffers[s]),
                    mode="lines+markers",
                    name=s
                ))

        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Acceleration"
        )

        return fig


    @app.callback(
        Output("image", "src"),
        Input("update", "n_intervals")
    )
    def update_image(_):

        with lock:
            path = latest_image

        if not path or not os.path.exists(path):
            return None

        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()

        return "data:image/jpeg;base64," + encoded


    return add_value


DEVICE_ID = b"Enter your own if you want to use it -> get it on Arduino IoT cloud"
SECRET_KEY = b"Get the secret key by downloading the pdf you get when assigning a python THING"

app = Dash(__name__)
add_sensor = create_live_stream(app, ["X", "Y", "Z"])


def on_x_changed(client, value):
    add_sensor("X", value)

def on_y_changed(client, value):
    add_sensor("Y", value)

def on_z_changed(client, value):
    add_sensor("Z", value)


client = ArduinoCloudClient(
    device_id=DEVICE_ID,
    username=DEVICE_ID,
    password=SECRET_KEY
)

client.register("acceleration_x", value=None, on_write=on_x_changed)
client.register("acceleration_y", value=None, on_write=on_y_changed)
client.register("acceleration_z", value=None, on_write=on_z_changed)

threading.Thread(target=client.start, daemon=True).start()


if __name__ == "__main__":
    app.run(debug=False)
