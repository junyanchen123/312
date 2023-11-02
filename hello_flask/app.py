import html
import hashlib
import bcrypt
import json
import datetime
from bson.objectid import ObjectId
from flask import Flask, make_response, request, redirect, render_template
from pymongo import MongoClient
from uuid import uuid4

mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]  # database

security_collection = db["security"]  # collection in the database for usernames/salts/password hashes/auth hashes
post_collection = db["post"]
quiz_collection = db['quiz']

app = Flask(__name__)  # initialise the applicaton

# post_collection.delete_many({})                            #REMOVE THIS LINE
# security_collection.delete_many({})                        #REMOVE THIS LINE

@app.route("/")
def home():
    return htmler("templates/index.html")


@app.route("/login.html")
def logger():
    return htmler("templates/login.html")


@app.route("/index.css")
def indexCsser():
    return csser("templates/index.css")


@app.route("/posts.html")
def posterhtml():
    return htmler("templates/posts.html")


@app.route("/posts.css")
def posterthingy():
    return csser("templates/posts.css")


@app.route("/finduser")
def userLocator():
    auth = request.cookies.get('auth')          #gets auth plaintext
    username = "Guest"                          #default is guest
    if auth != None:                            #if there is an auth cookie, gets username
        hashAuth = hashSlingingSlasher(auth)    #hashes auth plaintext
        record = security_collection.find_one({"hashed authentication token": hashAuth})    #finds user record in database
        username = record["username"]           #gets username from user record
    return betterMakeResponse(username, "text/plain")


@app.route("/functions.js")
def jsFunctions():
    jsCodeStream = open("static/functions.js", "rb").read()
    return betterMakeResponse(jsCodeStream, "text/javascript")


@app.route("/background-posts.jpg")
def background():
    imageCodeStream = open("templates/background-posts.jpg", "rb").read()
    return betterMakeResponse(imageCodeStream,"image/jpg")

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


@app.route("/guest", methods=['POST'])
def guestMode():
    token_str = request.cookies.get("auth")                 #gets auth plaintext cookie
    response = make_response(redirect("/posts.html",301))   #makes redirect response object
    if token_str != None:                                   #if there is a user signed in
        response.delete_cookie("auth")                      #remove auth cookie (sign user out)
    return response                                         #return posts.html

@app.route("/register", methods=['POST'])
def register():
    username = html.escape(str(request.form.get('reg_username')))  # working, gets username from request
    bPass = str(request.form.get('reg_password')).encode()  # password from request in bytes
    salt = bcrypt.gensalt()  # salt used to hash password (we need this later)
    hashPass = bcrypt.hashpw(bPass, salt)  # salted and hashed password

    registeredUsers = list(security_collection.find(
        {'username': username}))  # looks for the username in the database, needs to be converted to list to use
    if len(registeredUsers) != 0:  # this list is always len 1, the only element is one dictionary containing each user record
        return redirect("/", 301)  # username is not available
    else:
        security_collection.insert_one({"username": username, "salt": salt,
                                        "hpw": hashPass})  # username is unique so it is inserted into the database
        return redirect("/login.html", 301)  # username is available


@app.route("/login", methods=['POST'])
def login():
    username = html.escape(str(request.form.get('log_username')))  # gets username from the username textbox
    password = str(request.form.get('log_password')).encode()  # gets password from the password textbox
    userRecord = list(security_collection.find(
        {"username": username}))  # looks up the username in the database and gets the unique user data
    # ^converts the user record into a list with ONE dictionary containing all of the user information
    # referencing the user info will always need to be userRecord[0], this list will never be greater than size 1

    if len(userRecord) != 0:
        userInfo = userRecord[0]  # used to simplify notation, user information is always in index 0
        salt = userInfo["salt"]  # gets salt from the database record
        realHash = userInfo["hpw"]  # gets the sha256 hash of the user's password from the database record
        passHash = bcrypt.hashpw(password, salt)  # gets the sha256 hash of the ENTERED password from the textbox
        if passHash == realHash:  # user is logged in if both hashes match
            token = str(uuid4())  # generate a random token using uuid4
            tokenHash = hashSlingingSlasher(token)  # hash this token for the database
            security_collection.update_one({"username": username, "salt": salt, "hash": realHash},
                                           {"$set": {"hashed authentication token": tokenHash}},
                                           True)  # updates database to include authenticated token hash in the record
            response = make_response(
                redirect('/create_quiz', 301))  # generates response that will redirect to the posts page
            response.set_cookie("auth", token, 3600, httponly=True)  # sets authentication token as a cookie
            return response
        else:
            return redirect("/login.html", 301)  # incorrect password
    else:
        return redirect("/login.html", 301)  # username not found


@app.route("/get_posts", methods=['GET'])
def get_posts():  # UNTESTED (pulled from most recent push)
    posts = list(post_collection.find({}))
    for post in posts:
        post["_id"] = str(post["_id"])
    return json.dumps(posts)


