from flask import Flask, jsonify, redirect, url_for, session, request
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
import os
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = os.urandom(24)

# region Debug Output

# for ease of debugging, debug output will be written to debug_out.txt
DEBUG_FILE = "debug_out.txt"

# clear debug file in startup
with open(DEBUG_FILE, "w") as f:
    f.write("DEBUG LOG\n")


# function to write to debug file
def debug_out(message: str):
    with open(DEBUG_FILE, "a") as f:
        f.write(str(message) + "\n")


# endregion Debug Output

# code provided by starter file

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


# Wrapper object for interacting with database
class MongoWrapper:
    def __init__(self, uri):
        self.client = MongoClient(uri)

    def getDatabase(self, dbName):
        db = self.client[dbName]
        return db

    def getCollection(self, dbName, colName):
        col = self.getDatabase(dbName)[colName]
        return col

    # Insert a single document into the specified collection in the specified collection
    # The dict that is passed in will have an ObjectID added to it
    def insertDocument(self, dbName, colName, jsonObj):
        return self.getCollection(dbName, colName).insert_one(jsonObj)

    # Find a singe document in the specified collection in the specified collection
    # Returns with a the first matching document
    # A document is a match if all keys:value pairs in the query dict are present and match
    def findDocument(self, dbName, colName, jsonObj={}):
        return self.getCollection(dbName, colName).find_one(jsonObj)

    # Find all documents in the specified collection in the specified collection
    # Returns with an iterable containing matching documents
    # A document is a match if all keys:value pairs in the query dict are present and match
    def searchDocument(self, dbName, colName, jsonObj={}):
        return self.getCollection(dbName, colName).find(jsonObj)

    # Update a singe document in the specified collection in the specified collection
    # Updates with a the first matching document
    # A document is a match if all keys:value pairs in the query dict are present and match
    # All key:value pairs in the values dict will be added or override those in the document
    def updateDocument(self, dbName, colName, valuesToSet, jsonObj={}):
        update_operation = {"$set": valuesToSet}
        return self.getCollection(dbName, colName).update_one(jsonObj, update_operation)


# A class to construct the data of a comment
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

    # convert comment object to a dict/json for the database to read
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


# names of databases and collections
DB_COMMENTS = "commentsdb"
COL_COMMENTS = "comments"
COL_USERS = "users"
COL_PERMISSIONS = "permissions"

# create a wrapper object using the URI
mongo = MongoWrapper(os.getenv("MONGO_URI"))


# Function to insert a sample comment and a sample reply to an article
# ONLY IF it does not have any comments yet.
def addTestComments(articleID):
    # check if any documents (comments) exist
    exists = False
    for c in mongo.searchDocument(DB_COMMENTS, COL_COMMENTS, {"articleID": articleID}):
        exists = True
        break
    # if not, create them
    if not exists:
        # create and push a sample comment
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
        # create and push a sample reply
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


# Add sample comments to articles. More information can be found in README.md
addTestComments("d38b9aef-ab20-51c2-883c-94aa475b7273")

# print all comments
for c in mongo.searchDocument(DB_COMMENTS, COL_COMMENTS):
    debug_out(dict(c))

# User information for database.
# Identical to the information found in `dex.yaml` and `dex_final.yaml`.
# More information can be found in README.md
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

# List of users that are moderators
USERS_MODERATOR = ["admin@hw3.com", "moderator@hw3.com"]
# List of permissions
PERMISSIONS = {"can_remove_comments": USERS_MODERATOR}

# Message that replaces a removed comment
COMMENT_REMOVAL_MESSAGE = "COMMENT REMOVED BY MODERATOR!"
# Character that replaces redacted sections
COMMENT_REDACTION_CHAR = "█"


# Function to initialize the Users collection
def initalizeUsersDB():
    # check if any documents exist
    exists = False
    for c in mongo.searchDocument(DB_COMMENTS, COL_USERS):
        exists = True
        break
    # if not, create them
    if not exists:
        debug_out("Creating Users DB")
        for u in USERS_REGISTERED:
            mongo.insertDocument(DB_COMMENTS, COL_USERS, u)


