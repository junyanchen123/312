import html
from flask import Flask, make_response, request, session, render_template, redirect
from pymongo import MongoClient
import bcrypt

mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]                                 #database                         

security_collection = db["security"]                        #collection in the database for usernames/passwords?
token_collection = db["token"]                              #collection in the database for ???

app = Flask(__name__)                                       #initialise the applicaton
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


@app.route("/register", methods=['POST'])
def register():
    username = html.escape(str(request.form.get('reg_username')))                           #working, gets username from request
    bPass = str(request.form.get('reg_password')).encode()                                  #password from request in bytes
    salt = bcrypt.gensalt()                                                                 #salt used to hash password (we need this later)
    hashPass = bcrypt.hashpw(bPass,salt)                                                    #salted and hashed password

    registeredUsers = list(security_collection.find({}))                                    #finds all registered users, needs to be converted to list to use
    print(registeredUsers[0])
    if registeredUsers[0].get('username') != None:                                          #this list is always len 1, the only element is one dictionary containing each user record
        print("username already in use")                                                    #maybe we can display this in the frontend at some point?
        return redirect("/")                                                                #redirects back to the login page for now :)
    else:
        print("username is available :)")
        security_collection.insert_one({"username":username,"salt":salt,"hpw":hashPass})    #username is unique so it is inserted into the database
        return redirect("/")


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
