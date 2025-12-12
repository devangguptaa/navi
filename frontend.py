import json
import ssl
import threading
import time

import paho.mqtt.client as mqtt
import gradio as gr

# ---------------- AWS IoT Core configuration ----------------
AWS_IOT_ENDPOINT = "a3ek4nc9h6bz8z-ats.iot.us-east-2.amazonaws.com"
AWS_IOT_PORT = 8883

DATA_TOPIC = "test/data"
ALERT_TOPIC = "device/NaviCane/alerts"

CLIENT_CERT_PATH = "/Users/devanggupta/Downloads/1e6afb8143cf2d3cfe6c445e69d2dc6505545dc34b97ef8a5d570c69bd07d5a3-certificate.pem.crt"
PRIVATE_KEY_PATH = "/Users/devanggupta/Downloads/1e6afb8143cf2d3cfe6c445e69d2dc6505545dc34b97ef8a5d570c69bd07d5a3-private.pem.key"
CLIENT_ID = "NaviCane"

# ---------------- Shared state ----------------
latest_coords = {"lat": None, "lon": None}
coords_lock = threading.Lock()

latest_alert = {"message": None, "timestamp": None, "unread": False}
alert_lock = threading.Lock()

# ---------------- MQTT callbacks ----------------
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected to AWS IoT Core")
        client.subscribe(DATA_TOPIC)
        client.subscribe(ALERT_TOPIC)
        print(f"Subscribed to: {DATA_TOPIC} and {ALERT_TOPIC}")
    else:
        print(f"Connection failed with code {rc}")


def on_message(client, userdata, msg):
    try:
        payload_bytes = msg.payload
        print(f"Message received on topic {msg.topic}: {payload_bytes}")

        payload = payload_bytes.decode("utf-8")
        data = json.loads(payload)

        # Data topic for GPS
        if msg.topic == DATA_TOPIC:
            lat = data.get("lat", data.get("latitude"))
            lon = data.get("lon", data.get("longitude"))

            if lat is not None and lon is not None:
                with coords_lock:
                    latest_coords["lat"] = float(lat)
                    latest_coords["lon"] = float(lon)
                print(f"Updated coordinates: {lat}, {lon}")
            else:
                print("Payload missing lat or lon fields:", payload)

        # Alert topic for push notifications
        elif msg.topic == ALERT_TOPIC:
            # You can customize what field to read from the JSON
            # For now try "message" and fall back to the raw payload
            alert_msg = data.get("message", payload)
            with alert_lock:
                latest_alert["message"] = alert_msg
                latest_alert["timestamp"] = time.time()
                latest_alert["unread"] = True
            print(f"New alert: {alert_msg}")

    except Exception as e:
        print("Error parsing message:", e)


# ---------------- MQTT client setup ----------------
def start_mqtt_client():
    client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv5)

    client.tls_set(
        certfile=CLIENT_CERT_PATH,
        keyfile=PRIVATE_KEY_PATH,
        tls_version=ssl.PROTOCOL_TLSv1_2,
    )

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(AWS_IOT_ENDPOINT, AWS_IOT_PORT, keepalive=60)

    # Non blocking network loop
    client.loop_start()

    return client


def generate_map_embed_html(lat, lon, zoom=13):
    """
    OpenStreetMap iframe embed with a wider bounding box (less zoomed-in).
    """
    delta = 0.01  # bigger value = zoomed out more

    left = lon - delta
    right = lon + delta
    top = lat + delta
    bottom = lat - delta

    return f"""
    <iframe
      width="100%"
      height="400"
      frameborder="0"
      scrolling="no"
      marginheight="0"
      marginwidth="0"
      src="https://www.openstreetmap.org/export/embed.html?bbox={left}%2C{bottom}%2C{right}%2C{top}&layer=mapnik&marker={lat}%2C{lon}">
    </iframe>
    <br/>
    <small>
      <a href="https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map={zoom}/{lat}/{lon}" target="_blank">
          View larger map
      </a>
    </small>
    """



# ---------------- Gradio interface logic ----------------
def get_current_location():
    """
    Called from Gradio to fetch the latest coordinates and render UI pieces.
    """
    with coords_lock:
        lat = latest_coords["lat"]
        lon = latest_coords["lon"]

    if lat is None or lon is None:
        status = "Waiting for coordinates from MQTT..."
        map_html = "<p>No location data received yet.</p>"
        directions_html = "<p>Directions will appear when a location is received.</p>"
        return status, map_html, directions_html

    status = f"Latest location: {lat:.6f}, {lon:.6f}"

    # map_html = generate_leaflet_map_html(lat, lon)
    map_html = generate_map_embed_html(lat, lon)
    # Directions link using Google Maps
    # Leaving out origin means Google Maps uses "Your location" by default
    directions_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
    directions_html = f"""
    <button onclick="window.open('{directions_url}', '_blank')" 
            style="padding: 0.6rem 1.2rem; font-size: 1rem; cursor: pointer;">
        Get directions in Google Maps
    </button>
    """

    return status, map_html, directions_html


def get_alert_for_ui():
    """
    Called by a Gradio Timer to check if there is a new alert.
    """
    with alert_lock:
        msg = latest_alert["message"]
        ts = latest_alert["timestamp"]
        unread = latest_alert["unread"]

        if msg is None:
            return "No alerts received yet."

        # Format time
        ts_str = time.strftime("%H:%M:%S", time.localtime(ts)) if ts else ""

        if unread:
            # Mark as read after notifying
            latest_alert["unread"] = False
            return f"New alert at {ts_str}: {msg}"
        else:
            return f"Last alert at {ts_str}: {msg}"


def build_interface():
    with gr.Blocks(title="NAVI - A Smart Cane") as demo:
        gr.Markdown(
            """
            # NAVI - A Smart Cane
            """
        )

        with gr.Row():
            status_box = gr.Textbox(
                label="Status",
                value="Click 'Refresh from MQTT' to load the latest coordinates",
                interactive=False,
            )

        map_html = gr.HTML(label="Map")
        directions_html = gr.HTML(label="Directions")

        with gr.Row():
            alert_box = gr.Textbox(
                label="Alerts",
                value="Waiting for alerts...",
                interactive=False,
            )

        refresh_btn = gr.Button("Refresh from MQTT")

        refresh_btn.click(
            fn=get_current_location,
            inputs=[],
            outputs=[status_box, map_html, directions_html],
        )

        # Call once on load (no 'every' argument here)
        demo.load(
            fn=get_current_location,
            inputs=[],
            outputs=[status_box, map_html, directions_html],
        )

        # Timer to poll for new alerts and update alert_box
        alert_timer = gr.Timer(2.0)  # every 2 seconds
        alert_timer.tick(
            fn=get_alert_for_ui,
            inputs=[],
            outputs=[alert_box],
        )

    return demo


if __name__ == "__main__":
    mqtt_client = start_mqtt_client()
    time.sleep(1)
    demo = build_interface()
    demo.launch(server_name="0.0.0.0", server_port=7860)
