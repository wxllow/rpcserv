# RPCServ

RPCServ is a server and client designed to allow applications/services to send rich presence to the client from anywhere in the world by making a simple HTTP request.

It was made for use in a mobile Apple Music Discord Rich Presence shortcut, but can be used for anything. :p

Also BIG CREDITS to [BennoCrafter](https://github.com/BennoCrafter) who also worked on this project!

## Client Instructions

### Installation

**Downloads coming soon!**

#### Manual Installation

**Requirements:**

- Python 3.9+
- [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)

1. Clone the github repository and change directory

```bash
git clone https://github.com/wxllow/rpcsev
cd rpcserv/client
```

2. Install the dependencies

```bash
poetry install
```

### Running

1. Run the client

```bash
poetry run python client.py
```

2. Create a token

Go to [rpcserv.wxllow.dev](https://rpcserv.wxllow.dev) and login to create a secret token. (Will be different if you use a custom server)

3. Add the token to the client

Once the app is running, you will be prompted to enter a token. Enter the token you created in step 2 and click Ok.

4. Send a request

**Curl Example:**

```bash
curl -X POST -H "Content-Type: application/json" -d '{"state": "Hello World!", "details": "RPCServ is awesome!"}
```

### Configuration

#### Reset Token

Once you have authorized with the server, your secret token will persist even after reauthenticating. To reset your token, simply go to [rpcserv.wxllow.dev/authorize/reset](https://rpcserv.wxllow.dev/authorize/reset) (Will be different if you use a custom server)

#### Custom Client ID

If you would like to use a custom client ID, you can set one in your config file (located at `~/.config/rpcserv/config.json` on macOS/Linux and `%APPDATA%\rpcserv\config.json` on Windows).

Example:

```json
{
    "client_id": "123456789012345678"

}
```

#### Custom Server

You can also set a custom server in your config file.
Example:

```json
{
    "server": "https://rpcserv.wxllow.dev"

}
```

#### Request Parameters List

List of parameters that can be sent in an RPC request.

```javascript
{
    "clear": boolean, // If true, clears the rich presence, ignoring all other parameters
    "state": string,
    "details": string,
    "large_image": string,
    "large_text": string,
    "metadata": {}, // Metadata that can be used by a client for whatever purpose
}
```
