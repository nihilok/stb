# stb
###### a take on the popular word game 'Stop the bus'

To run the server, you will need python3 with pip installed. Clone repository and install requirements:

```
git clone https://github.com/nihilok/stb.git
cd stb/
pip install -r requirements.txt
gunicorn -k eventlet -w 1 stb_server:app --bind 0.0.0.0:<PORT>
```

In a browser, visit `localhost:<PORT>` on host machine, or `<local-ip>:<PORT>` on local network (or `<EXTERNAL-IP/domain-name>:<PORT>` over the web - you must forward the port in question or otherwise allow traffic in firewall settings).

Example:

`gunicorn ... --bind 0.0.0.0:7777`

`http://example.com:7777`
