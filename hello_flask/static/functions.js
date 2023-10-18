function user(){                                                    //gets the username for the frontend display
    const request = new XMLHttpRequest();                           //generates an XMLHttpRequest for later use
    request.onreadystatechange = function() {                       
        if(this.readyState === 4 && this.status === 200){           //when a 200 response is received resume here
            var username = this.response;                           //gets username from python response
            var uPostField = document.getElementById("username");   //gets the post field that normally would say "username"
            var uHead = document.getElementById("uHeader");         //gets the post field that normally would say "username's Feed"
            uHead.innerHTML = (username + "'s Feed");               //updates username frontend
            uPostField.innerHTML = username;                        //updates username frontend
        }
    }
    request.open("GET","/finduser");
    request.send();
}

function updatePosts() {  //TODO adapt this function for new frontend
    const request = new XMLHttpRequest();
    request.onreadystatechange = function() {
        if (request.readyState === 4 && request.status === 200) {
            const data = JSON.parse(request.responseText);
            const postsSection = document.querySelector('.posts-section');
            let posts = '<h3>Posts RIGHT HERE!</h3>';
            data.forEach(post => {
                posts += `
                <div class="post">
                    <h3>${post.title}</h3>
                    <p>${post.description}</p>
                    <small>Posted by: ${post.username}</small>
                </div>`;
            });
            postsSection.innerHTML = posts;
        }
    };
    request.open("GET", "/get_posts");
    request.send();
}

function post(){                    //christian is working on this
    const titleTextBox = document.getElementById("titleBox");       //gets title of posts from the frontend
    const title = titleTextBox.value;                               //actual text from the title box in frontend
    const messageTextBox = document.getElementById("messageBox");   //gets message from post from the frontend
    const message = messageTextBox.value;                           //actual text from the message box 
    titleTextBox.value = "";                                        //resets the frontend to show a blank title box
    messageTextBox.value = "";                                      //resets the frontend to show a blank message box
    const request = new XMLHttpRequest();                           //generates an XMLHttpRequest for later use
    request.onreadystatechange = function(){                        //when a 200 response is received, resumes function here
        if(request.readyState === 4 && request.status === 200){
            console.log(this.response);                             //placeholder for now
        }
    }
    const postInfo = {"title":title,"message":message};             //creates a dictionary to hold the title and message from the frontend
    request.open("POST","/add_post");                               //prepares request to send to python
    request.setRequestHeader("Content-Type","application/json;charset=utf-8");
    request.send(JSON.stringify(postInfo));                         //sends jsonified dictionary with post content to python
}

function post_init(){//this function is loaded when the body of posts.html is loaded
    user();
    updatePosts();
    setInterval(updatePosts,2000);//constantly gets posts
}