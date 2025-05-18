import app
import os
from dotenv import load_dotenv

load_dotenv()

def getKeyFromFile():
    envfile = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..",".env")
    with open(envfile, "r") as f:
        s = f.read()
        s = s.splitlines()[0]
        s = s[len("NYT_API_KEY="):]
        return s

def test_fetchKey():
    with app.app.app_context():
        assert app.get_key().get_json()["apiKey"] == getKeyFromFile()

#python -m pytest