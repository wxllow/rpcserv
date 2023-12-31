# Ran on the client machine, this connects to the server and updates the Discord Rich Presence status.
import asyncio
import os
import sys
import socketio
import pypresence
import pystray
from PIL import Image
from tkinter import simpledialog, messagebox
import threading
import apple_music as apple_music_service
from utils import get_config, save_config, locate_config

config = get_config()
CLIENT_ID = config.get("client_id") or "952320054870020146"
SERVER = config.get("server") or "https://rpcserv.wxllow.dev"
SECRET = config.get("secret")

loop = asyncio.get_event_loop()
sio = socketio.AsyncClient()
rpc = pypresence.AioPresence(
    client_id=CLIENT_ID,
    loop=loop,
)


# Connect to socket.io
@sio.event
async def connect():
    print("Connected to socket")
    await rpc.connect()
    await rpc.clear()
    print("Connected to Discord")


@sio.on("status_update")
async def status_update(data):
    print(f"GOT STATUS UPDATE: {data}")

    if data["service"] == "apple_music":
        service_data = await apple_music_service.rpcserv(data)

    # Merge service data with data (override data with service_data, do not override if None)
    data = {**data, **service_data}

    await rpc.update(
        state=data["state"],
        details=data["details"],
        start=data.get("start"),
        buttons=data.get("buttons"),
        large_image=data.get("large_image"),
    )


@sio.on("status_clear")
async def status_clear():
    print("GOT STATUS CLEAR")
    await rpc.clear()


@sio.event
async def disconnect():
    print("Disconnected from socket")
    await rpc.close()
    print("Disconnected from Discord")


async def thread_async(secret):
    print("Connecting to socket")
    try:
        await sio.connect(f"{SERVER}/?secret={secret}", transports=["websocket"])
        await sio.wait()
    except socketio.exceptions.ConnectionError:
        print(
            "ERROR: Could not connect to server. Is it running and is the secret correct?"
        )
        config["startup_prompt"] = True
        save_config(config)
        sys.exit(1)


def thread_func(secret):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(thread_async(secret))


def reset_config():
    # Reset config
    config = {}
    save_config(config)
    print("Config reset, restarting...")
    os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)


def main():
    print(f"Your config file is located at: {locate_config()}")
    global config

    secret = SECRET

    # Prompt for secret if not set or if an error occured last time
    if (not config.get("secret")) or config.get("startup_prompt"):
        runAgain = True

        while runAgain:
            runAgain = False

            secret = simpledialog.askstring(
                "Secret", "What is your secret?", initialvalue=SECRET
            ).strip()

            if secret:
                config["secret"] = secret
                config["startup_prompt"] = False
                save_config(config)
            else:
                runAgain = True

    # Make a white square image
    image = Image.new("RGB", (64, 64), (255, 255, 255))

    tray = pystray.Icon(
        "RPC",
        image,
        "RPC",
        menu=pystray.Menu(
            pystray.MenuItem("Reset Config", reset_config),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda: tray.stop()),
        ),
    )

    # Run async a_main function in a seperate thread
    thread = threading.Thread(target=thread_func, args=(secret,), daemon=True)

    thread.start()

    tray.run()


if __name__ == "__main__":
    # Ensure that if on Linux, we use AppIndicator for best compatibility
    if sys.platform == "linux":
        # Check if appindicator is available
        try:
            import gi

            gi.require_version("AppIndicator3", "0.1")
        except (ImportError, ValueError) as e:
            print(f"Error: {e}")
            messagebox.showerror(
                title="Error",
                message="AppIndicator is not installed. Please install python-pygobject and libappindicator-gtk3. (Package names may be different, these are for Arch!)",
            )
            sys.exit(1)

        os.environ["PYSTRAY_BACKEND"] = "appindicator"

    try:
        main()
    except KeyboardInterrupt:
        pass
