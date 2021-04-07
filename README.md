# stb
a take on the popular word game 'Stop the bus'

```
pip install -r- requirements.txt
gunicorn -k eventlet -w 1 stb_server:app --bind <HOST>:<PORT>
```

Visit <HOST>:<PORT> in browser to play game.