@app.route("/add_post", methods=['POST'])  # stores posts in the database
def addPost():
    token_str = request.cookies.get('auth')  # token is a now a string in the database
    try:
        token = str(token_str)  # should already be str, if None it will fail
    except TypeError:  # if None no user log in
        return betterMakeResponse("No user login", "text/plain", 401)
    hashedToken = hashSlingingSlasher(token)  # hashes the token using sha256 (no salt)
    userData = security_collection.find_one(
        {"hashed authentication token": hashedToken})  # gets all user information from security_collection
    if not userData:
        return betterMakeResponse("Invalid token", "text/plain", 401)

    username = userData.get('username')  # gets username from security_collection
    postData = request.json  # parses the post json data
    title = postData['title']  # takes the title from the post data
    message = postData['message']  # takes the message from the post data
    post_collection.insert_one({  # inserts the post into the database
        "title": html.escape(title),
        "message": html.escape(message),
        "username": html.escape(username),
        "mesID": str(uuid4()),
        "likes": str(0),
        "userswholiked": str("")  # string 'list' of users who liked the post. Initalize as empty.
    })
    return betterMakeResponse("Post Success", "text/plain")


@app.route('/like', methods=['POST'])
def like():
    token_str = request.cookies.get('auth')  # token is a now a string in the database
    try:
        token = str(token_str)  # should already be str, if None it will fail
    except TypeError:  # if None no user log in
        return betterMakeResponse("No user login", "text/plain", 401)

    hashedToken = hashSlingingSlasher(token)  # hashes the token using sha256 (no salt)
    userData = security_collection.find_one(
        {"hashed authentication token": hashedToken})  # gets all user information from security_collection
    messageID = request.json
    print(messageID)
    print(post_collection.find_one({"mesID": (messageID['postid'])}))
    post = post_collection.find_one({"mesID": (messageID['postid'])})  # post that was clicked on
    likedusers = str(post['userswholiked'])
    likedusersList = likedusers.split(",")
    likes = post.get('likes')

    if (str(userData['username']) in likedusersList) == False:  # user has not liked post
        post_collection.update_one({"mesID": messageID['postid']}, {"$set": {"likes": str((int(likes) + 1))}})
        likedusersList.append(userData['username'])
        listasString = ','.join(likedusersList)
        post_collection.update_one({"mesID": messageID['postid']}, {"$set": {"userswholiked": listasString}})
        return betterMakeResponse("User liked", "text/plain", 200)
    else:  # unlike part
        post_collection.update_one({"mesID": messageID['postid']}, {"$set": {"likes": str((int(likes) - 1))}})
        likedusersList.remove(userData['username'])
        listasString = ','.join(likedusersList)
        post_collection.update_one({"mesID": messageID['postid']}, {"$set": {"userswholiked": listasString}})
        return betterMakeResponse("User did not like", "text/plain", 200)

@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if request.method == 'POST':
        # Get quiz data from the form
        question = request.form['question']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_answer = request.form['correct_answer']

        # Save the quiz data to the MongoDB database
        quiz_data = {
            'question': question,
            'option1': option1,
            'option2': option2,
            'option3': option3,
            'option4': option4,
            'correct_answer': correct_answer
        }
        quiz_collection.insert_one(quiz_data)

        return betterMakeResponse("Create quiz successfully", "text/plain", 200)
    else:
        # If it's a get request, render the 'create_quiz.html' template
        return render_template('create_quiz.html')

@app.route('/view_quizzes', methods=['GET'])
def view_quizzes():
    quizzes = quiz_collection.find()
    return render_template('view_quizzes.html', quizzes=quizzes)

@app.route('/check_answer/<quiz_id>', methods=['POST'])
def check_answer(quiz_id):
    if request.method == 'POST':
        selected_choice = request.form['choice']

        # Retrieve the quiz from the database based on quiz_id
        quiz = quiz_collection.find_one({"_id": ObjectId(quiz_id)})

        # Check if the selected choice is the correct answer
        is_correct = (selected_choice == quiz['correct_answer'])
    
        if is_correct:
            return betterMakeResponse("Correct", "text/plain", 200)
        else:
            return betterMakeResponse("Incorrect", "text/plain", 200)

def hashSlingingSlasher(token):  # wrapper for hashlib256
    object256 = hashlib.sha256()
    object256.update(token.encode())
    tokenHash = object256.digest()
    return (tokenHash)


def htmler(filename):  # wrapper for opening html files as bytes
    file = open(filename, "rb").read()  # opens filename as bytes and reads the contents
    return betterMakeResponse(file, "text/html")  # uses betterMakeResonse wrapper to make a response


def csser(filename):  # wrapper for opening css files
    file = open(filename, "rb").read()  # opens filename as bytes and reads the contents
    return betterMakeResponse(file, "text/css")  # uses betterMakeResponse wrapper to make a response


def betterMakeResponse(file, ct, status=200):  # takes in all necessary info to make a response
    response = make_response(file, status)
    # file is either a file to send or a string to encode
    # default status is 200 unless specified otherwise
    response.headers.set("Content-Type", ct)  # sets content type header to the content type string ct
    response.headers.set("X-Content-Type-Options", "nosniff")  # sets nosniff header
    return response  # returns response object


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)  # any time files change automatically refresh
