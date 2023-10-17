function welcome() {
    document.getElementById("paragraph").innerHTML += "<br/>This text was added by JavaScript 😀"

    updatePosts();
    setInterval(updatePosts, 2000);
}

function updatePosts() {  // update post every 2 sec
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


