from flask import Flask, make_response, request
from pymongo import MongoClient

app = Flask(__name__) #initialise the applicaton

@app.route("/")
def home():

    htmlCodeStream = open("index.html", "rb")

    bodystring: bytes = htmlCodeStream.read()

    htmlCodeStream.close()

    r = make_response(bodystring.decode())

    r.headers.set("X-Content-Type-Options", "nosniff")

    return r


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
        
        timesvisited = int(stringNumber) + 1       #update

    visitstring = "Times Visited: " + str(timesvisited)

    response = make_response(visitstring)

    response.set_cookie("visits",str(timesvisited), max_age = 3600)

    response.headers.set("X-Content-Type-Options", "nosniff")

    return response


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)  #any time files change automatically refresh









