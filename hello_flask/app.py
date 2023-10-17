import html
import json

from flask import Flask, make_response, request, session, render_template, redirect
from pymongo import MongoClient
import bcrypt
import uuid

mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]  # database

security_collection = db["security"]  # collection in the database for usernames/passwords?
token_collection = db["token"]  # collection in the database for ???
post_collection = db["post"]  #

app = Flask(__name__)  # initialise the applicaton
app.secret_key = "super secret key"


@app.route("/")
def home():
    htmlCodeStream = open("templates/index.html", "rb")

    bodystring: bytes = htmlCodeStream.read()

    htmlCodeStream.close()

    r = make_response(bodystring.decode())

    r.headers.set("X-Content-Type-Options", "nosniff")

    all_posts = list(post_collection.find({}))  # get post from db send to the home page

    return render_template('index.html', username=session.get('username'), posts=all_posts)


@app.route("/static/style.css")
def home2():
    cssCodeStream = open("static/style.css", "rb")

    bodystring: bytes = cssCodeStream.read()

    cssCodeStream.close()

    r = make_response(bodystring.decode())

    r.headers.set("X-Content-Type-Options", "nosniff")
    r.headers.set("Content-Type", "text/css")

    return r


@app.route("/static/functions.js")
def home3():
    jsCodeStream = open("static/functions.js", "rb")

    bodystring: bytes = jsCodeStream.read()

    jsCodeStream.close()

    r = make_response(bodystring.decode())

    r.headers.set("X-Content-Type-Options", "nosniff")
    r.headers.set("Content-Type", "text/javascript")

    return r


@app.route("/static/about-us.jpg")
def home4():
    imageCodeStream = open("static/about-us.jpg", "rb")

    bodystring: bytes = imageCodeStream.read()

    imageCodeStream.close()

    r = make_response(bodystring)

    r.headers.set("X-Content-Type-Options", "nosniff")
    r.headers.set("Content-Type", "image/jpg")

    return r


@app.route("/visit-counter")
def cookie():
    timesvisited = 1

    if "visits" in request.cookies:
        stringNumber = request.cookies.get("visits")

        timesvisited = int(stringNumber) + 1  # update

    visitstring = "Times Visited: " + str(timesvisited)

    response = make_response(visitstring)

    response.set_cookie("visits", str(timesvisited), max_age=3600)

    response.headers.set("X-Content-Type-Options", "nosniff")

    return response


@app.route("/get_posts", methods=['GET'])
def get_posts():
    posts = list(post_collection.find({}))
    for post in posts:
        post["_id"] = str(post["_id"])
    return json.dumps(posts)


@app.route("/add_post", methods=['POST'])
def addPost():
    token_str = request.cookies.get('token')
    # token store in cookie is String, change it to int(in db is int)
    try:
        token = int(token_str)
    except TypeError:  # if None no user log in
        response = make_response("No user login", 400)
        response.headers.set("X-Content-Type-Options", "nosniff")
        response.headers.set("Content-Type", "text/plain")
        return response

    userData = token_collection.find_one({"token": token})
    if not userData:
        response = make_response("Invalid token", 401)  # un-auth
        response.headers.set("X-Content-Type-Options", "nosniff")
        response.headers.set("Content-Type", "text/plain")
        return response

    username = userData.get('username')

    title = request.form.get('post_title')
    description = request.form.get('post_description')

    post_collection.insert_one({
        "title": html.escape(title),
        "description": html.escape(description),
        "username": html.escape(username),
        "mesID": str(uuid.uuid4())
    })

    response = make_response("Post Success")
    response.headers.set("X-Content-Type-Options", "nosniff")
    response.headers.set("Content-Type", "text/plain")
    return response


@app.route("/register", methods=['POST'])
def register():
    username = html.escape(str(request.form.get('reg_username')))
    bPass = str(request.form.get('reg_password')).encode()
    salt = bcrypt.gensalt()
    hashPass = bcrypt.hashpw(bPass, salt)

    uniqueUser = True

    for x in security_collection.find():
        databaseUser = x["username"]
        if databaseUser == username:
            uniqueUser = False

    if (not uniqueUser):
        bodystring = "Invalid register. Must be unique"

        response = make_response(bodystring)

        response.headers.set("X-Content-Type-Options", "nosniff")
        response.headers.set("Content-Type", "text/plain")
        return response
    if (uniqueUser):
        security_collection.insert_one({"username": username, "salt": salt, "hpw": hashPass})
        bodystring = username + " has been registered"

        response = make_response(bodystring)

        response.headers.set("X-Content-Type-Options", "nosniff")
        response.headers.set("Content-Type", "text/plain")

        return response


@app.route("/login", methods=['POST'])
def login():
    # i did str on the request form data since I dont know what type original data is. Probably JSON
    username = html.escape(str(request.form.get('log_username')))

    userornah = False  # false if not user. True if user.

    password = str(request.form.get('log_password'))  # un-hashed/salted password

    passwordInBytes = password.encode('utf-8')

    for x in security_collection.find():
        databaseUsername = x["username"]

        databasePassword = x["hpw"]

        databaseSalt = x["salt"]
        if (username == databaseUsername and bcrypt.hashpw(passwordInBytes, databaseSalt) == databasePassword):
            userornah = True

    if userornah:
        # set the token and put it in the token_collection part of the DB

        randomTokenString = bcrypt.gensalt()  # just a random string
        randomHashedTokenString = hash(randomTokenString)
        token_collection.insert_one({"username": (html.escape(username)), "token": randomHashedTokenString})

        bodystring = username + " has been logged in"

        response = make_response(bodystring)

        response.headers.set("X-Content-Type-Options", "nosniff")
        response.headers.set("Content-Type", "text/plain")
        response.set_cookie("token", str(randomHashedTokenString), max_age=3600, httponly=True)
        return response


    else:
        # Invalid login. Just let them know, no token here.
        bodystring = "Invalid login. Try again"

        response = make_response(bodystring)

        response.headers.set("X-Content-Type-Options", "nosniff")
        response.headers.set("Content-Type", "text/plain")

        return response


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)  # any time files change automatically refresh
