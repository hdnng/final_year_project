document.getElementById("loginForm").addEventListener("submit", async function (e) {

    e.preventDefault()

    const email = document.getElementById("email").value
    const password = document.getElementById("password").value

    const response = await fetch("http://127.0.0.1:8000/login", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            email: email,
            password: password
        })

    })

    const data = await response.json()

    if (data.access_token) {

        localStorage.setItem("token", data.access_token)

        window.location.href = "/frontend/home.html"

    } else {

        alert("Login failed")

    }

})