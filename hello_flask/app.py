import html
from flask import Flask, make_response, request, session, render_template
from pymongo import MongoClient
import bcrypt

mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]

security_collection = db["security"]
token_collection = db["token"]

app = Flask(__name__)  # initialise the applicaton
app.secret_key = "super secret key"


@app.route("/")
def home():
    htmlCodeStream = open("templates/index.html", "rb")

    bodystring: bytes = htmlCodeStream.read()

    htmlCodeStream.close()

    r = make_response(bodystring.decode())

    r.headers.set("X-Content-Type-Options", "nosniff")

    return render_template('index.html',username = session.get('username'))


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


@app.route("/visit-counter/")
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


@app.route("/register", methods=['POST'])
def register():
    # i did str on the request form data since I dont know what type original data is. Probably JSON
    username = html.escape(str(request.form.get('reg_username')))

    password = str(request.form.get('reg_password'))  # un-hashed/salted password
    passwordInBytes = password.encode('utf-8')
    saltedandHashed = bcrypt.hashpw(bytes, bcrypt.gensalt())

    flag = True  # flag is true if user and pass are unique

    # below is to check if the user and pass are unique
    for x in security_collection.find():
        databaseUsername = x["username"]
        databasePassword = x["password"]
        if (username == databaseUsername or bcrypt.checkpw(passwordInBytes,databasePassword)):
            flag = False

    if flag == True:
        # add new user to the database with html escaped user and salted pass
        # html escape username here
        security_collection.insert_one({"username": (html.escape(username)), "password": saltedandHashed})

        # Below code should load a page with text saying that registering was sucessful
        bodystring = username + " has been registered."
        r = make_response(bodystring)

        r.headers.set("X-Content-Type-Options", "nosniff")
        r.headers.set("Content-Type", "text/plain")

        return r

    else:
        # passing this means either username or password exists in the database
        bodystring = "Invalid registration. Must be unique username and password"
        r = make_response(bodystring)

        r.headers.set("X-Content-Type-Options", "nosniff")
        r.headers.set("Content-Type", "text/plain")

        return r


@app.route("/login", methods=['POST'])
def login():
    # i did str on the request form data since I dont know what type original data is. Probably JSON
    username = html.escape(str(request.form.get('log_username')))

    userornah = False  # false if not user. True if user.

    password = str(request.form.get('log_password'))  # un-hashed/salted password

    passwordInBytes = password.encode('utf-8')
    
    for x in security_collection.find():
        databaseUsername = x["username"]
        databasePassword = x["password"]
        if (username == databaseUsername and bcrypt.checkpw(passwordInBytes,databasePassword)):
            userornah = True
            session['username'] = username
            session['logged_in'] = True

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
