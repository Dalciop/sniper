import requests
from pprint import pprint

API_URL = 'https://osu.ppy.sh/api/v2'
TOKEN_URL = 'https://osu.ppy.sh/oauth/token'

def get_token():
    data = {
        'client_id': 15818,
        'client_secret': '4XmFzV8FAfP8o9jIQs8asXsP8EOHdLZ6cFuZnHvz',
        'grant_type': 'client_credentials',
        'scope': 'public'
    }

    response = requests.post(TOKEN_URL, data=data)

    return response.json().get('access_token')

def main():
    token = get_token()

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    params = {
        'mode': 'osu',
    }

    response = requests.get(f'{API_URL}/beatmaps/712278/scores/users/11525785/all', params=params, headers=headers)
    
    # beatmapset_data = response.json()[0].get('beatmapset')
    beatmapset_data = response.json()

    pprint(beatmapset_data, indent=2)


if __name__ == '__main__':
    main()