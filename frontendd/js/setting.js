const API_URL = "http://127.0.0.1:8000"

document.addEventListener("DOMContentLoaded", () => {

    document
        .getElementById("saveBtn")
        .addEventListener("click", updateProfile)

    loadSidebar()
    loadProfile()

})


async function loadSidebar(){

    const res = await fetch("./layout/sidebar.html")
    const html = await res.text()

    document.getElementById("sidebar").innerHTML = html
}


async function loadProfile(){

    const token = localStorage.getItem("token")

    if(!token){
        window.location.href = "login.html"
        return
    }

    const response = await fetch(`${API_URL}/profile`,{

        headers:{
            "Authorization": "Bearer " + token
        }

    })

    if(response.status === 401){
        window.location.href = "login.html"
        return
    }

    const data = await response.json()

    document.getElementById("profileName").innerText = data.name
    document.getElementById("profileEmail").innerText = data.email

    document.getElementById("nameInput").value = data.name
    document.getElementById("emailInput").value = data.email
}


async function updateProfile(){

    const token = localStorage.getItem("token")

    const name = document.getElementById("nameInput").value
    const email = document.getElementById("emailInput").value

    const response = await fetch(`${API_URL}/update`,{

        method:"PUT",

        headers:{
            "Content-Type":"application/json",
            "Authorization":"Bearer " + token
        },

        body:JSON.stringify({
            name:name,
            email:email
        })

    })

    if(response.ok){

        alert("Cập nhật thành công")
        loadProfile()

    }else{

        alert("Cập nhật thất bại")

    }

}