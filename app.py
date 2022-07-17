from datetime import datetime
from json import dump, dumps, load, loads
from flask import Flask, Response, flash, render_template, redirect, request, session, url_for
from requests import post, get
from PIL import Image, ImageFont, ImageDraw, ImageFilter, ImageEnhance

app = Flask(__name__)

app.secret_key = "secret key"

API_URL = 'https://osu.ppy.sh/api/v2'
TOKEN_URL = 'https://osu.ppy.sh/oauth/token'
OAUTH_URL = 'https://osu.ppy.sh/oauth/authorize?scope=public&response_type=code&redirect_uri=https://bdb0-185-157-14-201.eu.ngrok.io/authorise&client_id=15818'

with open('db.json', 'r+') as file:
    db = load(file)
    application = {
        'client_id': db.get('application')['client_id'],
        'client_secret': db.get('application')['client_secret']
    }

class Endpoint:
    def get_user_scores_all(bid: int, user: int): return f'{API_URL}/beatmaps/{bid}/scores/users/{user}/all'
    def get_user_best_score(bid: int, user: int): return f'{API_URL}/beatmaps/{bid}/scores/users/{user}'
    def get_own_data(): return f'{API_URL}/me'
    def get_user_data(uid: int): return f'{API_URL}/users/{uid}'
    def get_beatmap(bid: int): return f'{API_URL}/beatmaps/{bid}'