# Function to initialize the permissions collection
def initalizePermissionsDB():
    # check if any documents exist
    exists = False
    for c in mongo.searchDocument(DB_COMMENTS, COL_PERMISSIONS):
        exists = True
        break
    # if not, create them
    if not exists:
        debug_out("Creating Permissions DB")
        mongo.insertDocument(DB_COMMENTS, COL_PERMISSIONS, PERMISSIONS)


# initialize the Users collection
initalizeUsersDB()
# initialize the Permissions collection
initalizePermissionsDB()


# region NYT API Calls


# Route to return the API key
# Depricated: frontend does not need the key
# All API fetches should be done though the below routes
# @app.route('/api/key')
# def get_key():
#     return jsonify({'apiKey': os.getenv('NYT_API_KEY')})


# Route to search for articles via query
@app.route("/api/articles-query/<int:page>/<string:query>")
def fetch_article_query(page: int, query: str):
    # get key
    key = os.getenv("NYT_API_KEY")
    # call api
    return redirect(
        f"https://api.nytimes.com/svc/search/v2/articlesearch.json?q={query}&api-key={key}&page={page}",
        code=302,
    )


# Route to search for articles via filter
@app.route("/api/articles-filter/<int:page>/<string:filter>")
def fetch_article_filter(page: int, filter: str):
    # get key
    key = os.getenv("NYT_API_KEY")
    # format filter
    filter = filter.replace(":", "%3A")
    # call api
    return redirect(
        f"https://api.nytimes.com/svc/search/v2/articlesearch.json?fq={filter}&api-key={key}&page={page}",
        code=302,
    )


# endregion NYT API Calls


# region Comments Database CRUD operations


# route to get all comments for an article
@app.route("/api/comments/<string:articleid>")
def getComments(articleid: str):
    try:
        comments = {}
        queued = {}

        # search for all documents (comments) that match article ID
        for c in list(
            mongo.searchDocument(DB_COMMENTS, COL_COMMENTS, {"articleID": articleid})
        ):
            # Convert to dictionary
            d = dict(c)
            # convert ObjectID to string
            _id = str(d["_id"])
            d["_id"] = _id
            # if this is a reply, add it to the replies queue
            if d["parentID"]:
                queued[_id] = d
            else:
                comments[_id] = d

        # for all queued replies
        for _id, d in queued.items():
            # add it to the replies list for its parent comment
            pid = d["parentID"]
            comments[pid]["replies"].append(d)

        # convert dictionary to list
        comments_list = list(comments.values())
        # show in reverse chronological order
        comments_list.reverse()
        return jsonify({"comments": comments_list})
    except Exception as e:
        return jsonify({"Internal error": str(e)})


# Route to post a comment via POST method
# Requires the poster's email,
# the article ID,
# the parent comment (for replies) or an empty string (for comments),
# and the comment's content
# Adds the comment to the database and returns the newly formed comment as JSON
@app.route("/api/postcomment", methods=["POST"])
def postComment():
    try:
        data = request.form
        debug_out("Posting Comment")
        debug_out(data)

        # use email as username fallback
        username = data["email"]
        # search all users documents for a matching email
        for u in mongo.searchDocument(DB_COMMENTS, COL_USERS, {"email": data["email"]}):
            # retrieve their username
            username = u["username"]

        parentID = data["parentID"]
        # if parentID is an empty string, change it to null
        if not parentID:
            parentID = None

        # Create comment object
        commentData = Comment(
            username=username,
            useremail=data["email"],
            content=data["content"],
            articleID=data["articleID"],
            parentID=parentID,
        ).toJson()

        # push to database
        mongo.insertDocument(
            DB_COMMENTS,
            COL_COMMENTS,
            commentData,
        )

        # convert ObjectID to string and return the new comment's parsed data
        commentData["_id"] = str(commentData["_id"])
        debug_out(commentData)
        return jsonify({"status": "ok", "commentData": commentData})
    except Exception as e:
        raise e
        return jsonify({"Internal error": str(e)})


