# SNIPER

[Flask](https://github.com/pallets/flask) based website to snipe your friends and laugh from their skill issue

## Initial Startup

In order to start SNIPER run

Windows:
```bash 
python .\app.py
```
Linux:
```bash
python3 ./app.py
```

If you don't have python you can download it from their [website](https://www.python.org/downloads/) or install using package manager:

Ubuntu/Debian:
```bash
sudo apt install python3
```

I don't recommend using Microsoft Store version for it, because it have some issues with modules management.

On first start SNIPER should automatically generate database template but you still need to edit some of it values to make it work properly. Create your [application](https://osu.ppy.sh/wiki/en/osu!api) and put client_id, client_secret and redirect_uri in database application section.

```json
{
    "application": {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }
}
```

If you inserted correct values you should see in your terminal something like this:
```bash
 * Serving Flask app 'app' (lazy loading)
   WARNING: This is a development server. Do not use it in a production deployment.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:80 (Press CTRL+C to quit)
```

Now you should be able to load website.

## Configuration

You can configure SNIPER in config section of database:

```bash
"config": {
        "path": {
            "cover": "./static/cover",
            "banner": "./static/banner.jpg",
            "fonts": "./static/fonts"
        }
    }
```

For now you can configure:

- cover path
- banner path
- fonts path

###Note that due to lack of data injection in css from backend like in templates, fonts paths in it are hardcoded.


## Contributing

If you find any problem or have an idea feel free to post it in [issues](https://github.com/Dalciop/sniper/issues/) tab.