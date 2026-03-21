document.getElementById("registerForm").addEventListener("submit", async function(e){

    e.preventDefault()

    const name = document.getElementById("name").value
    const email = document.getElementById("email").value
    const password = document.getElementById("password").value
    const confirm = document.getElementById("confirm_password").value

    if(password !== confirm){
        alert("Mật khẩu không khớp")
        return
    }

    const response = await fetch("http://127.0.0.1:8000/register",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({
            name:name,
            email:email,
            password:password
        })

    })

    const data = await response.json()

    if(response.ok){

        alert("Đăng ký thành công")

        window.location.href="/frontend/login.html"

    }else{

        alert("Đăng ký thất bại")

        console.log(data)

    }

})