# Route to remove a comment via POST method
# Requires a comment ID
# Replaces the content of the specified comment in the database with a removal message
# and returns the modified comment as JSON
@app.route("/api/removecomment", methods=["POST"])
def removeComment():
    try:
        data = request.form
        debug_out("Removing Comment")
        debug_out(data)

        # replace comment content with removal message
        # flag comment as removed
        replaceData = {"content": COMMENT_REMOVAL_MESSAGE, "removed": True}
        # push changes to database
        mongo.updateDocument(
            DB_COMMENTS,
            COL_COMMENTS,
            replaceData.copy(),
            {"_id": ObjectId(data["commentID"])},  # convert string to ObjectID
        )

        # return the modified comment data
        return jsonify({"status": "ok", "commentData": replaceData})
    except Exception as e:
        raise e
        return jsonify({"Internal error": str(e)})


# Route to redact part of a comment via POST method
# Requires a comment ID, a start index, and end index
# Replaces the specified slice of the specified comment in the database with redacted characters
# and returns the modified comment as JSON
@app.route("/api/redactcomment", methods=["POST"])
def redactComment():
    try:
        data = request.form
        debug_out("Redacting Comment")
        debug_out(data)

        # convert string to ObjectID and use it to search the database
        oid = ObjectId(data["commentID"])
        content = mongo.findDocument(DB_COMMENTS, COL_COMMENTS, {"_id": oid})["content"]

        startIndex = int(data["startIndex"])
        endIndex = int(data["endIndex"])

        # replace a slice of the comment with redacted characters
        cHead = content[:startIndex]
        cRedact = COMMENT_REDACTION_CHAR * (endIndex - startIndex)
        cTail = content[endIndex:]

        # replace comment content with spliced content
        replaceData = {"content": cHead + cRedact + cTail}
        # push changes to database
        mongo.updateDocument(
            DB_COMMENTS,
            COL_COMMENTS,
            replaceData.copy(),
            {"_id": oid},
        )

        # return the modified comment data
        return jsonify({"status": "ok", "commentData": replaceData})
    except Exception as e:
        raise e
        return jsonify({"Internal error": str(e)})


# Route to check permissions of a user
# Returns a JSON object
# All existing permissions are included as keys,
# with the given user's permissions having a value of true
@app.route("/api/checkpermissions/<string:email>")
def checkPermissions(email: str):
    perms = {}
    # search all documents in the permissions collection
    for perm_doc in mongo.searchDocument(DB_COMMENTS, COL_PERMISSIONS):
        # convert to dict
        d = dict(perm_doc)
        for k, v in d.items():
            # each key in this doc is either the name of a permission or "_id"
            if k != "_id":
                # if this permission hasn't been seen yet, add it to the return object
                # this way, all permissions that exist will be part of the return object
                if k not in perms:
                    perms[k] = False
                # if this user has this permission, flag it as true
                if email in v:
                    perms[k] = True
    return jsonify(perms)


# endregion Comments Database CRUD operations


# region Authentication


# I have asked the TAs about login security, and they have explicitly stated that security is not an objective of this assignment.
# In their example, a login is handled by redirecting with the account's email as a URL parameter.
# A similar method is used here.
# Provided by starter code, except return statements are modified.
@app.route("/")
def home():
    user = session.get("user")
    if user:
        # return f"<h2>Logged in as {user['email']}</h2><a href='/logout'>Logout</a>"
        return redirect(f"http://localhost:5173/?email={user['email']}")
    # return '<a href="/login">Login with Dex</a>'
    return redirect(f"http://localhost:5173")


# Provided by starter code
@app.route("/login")
def login():
    session["nonce"] = nonce
    redirect_uri = "http://localhost:8000/authorize"
    return oauth.flask_app.authorize_redirect(redirect_uri, nonce=nonce)


# Provided by starter code
@app.route("/authorize")
def authorize():
    token = oauth.flask_app.authorize_access_token()
    nonce = session.get("nonce")

    user_info = oauth.flask_app.parse_id_token(
        token, nonce=nonce
    )  # or use .get('userinfo').json()
    session["user"] = user_info
    return redirect("/")


# Provided by starter code
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# endregion Authentication

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
