import html
import hashlib
import bcrypt
import json
from flask import Flask, make_response, request, redirect
from pymongo import MongoClient
from uuid import uuid4

mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]                                 #database                         

security_collection = db["security"]                        #collection in the database for usernames/salts/password hashes/auth hashes
post_collection = db["post"]   

#post_collection.delete_many({})                             #collection in the database for posts

app = Flask(__name__)                                       #initialise the applicaton

#security_collection.delete_many({})                        #REMOVE THIS LINE

@app.route("/")
def home():
    htmlCodeStream = open("templates/index.html", "rb").read()                  #reads index.html as bytes
    r = make_response(htmlCodeStream.decode())                                  #makes response to serve index.html
    r.headers.set("X-Content-Type-Options", "nosniff")                          #sets nosniff header
    return r

@app.route("/login.html")
def logger():
    loginPage = open("templates/login.html","rb").read()
    response = make_response(loginPage)
    response.headers.set("X-Content-Type-Options","nosniff")
    response.headers.set("Content-Type","text/html")
    return response

@app.route("/index.css")
def indexCsser():
    cssCodeStream = open("templates/index.css", "rb").read()
    r = make_response(cssCodeStream.decode())
    r.headers.set("X-Content-Type-Options", "nosniff")
    r.headers.set("Content-Type", "text/css")
    return r

@app.route("/posts.html")
def posterhtml():
    posterer = open("templates/posts.html","rb").read()
    response = make_response(posterer)
    response.headers.set("Content-Type","text/html")
    response.headers.set("X-Content-Type-Options","nosniff")
    return response

@app.route("/posts.css")
def posterthingy():
    posterer = open("templates/posts.css","rb").read()
    response = make_response(posterer)
    response.headers.set("Content-Type","text/css")
    response.headers.set("X-Content-Type-Options","nosniff")
    return response

@app.route("/finduser")
def userLocator():
    auth = request.cookies.get('auth')
    hashAuth = hashSlingingSlasher(auth)
    record = security_collection.find_one({"hashed authentication token":hashAuth})
    username = record["username"]
    response = make_response(username)
    response.headers.set("X-Content-Type-Options","nosniff")
    response.headers.set("Content-Type","text/plain")
    return response

@app.route("/functions.js")
def jsFunctions():
    jsCodeStream = open("static/functions.js", "rb").read()
    response = make_response(jsCodeStream)
    response.headers.set("X-Content-Type-Options", "nosniff")
    response.headers.set("Content-Type", "text/javascript")
    return response

@app.route("/static/about-us.jpg")
def home4():
    imageCodeStream = open("static/about-us.jpg", "rb").read()
    r = make_response(imageCodeStream)
    r.headers.set("X-Content-Type-Options", "nosniff")
    r.headers.set("Content-Type", "image/jpg")
    return r

@app.route("/background-posts.jpg")
def home5():
    imageCodeStream = open("templates/background-posts.jpg", "rb").read()
    r = make_response(imageCodeStream)
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

    registeredUsers = list(security_collection.find({'username':username}))                 #looks for the username in the database, needs to be converted to list to use
    if len(registeredUsers) != 0:                                                           #this list is always len 1, the only element is one dictionary containing each user record
        return redirect("/",301)                                                            #username is not available
    else:                                                                                   
        security_collection.insert_one({"username":username,"salt":salt,"hpw":hashPass})    #username is unique so it is inserted into the database
        return redirect("/login.html",301)                                                  #username is available

@app.route("/login", methods=['POST'])
def login():
    username = html.escape(str(request.form.get('log_username')))                           #gets username from the username textbox
    password = str(request.form.get('log_password')).encode()                               #gets password from the password textbox
    userRecord = list(security_collection.find({"username":username}))                      #looks up the username in the database and gets the unique user data
    #^converts the user record into a list with ONE dictionary containing all of the user information
    #referencing the user info will always need to be userRecord[0], this list will never be greater than size 1

    if len(userRecord) != 0:
        userInfo = userRecord[0]                                        #used to simplify notation, user information is always in index 0    
        salt = userInfo["salt"]                                         #gets salt from the database record
        realHash = userInfo["hpw"]                                      #gets the sha256 hash of the user's password from the database record
        passHash = bcrypt.hashpw(password,salt)                         #gets the sha256 hash of the ENTERED password from the textbox
        if passHash == realHash:                                        #user is logged in if both hashes match
            token = str(uuid4())                                        #generate a random token using uuid4
            tokenHash = hashSlingingSlasher(token)                      #hash this token for the database
            security_collection.update_one({"username":username,"salt":salt,"hash":realHash},{"$set":{"hashed authentication token":tokenHash}},True) #updates database to include authenticated token hash in the record
            response = make_response(redirect('/posts.html',301))       #generates response that will redirect to the posts page
            response.set_cookie("auth",token,3600,httponly=True)        #sets authentication token as a cookie
            return response
        else:
            return redirect("/login.html",301)                          #incorrect password
    else:
        return redirect("/login.html",301)                              #username not found
    
@app.route("/get_posts", methods=['GET'])
def get_posts():                                #UNTESTED (pulled from most recent push)
    posts = list(post_collection.find({}))
    for post in posts:
        post["_id"] = str(post["_id"])
    return json.dumps(posts)


@app.route("/add_post", methods=['POST'])       #stores posts in the database
def addPost():
    token_str = request.cookies.get('auth')     #token is a now a string in the database
    try:
        token = str(token_str)                  #should already be str, if None it will fail
    except TypeError:  # if None no user log in
        response = make_response("No user login", 401)
        response.headers.set("X-Content-Type-Options", "nosniff")
        response.headers.set("Content-Type", "text/plain")
        return response
    hashedToken = hashSlingingSlasher(token)            #hashes the token using sha256 (no salt)
    userData = security_collection.find_one({"hashed authentication token": hashedToken}) #gets all user information from security_collection
    if not userData:
        response = make_response("Invalid token", 401)  # un-auth
        response.headers.set("X-Content-Type-Options", "nosniff")
        response.headers.set("Content-Type", "text/plain")
        return response
    
    username = userData.get('username')                         #gets username from security_collection
    postData = request.json                                     #parses the post json data
    title = postData['title']                                   #takes the title from the post data
    message = postData['message']                               #takes the message from the post data
    post_collection.insert_one({                                #inserts the post into the database
        "title": html.escape(title),
        "message": html.escape(message),
        "username": html.escape(username),
        "mesID": str(uuid4())
    })
    response = make_response("Post Success")                    #creates success response
    response.headers.set("X-Content-Type-Options", "nosniff")   #sets nosniff header
    response.headers.set("Content-Type", "text/plain")          #sets plaintext mimetype
    return response

def hashSlingingSlasher(token):                                                 #wrapper for hashlib256
    object256 = hashlib.sha256()
    object256.update(token.encode())
    tokenHash = object256.digest()
    return(tokenHash)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)  # any time files change automatically refresh
