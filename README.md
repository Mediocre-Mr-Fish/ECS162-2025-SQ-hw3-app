# Homework 3

The New York Times front page mock-up made by Ellison Song and Sean Singleton.

Ellison Song: ellsong@ucdavis.edu

Sean Singleton: ssingleton@ucdavis.edu

SVG sources linked in HTML comments or in .svg file comments.


## Git

Repository at `https://github.com/Mediocre-Mr-Fish/ECS162-2025-SQ-hw3-app`

Commit history only covers from importing files from Homework 2.

## AI Usage

No AI was used in the production of this project.

## Notes

### Security

I have asked the TAs about login security, and they have explicitly stated that security is not an objective of this assignment. In their example, a login is handled by passing the account's email as a URL parameter. A similar method is used here.

### Article Queries

Articles fetched are, by default, filtered to the Davis/Sacramento area using NYT's tagging system. All articles included have a `Location` tag of `Davis (Calif)` or `Sacramento (Calif)`.

![Screenshot of browser console. A response JSON object is shown. Dropdowns are expanded to show more information. Under [response/docs/0/keywords/4], a JSON object associates [name:'Location'] with [value:'Sacramento (Calif)']](readme_src/location_tag.png)

When searching for articles using the search bar, this default filter is overriden.

### Sample Comments

Flask backend includes code to add sample comments to a specific article.
This can be removed or changed on line `132` of `app.py`.
```Python
addTestComments("d38b9aef-ab20-51c2-883c-94aa475b7273")
```

By default, it only adds these comments to the article "[We Mapped Heat in 3 U.S. Cities. Some Sidewalks Were Over 130 Degrees.]("https://www.nytimes.com/interactive/2024/07/17/climate/heat-map-phoenix-sacramento-portland.html")", which is the first article to appear when filtering by location.

To add sample comments to a different article, the article ID can be changed. To find the ID of an article, it can be viewed in the consle. 

![Screenshot of browser console. A response JSON object is shown. Dropdowns are expanded to show more information. Under [response/docs/0], [_id: "nyt://interactive/d38b9aef-ab20-51c2-883c-94aa475b7273"] is hovered over. [d38b9aef-ab20-51c2-883c-94aa475b7273] is highlighted.](readme_src/article_id.png)