class Headers:
    def headers(token):
        return {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    OAuthHeader = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
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
        'redirect_uri': 'https://bdb0-185-157-14-201.eu.ngrok.io/authorise'
    }
    def RefreshOAuth(refresh_token, access_token):
        return {
            'grant_type': "refresh_token",
            'refresh_token': refresh_token,
            'access_token': access_token,
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

    def refresh_OAuth(refresh_token, access_token):
        response = post(TOKEN_URL, data=RequestData.RefreshOAuth(refresh_token, access_token), headers=Headers.OAuthHeader)
        r = response.json()
        with open('db.json', 'r+') as file:
            db = load(file)
            for i in db.get('users'):
                if i['uid'] == session['uid']:
                    i['access_token'] = r.get('access_token')
                    i['refresh_token'] = r.get('refresh_token')
            file.seek(0)
            dump(db, file, indent = 4)
            return r

class Converter:
    def Accuracy(acc):
        if acc == 1:
            return '100%'
        acc = acc * 100
        acc = str(round(acc, 2)) + '%'
        return acc

def check_scores(bid):
    scores = []
    with open('db.json', 'r+') as file:
        db = load(file)
        for i in db.get('bounty'):
            if i['bid'] == bid:
                i=dumps(i)
                for i in loads(i).get('participants'):
                    r = get_data(Endpoint.get_user_best_score(bid, i['uid']), Token.get_NoOAuth(), params = {'mode': 'osu'}).get('score') 
                    scores.append({'accuracy': Converter.Accuracy(r['accuracy']), 'date': r['created_at'], 'score': r['score'], 'rank': r['rank'], 'uid': r['user_id'], 'username': r['user']['username'], 'perfect': r['perfect'], 'score_url': f'https://osu.ppy.sh/scores/osu/{r["best_id"]}'})
    scores = sorted(scores, key=lambda d: d['score'], reverse=True)
    return scores

def get_data(eurl, token, params=None):
    if params == None:
        response = get(f'{eurl}', headers=Headers.headers(token))
    response = get(f'{eurl}', params=params, headers=Headers.headers(token))
    return response.json()

def process_cover(cover):
    r = get(cover['banner_url'])
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
    with open('db.json', 'r+') as file:
        db = load(file)
        bounty = []
        query = request.args.get('search')
        if query != None:
            for i in db.get('bounty'):
                if query.lower() in i['artist'].lower() or query.lower() in i['tags'].lower() or query.lower() in i['version'].lower() or query.lower() in i['creator'].lower() or query.lower() in i['title'].lower() or query in str(i['bid']) or query.lower() in i['burl'].lower():
                    bounty.append(i)
        else:
            for i in db.get('bounty'):
                bounty.append(i)
        
    return render_template("index.html", bounty=loads(dumps(bounty)))

@app.route('/score')
def score():
    return get_data(Endpoint.get_user_best_score(712278, 11525785), Token.get_NoOAuth(), params = {'mode': 'osu'})

@app.route('/me')
def me():
    if('uid' in session):
        r = get_data(Endpoint.get_own_data(), session['access_token'])
        if r.get('authentication') == 'basic':
            with open('db.json', 'r+') as file:
                db = load(file)
                for i in db.get('users'):
                    if i['uid'] == session['uid']:
                        session['access_token'] = Token.refresh_OAuth(i['refresh_token'], i['access_token']).get('access_token')
        else:
            return r
    return redirect(OAUTH_URL)

@app.route('/login')
def login():
    return f'<a href="{OAUTH_URL}">Login</a>'

@app.route('/authorise')
def authorise():
    code = request.args.get('code')
    with open('db.json', 'r+') as file:
        db = load(file)
        token_OAuth = Token.get_OAuth(code)
        uid = get_data(Endpoint.get_own_data(), token_OAuth.get('access_token'))['id']
        session['access_token'] = token_OAuth['access_token']
        session['uid'] = uid
        for i in db.get('users'):
            if int(i['uid']) == int(uid):
                i['access_token'] = token_OAuth['access_token']
                i['refresh_token'] = token_OAuth['refresh_token']
                file.seek(0)
                dump(db, file, indent = 4)
                return redirect('/me')
        db["users"].append({"access_token": token_OAuth.get('access_token'), "refresh_token": token_OAuth.get("refresh_token"), "uid": uid})
        file.seek(0)
        dump(db, file, indent = 4)
        return redirect('/')

@app.route('/beatmap/<int:bid>')
def beatmap(bid):
    return get_data(Endpoint.get_beatmap(bid), Token.get_NoOAuth())

@app.route('/userscore/<int:uid>/<int:bid>')
def shit(bid, uid):
    return get_data(Endpoint.get_user_best_score(bid, uid), Token.get_NoOAuth()) 

@app.route('/bounty/<int:bid>')
def bounty(bid):
    with open('db.json', 'r+') as file:
        db = load(file)
        bounty = []
        author = []
        beatmap = []
        scores = []
        on_rankings = False
        
        action = request.args.get('accept')
        error = request.args.get('error')

        for i in db['bounty']:
            if i['bid'] == bid:
                if session['uid']:
                    participants = i.get('participants') 
                    for j in participants:
                        if j['uid'] == session['uid']:
                            on_rankings = False
                if bool(action) == True:
                    if on_rankings == False:
                        response = get_data(Endpoint.get_user_best_score(2862287, 9667334), Token.get_NoOAuth())
                        if 'error' not in response:
                            participants.append({'uid': session['uid']})
                            file.seek(0)
                            dump(db, file, indent = 4)
                            return redirect(f'/bounty/{bid}')
                        else:
                            return redirect(f'/bounty/{bid}?error=1')
                else:
                    scores = check_scores(bid)
                    author_data = get_data(Endpoint.get_user_data(i['uid']), Token.get_NoOAuth(), params={'key': 'id'})
                    author.append({'avatar_url': author_data['avatar_url'], 'username': author_data['username']})
                    bounty.append({'date': i['date'], 'bmode': i['bmode'], "burl": i['burl']})
                    beatmap.append({'cover': f'/static/cover/{bid}.jpg'})
                    return render_template('bounty.html', author=loads(dumps(author)), bounty=loads(dumps(bounty)), beatmap=loads(dumps(beatmap)), scores=loads(dumps(scores)), on_rankings=on_rankings, bid=bid, error=error)
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
                bounty = {'artist': beatmap_data['beatmapset']['artist'],
                        'title': beatmap_data['beatmapset']['title'],
                        'version': beatmap_data['version'],
                        'bid': bid, 
                        'burl': burl,
                        "bmode": bmode,
                        "uid": uid,
                        "date": date,
                        'tags': beatmap_data['beatmapset']['tags'],
                        'banner_url': beatmap_data['beatmapset']['covers']['cover@2x'],
                        'cover_url': beatmap_data['beatmapset']['covers']['list@2x'],
                        'creator': beatmap_data['beatmapset']['creator'],
                        'participants': [{'uid': uid}]
                    }
                process_cover(bounty)
                db["bounty"].append(bounty)
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