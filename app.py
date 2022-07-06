from datetime import datetime
from json import dump, dumps, load, loads
from flask import Flask, Response, render_template, redirect, request, session
from requests import post, get
from PIL import Image, ImageFont, ImageDraw, ImageFilter, ImageEnhance

app = Flask(__name__)

app.secret_key = "secret key"

API_URL = 'https://osu.ppy.sh/api/v2'
TOKEN_URL = 'https://osu.ppy.sh/oauth/token'
OAUTH_URL = 'https://osu.ppy.sh/oauth/authorize?scope=public&response_type=code&redirect_uri=http://127.0.0.1/authorise&client_id=15818'

with open('db.json', 'r+') as file:
    db = load(file)
    application = {
        'client_id': db.get('application')['client_id'],
        'client_secret': db.get('application')['client_secret']
    }

class Endpoint:
    def get_user_scores_all(bid: int, user: int): return f'{API_URL}/beatmaps/{bid}/scores/users/{user}/all'
    def get_own_data(): return f'{API_URL}/me'
    def get_user_data(uid): return f'{API_URL}/users/{uid}'
    def get_beatmap(bid): return f'{API_URL}/beatmaps/{bid}'

class Headers:
    def headers(token):
        return {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }

class RequestData:
    NoOAuthData = {
        'client_id': application['client_id'],
        'client_secret': application['client_secret'],
        'grant_type': 'client_credentials',
        'scope': 'public'
    }
    def OAuthData(code):
        return {
        'client_id': application['client_id'],
        'client_secret': application['client_secret'],
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': 'https://f455-185-157-14-201.eu.ngrok.io/authorise'
    }
    def RefreshOAuth(refresh_token):
        return {
            'grant_type': "refresh_token",
            'refresh_token': refresh_token,
            'client_id': application['client_id'],
            'client_secret': application['client_secret']
        }

class Token:
    def get_NoOAuth():
        response = post(TOKEN_URL, data=RequestData.NoOAuthData)
        return response.json().get('access_token')

    def get_OAuth(code):
        response = post(TOKEN_URL, data=RequestData.OAuthData(code))
        return response.json()

    def refresh_OAuth(refresh_token):
        response = post(TOKEN_URL, data=RequestData.RefreshOAuth(refresh_token))
        return response.json()

def get_data(eurl, token, params=None):
    if params == None:
        response = get(f'{eurl}', headers=Headers.headers(token))
    response = get(f'{eurl}', params=params, headers=Headers.headers(token))
    return response.json()

def process_cover(cover):
    r = get(cover['cover_url'])
    with open(f'./static/cover/{cover["bid"]}.jpg', 'wb') as f:
        f.write(r.content)
    font75 = ImageFont.truetype("./static/fonts/Modern_Sans_Light.otf", 75)
    font50 = ImageFont.truetype("./static/fonts/Modern_Sans_Light.otf", 50)
    coverimg = Image.open(f'./static/cover/{cover["bid"]}.jpg')
    coverimg = coverimg.filter(ImageFilter.GaussianBlur(15))
    coverimg = ImageEnhance.Brightness(coverimg).enhance(0.8)
    draw = ImageDraw.Draw(coverimg)
    draw.text((75, 325), cover['artist'], (255, 255, 255), font=font75)
    draw.text((125, 400), f"{cover['title']} - [{cover['version']}]", (255, 255, 255), font=font50)
    coverimg.save(f'./static/cover/{cover["bid"]}.jpg')

@app.route('/')
def index():
    return get_data(Endpoint.get_user_scores_all(712278, 11525785), Token.get_NoOAuth(), params = {'mode': 'osu'})
    # return render_template("index.html")

@app.route('/me')
def me():
    if('access_token' in session):
        OAuthToken = {
            "access_token": session['access_token'],
            "expires_in": session['expires_in'],
            "token_type": session['token_type'],
            "refresh_token": session['refresh_token']
        }
        return get_data(Endpoint.get_own_data(), OAuthToken['access_token'])
    return redirect('/')

@app.route('/authorise')
def authorise():
    code = request.args.get('code')
    with open('db.json', 'r+') as file:
        db = load(file)
        token_OAuth = Token.get_OAuth(code)
        uid = get_data(Endpoint.get_own_data(), token_OAuth.get('access_token'))['id']
        session['access_token'] = token_OAuth['access_token']
        session['expires_in'] = token_OAuth['expires_in']
        session['token_type'] = token_OAuth['token_type']
        session['refresh_token'] = token_OAuth['refresh_token']
        session['uid'] = uid
        for i in db.get('users'):
            if int(i['uid']) == int(uid):
                i['access_token'] = token_OAuth['access_token']
                i['refresh_token'] = token_OAuth['refresh_token']
                return redirect('/me')
        db["users"].append({"access_token": token_OAuth.get('access_token'), "refresh_token": token_OAuth.get("refresh_token"), "uid": uid})
        file.seek(0)
        dump(db, file, indent = 4)
        return redirect('/me')

@app.route('/beatmap/<int:bid>')
def beatmap(bid):
    return get_data(Endpoint.get_beatmap(bid), Token.get_NoOAuth())

@app.route('/bounty/<int:bid>')
def bounty(bid):
    with open('db.json', 'r+') as file:
        db = load(file)
        bounty = []
        author = []
        beatmap = []
        for i in db['bounty']:
            if i['bid'] == bid:
                author_data = get_data(Endpoint.get_user_data(i['uid']), Token.get_NoOAuth(), params={'key': 'id'})
                author.append({'avatar_url': author_data['avatar_url'], 'username': author_data['username']})
                bounty.append({'date': i['date'], 'bmode': i['bmode'], "burl": i['burl']})
                beatmap.append({'cover': f'/static/cover/{bid}.jpg'})
                author = dumps(author)
                bounty = dumps(bounty)
                beatmap = dumps(beatmap)
                return render_template('bounty.html', author=loads(author), bounty=loads(bounty), beatmap=loads(beatmap))
        return redirect("/")

@app.route('/make-bounty', methods=['GET', 'POST'])
def makebounty():
    if('access_token' in session):
        if request.method == 'POST':
            with open('db.json', 'r+') as file:
                db = load(file)
                burl = request.form['burl']
                bid = int(burl.split("#")[1].split('/')[1])
                for i in db["bounty"]:
                    if i["bid"] == bid:
                        return redirect('/make-bounty?exists=1')
                date = str(datetime.now())
                date = date.split(':')[0] + ":" + date.split(':')[1]
                uid = int(request.args.get('uid'))
                bmode = burl.split("#")[1].split('/')[0]
                beatmap_data = get_data(Endpoint.get_beatmap(bid), Token.get_NoOAuth())
                cover = {'artist': beatmap_data['beatmapset']['artist'],
                        'title': beatmap_data['beatmapset']['title'],
                        'version': beatmap_data['version'],
                        'bid': bid, 
                        'cover_url': beatmap_data['beatmapset']['covers']['cover@2x']}
                process_cover(cover)
                db["bounty"].append({"burl": burl, "bid": bid, "bmode": bmode, "uid": uid, "date": date})
                file.seek(0)
                dump(db, file, indent = 4)
            return redirect(f'/bounty/{bid}')
        if request.method == 'GET':
            if bool(request.args.get('exists')) == True:
                return render_template('make-bounty.html', uid=session['uid'], exists=True)
            return render_template('make-bounty.html', uid=session['uid'], exists=False)
    return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)