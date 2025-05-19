# IMPORTANT

**DOES NOT WORK IN PRODUCTION MODE**

**RUN IN DEV MODE**

`docker-compose -f docker-compose.dev.yml up --build`

# Homework 3

The New York Times front page mock-up made by Ellison Song and Sean Singleton.

Ellison Song: ellsong@ucdavis.edu

Sean Singleton: ssingleton@ucdavis.edu

SVG sources linked in HTML comments or in the .svg file itself when opened in a text editor.

## Git

Repository at [`https://github.com/Mediocre-Mr-Fish/ECS162-2025-SQ-hw3-app`](<https://github.com/Mediocre-Mr-Fish/ECS162-2025-SQ-hw3-app>).

Commit history only covers from importing files from Homework 2.

## AI Usage

No AI was used in the production of this project.

## Notes

### Comment Redaction

To redact a portion of a comment, as a moderator, press the 'Redact' button, highlight the portion of the text to redact, then press the 'Redact' button.

### Security

I have asked the TAs about login security, and they have explicitly stated that security is not an objective of this assignment.
In their example, a login is handled by redirecting with the account's email as a URL parameter.
A similar method is used here.

### Admin and Permissions

Admin accounts are not mentioned in the Homework directions.
Thus, they are treated identically to moderators here.

Account permissions are stored in the database, initialized by Flask (See [Users](#Users) below for more info) on line `238` in `app.py`:
```Python
initalizePermissionsDB()
```

Permission information is stored on lines `197` to `200` in `app.py`:

```Python
# List of users that are moderators
USERS_MODERATOR = ["admin@hw3.com", "moderator@hw3.com"]
# List of permissions
PERMISSIONS = {"can_remove_comments": USERS_MODERATOR}
```

### Users

Despite following the instructions in the discussion, a database collection for users is *not* automatically generated upon building the container.
Instead, Flask backend will generate this collection on startup.

The database that is created is named "commentsdb", with collections "comments", "users", and "permissions".
Database and collection names are defined on lines `120` to `124` in `app.py`:
```Python
# names of databases and collections
DB_COMMENTS = "commentsdb"
COL_COMMENTS = "comments"
COL_USERS = "users"
COL_PERMISSIONS = "permissions"
```

User information is stored on lines `176` to `195` in `app.py`, which is identical to the information found in `dex.yaml` and `dex_final.yaml`.
This means that the example user `alice@example.com` seen in discussion is not included.

User information collection is initialized on line `236` in `app.py`:
```Python
initalizeUsersDB()
```

### Sample Comments

The Flask backend includes code to add sample comments to a specific article.
This can be removed or changed on line `167` of `app.py`:
```Python
addTestComments("d38b9aef-ab20-51c2-883c-94aa475b7273")
```

By default, it only adds these comments to the article "[We Mapped Heat in 3 U.S. Cities. Some Sidewalks Were Over 130 Degrees.](<https://www.nytimes.com/interactive/2024/07/17/climate/heat-map-phoenix-sacramento-portland.html>)", which is the first article to appear when filtering by location.

To add sample comments to a different article, the article ID can be changed.
To find the ID of an article, it can be viewed in the console.
Only articles that have no comments can have these sample comments added.

![Screenshot of browser console. A response JSON object is shown. Dropdowns are expanded to show more information. Under [response/docs/0], [_id: "nyt://interactive/d38b9aef-ab20-51c2-883c-94aa475b7273"] is hovered over. [d38b9aef-ab20-51c2-883c-94aa475b7273] is highlighted.](readme_src/article_id.png)

### Article Queries

Articles fetched are, by default, filtered to the Davis/Sacramento area using NYT's tagging system.
All articles included have a `Location` tag of `Davis (Calif)` or `Sacramento (Calif)`.
The tags for fetched articles can be found in the console output:

![Screenshot of browser console. A response JSON object is shown. Dropdowns are expanded to show more information. Under [response/docs/0/keywords/4], a JSON object associates [name:'Location'] with [value:'Sacramento (Calif)']](readme_src/location_tag.png)

When searching for articles using the search bar, this default filter is overriden.

This differs from our Homework 2 submission, which simply defaulted to searching for "Davis" when the search bar was empty.
That approach did not fufill the localization requiremnt, and was worth no credit.
According to a TA:

> When I run your code, it appears that only articles that contain "davis" are returned. The assignment asked for stories from the Davis/Sacramento area. We are looking for articles localized in Davis/Sacramento, not articles that contain the word "Davis." 

However during Thursday office hours, when asked, a TA provided the following code:

```TypeScript
const query = 'Davis OR Sacramento';
try {
    const res = await fetch(
        `https://api.nytimes.com/svc/search/v2/articlesearch.json?q=${encodeURIComponent(query)}&api-key=${apiKey}&page=${page}`
    );
}
```

The provided code simply searches for articles that contain "Davis" or "Sacramento", which is nearly identical to the method used in Homework 2, which recieved no credit for that requirement.
Thus, we are using a different method for filtering that hopefully better fills that requirement.