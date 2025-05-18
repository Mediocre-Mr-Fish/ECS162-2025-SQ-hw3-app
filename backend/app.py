from flask import Flask, jsonify, redirect, url_for, session, request
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
import os
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = os.urandom(24)

with open("debug_out.txt", "w") as f:
    f.write("DEBUG LOG\n")


def debug_out(message: str):
    with open("debug_out.txt", "a") as f:
        f.write(str(message) + "\n")


oauth = OAuth(app)

nonce = generate_token()


oauth.register(
    name=os.getenv("OIDC_CLIENT_NAME"),
    client_id=os.getenv("OIDC_CLIENT_ID"),
    client_secret=os.getenv("OIDC_CLIENT_SECRET"),
    # server_metadata_url='http://dex:5556/.well-known/openid-configuration',
    authorization_endpoint="http://localhost:5556/auth",
    token_endpoint="http://dex:5556/token",
    jwks_uri="http://dex:5556/keys",
    userinfo_endpoint="http://dex:5556/userinfo",
    device_authorization_endpoint="http://dex:5556/device/code",
    client_kwargs={"scope": "openid email profile"},
)


class MongoWrapper:
    def __init__(self, uri):
        self.client = MongoClient(uri)

    def getDatabase(self, dbName):
        db = self.client[dbName]
        return db

    def getCollection(self, dbName, colName):
        col = self.getDatabase(dbName)[colName]
        return col

    def insertDocument(self, dbName, colName, jsonObj):
        return self.getCollection(dbName, colName).insert_one(jsonObj)

    def findDocument(self, dbName, colName, jsonObj={}):
        return self.getCollection(dbName, colName).find_one(jsonObj)

    def searchDocument(self, dbName, colName, jsonObj={}):
        return self.getCollection(dbName, colName).find(jsonObj)

    def updateDocument(self, dbName, colName, valuesToSet, jsonObj={}):
        update_operation = {"$set": valuesToSet}
        return self.getCollection(dbName, colName).update_one(jsonObj, update_operation)


class Comment:
    def __init__(
        self,
        username: str,
        useremail: str,
        content: str,
        articleID: str,
        parentID: str = None,
        removed: bool = False,
    ):
        self.articleID: str = articleID
        self.parentID: str = parentID
        self.username: str = username
        self.useremail: str = useremail
        self.content: str = content
        self.removed: str = removed

    def toJson(self):
        return {
            "articleID": self.articleID,
            "parentID": self.parentID,
            "username": self.username,
            "useremail": self.useremail,
            "content": self.content,
            "removed": self.removed,
            "replies": [],
        }


DB_COMMENTS = "commentsdb"
COL_COMMENTS = "comments"
COL_USERS = "users"
COL_PERMISSIONS = "permissions"

mongo = MongoWrapper(os.getenv("MONGO_URI"))


def addTestComments(articleID):
    exists = False
    for c in mongo.searchDocument(DB_COMMENTS, COL_COMMENTS, {"articleID": articleID}):
        exists = True
        break
    if not exists:
        test_comment_id = mongo.insertDocument(
            DB_COMMENTS,
            COL_COMMENTS,
            Comment(
                "Some User",
                "someuser@mail",
                "Hello World!",
                articleID,
            ).toJson(),
        )
        # debug_out(test_comment_id.inserted_id)
        test_reply_id = mongo.insertDocument(
            DB_COMMENTS,
            COL_COMMENTS,
            Comment(
                "Other User",
                "otheruser@mail",
                "Hello to you too!",
                articleID,
                str(test_comment_id.inserted_id),
            ).toJson(),
        )


addTestComments("d38b9aef-ab20-51c2-883c-94aa475b7273")
for c in mongo.searchDocument(DB_COMMENTS, COL_COMMENTS):
    debug_out(dict(c))

USERS_REGISTERED = [
    {
        "email": "admin@hw3.com",
        "hash": "$2b$10$8NoCpIs/Z6v0s/pU9YxYIO10uWyhIVOS2kmNac9AD0HsqRhP5dUie",
        "username": "admin",
        "userID": "123",
    },
    {
        "email": "moderator@hw3.com",
        "hash": "$2b$12$2aaoZyVjMWvoCq.DmCUECOGoW0oaBCyzSluUm3BpLrP26sVT71PSC",
        "username": "moderator",
        "userID": "456",
    },
    {
        "email": "user@hw3.com",
        "hash": "$2b$12$321HomfT164U9f5l.xQaYuHThGCss8PRPNy8t./tq8Frgr6UYeEka",
        "username": "user",
        "userID": "789",
    },
]
USERS_MODERATOR = ["admin@hw3.com", "moderator@hw3.com"]
PERMISSIONS = {"can_remove_comments": USERS_MODERATOR}


def initalizeUsersDB():
    exists = False
    for c in mongo.searchDocument(DB_COMMENTS, COL_USERS):
        exists = True
        break
    if not exists:
        debug_out("Creating Users DB")
        for u in USERS_REGISTERED:
            mongo.insertDocument(DB_COMMENTS, COL_USERS, u)
        mongo.insertDocument(DB_COMMENTS, COL_PERMISSIONS, PERMISSIONS)


initalizeUsersDB()

