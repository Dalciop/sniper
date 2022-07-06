from json import dump, load
from flask import Flask, Response, render_template, redirect, request, session
from requests import post, get

app = Flask(__name__)

app.secret_key = "secret key"

API_URL = 'https://osu.ppy.sh/api/v2'
TOKEN_URL = 'https://osu.ppy.sh/oauth/token'

with open('db.json', 'r+') as file:
    db = load(file)
    application = {
        'client_id': db.get('application')['client_id'],
        'client_secret': db.get('application')['client_secret']
    }

class Endpoint:
    def get_user_scores_all(bid: int, user: int): return f'/beatmaps/{bid}/scores/users/{user}/all'

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
        'client_id': 15818,
        'client_secret': '4XmFzV8FAfP8o9jIQs8asXsP8EOHdLZ6cFuZnHvz',
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': 'http://127.0.0.1/authorise'
    }

def get_token_NoOAuth():
    response = post(TOKEN_URL, data=RequestData.NoOAuthData)

    return response.json().get('access_token')

def get_token_OAuth(code):
    response = post(TOKEN_URL, data=RequestData.OAuthData(code))

    return response.json()

def get_data(eurl, token):
    params = {
        'mode': 'osu'
    }
    
    response = get(f'{API_URL}{eurl}', params=params, headers=Headers.headers(token))

    return response.json()

def get_own_data(token):
    response = get(f'{API_URL}/me/', headers=Headers.headers(token))
    return response.json()

@app.route('/')
def index():
    return get_data(Endpoint.get_user_scores_all(712278, 11525785), get_token_NoOAuth())
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
        return get_own_data(OAuthToken['access_token'])
    return redirect('/')

@app.route('/authorise')
def authorise():
    code = request.args.get('code')
    with open('db.json', 'r+') as file:
        db = load(file)
        token_OAuth = get_token_OAuth(code)
        session['access_token'] = token_OAuth['access_token']
        session['expires_in'] = token_OAuth['expires_in']
        session['token_type'] = token_OAuth['token_type']
        session['refresh_token'] = token_OAuth['refresh_token']
        userid = get_own_data(token_OAuth.get('access_token'))['id']
        for i in db.get('users'):
            if int(i['userid']) == int(userid):
                i['access_token'] = token_OAuth['access_token']
                i['refresh_token'] = token_OAuth['refresh_token']
                return redirect('/me')
        db["users"].append({"access_token": token_OAuth.get('access_token'), "refresh_token": token_OAuth.get("refresh_token"), "userid": userid})
        file.seek(0)
        dump(db, file, indent = 4)
        return redirect('/me')

@app.route('/bounty')
def bounty():
    code = request.args.get('code')
    return get_data(Endpoint.get_user_scores_all(712278, 11525785), get_token_OAuth(code).get('access_token'))

# @app.route('/make-bounty', methods=['POST'])
# def makebounty():

#     return Response(status=200)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)