# @app.route('/api/key')
# def get_key():
#     return jsonify({'apiKey': os.getenv('NYT_API_KEY')})


@app.route("/api/articles-query/<int:page>/<string:query>")
def fetch_article_query(page: int, query: str):
    key = os.getenv("NYT_API_KEY")
    return redirect(
        f"https://api.nytimes.com/svc/search/v2/articlesearch.json?q={query}&api-key={key}&page={page}",
        code=302,
    )


@app.route("/api/articles-filter/<int:page>/<string:filter>")
def fetch_article_filter(page: int, filter: str):
    key = os.getenv("NYT_API_KEY")
    filter = filter.replace(":", "%3A")
    return redirect(
        f"https://api.nytimes.com/svc/search/v2/articlesearch.json?fq={filter}&api-key={key}&page={page}",
        code=302,
    )


@app.route("/api/comments/<string:articleid>")
def getComments(articleid: str):
    try:
        comments = {}
        queued = {}
        for c in list(
            mongo.searchDocument(DB_COMMENTS, COL_COMMENTS, {"articleID": articleid})
        ):
            d = dict(c)
            _id = str(d["_id"])
            d["_id"] = _id
            if d["parentID"]:
                queued[_id] = d
            else:
                comments[_id] = d

        for _id, d in queued.items():
            pid = d["parentID"]
            comments[pid]["replies"].append(d)

        comments_list = list(comments.values())
        comments_list.reverse()
        return jsonify({"comments": comments_list})
    except Exception as e:
        return jsonify({"Internal error": str(e)})


@app.route("/api/postcomment", methods=["POST"])
def postComment():
    try:
        data = request.form
        debug_out("Posting Comment")
        debug_out(data)

        username = None
        for u in mongo.searchDocument(DB_COMMENTS, COL_USERS, {"email": data["email"]}):
            username = u["username"]

        parentID = data["parentID"]
        if not parentID:
            parentID = None

        commentData = Comment(
            username=username,
            useremail=data["email"],
            content=data["content"],
            articleID=data["articleID"],
            parentID=parentID,
        ).toJson()

        mongo.insertDocument(
            DB_COMMENTS,
            COL_COMMENTS,
            commentData,
        )

        commentData["_id"] = str(commentData["_id"])
        debug_out(commentData)
        return jsonify({"status": "ok", "commentData": commentData})
    except Exception as e:
        raise e
        return jsonify({"Internal error": str(e)})


COMMENT_REMOVAL_MESSAGE = "COMMENT REMOVED BY MODERATOR!"
COMMENT_REDACTION_CHAR = "█"


@app.route("/api/removecomment", methods=["POST"])
def removeComment():
    try:
        data = request.form
        debug_out("Removing Comment")
        debug_out(data)

        replaceData = {"content": COMMENT_REMOVAL_MESSAGE, "removed": True}
        mongo.updateDocument(
            DB_COMMENTS,
            COL_COMMENTS,
            replaceData.copy(),
            {"_id": ObjectId(data["commentID"])},
        )
        return jsonify({"status": "ok", "commentData": replaceData})
    except Exception as e:
        raise e
        return jsonify({"Internal error": str(e)})


@app.route("/api/redactcomment", methods=["POST"])
def redactComment():
    try:
        data = request.form
        debug_out("Redacting Comment")
        debug_out(data)
        oid = ObjectId(data["commentID"])
        content = mongo.findDocument(DB_COMMENTS, COL_COMMENTS, {"_id": oid})["content"]

        startIndex = int(data["startIndex"] )
        endIndex = int(data["endIndex"] )

        cHead = content[:startIndex]
        cRedact = COMMENT_REDACTION_CHAR * (endIndex - startIndex)
        cTail = content[endIndex:]

        replaceData = {"content": cHead + cRedact + cTail}
        mongo.updateDocument(
            DB_COMMENTS,
            COL_COMMENTS,
            replaceData.copy(),
            {"_id": oid},
        )
        return jsonify({"status": "ok", "commentData": replaceData})
    except Exception as e:
        raise e
        return jsonify({"Internal error": str(e)})


@app.route("/api/checkpermissions/<string:email>")
def checkPermissions(email: str):
    perms = {}
    for perm_doc in mongo.searchDocument(DB_COMMENTS, COL_PERMISSIONS):
        d = dict(perm_doc)
        for k, v in d.items():
            if k != "_id":
                if k not in perms:
                    perms[k] = False
                if email in v:
                    perms[k] = True
    return jsonify(perms)


@app.route("/")
def home():
    user = session.get("user")
    if user:
        # return f"<h2>Logged in as {user['email']}</h2><a href='/logout'>Logout</a>"
        return redirect(f"http://localhost:5173/?email={user['email']}")
    # return '<a href="/login">Login with Dex</a>'
    return redirect(f"http://localhost:5173")


@app.route("/login")
def login():
    session["nonce"] = nonce
    redirect_uri = "http://localhost:8000/authorize"
    return oauth.flask_app.authorize_redirect(redirect_uri, nonce=nonce)


@app.route("/authorize")
def authorize():
    token = oauth.flask_app.authorize_access_token()
    nonce = session.get("nonce")

    user_info = oauth.flask_app.parse_id_token(
        token, nonce=nonce
    )  # or use .get('userinfo').json()
    session["user"] = user_info
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
