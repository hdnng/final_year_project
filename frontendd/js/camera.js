async function startCamera(){

    const token = localStorage.getItem("token")

    const response = await fetch("http://127.0.0.1:8000/camera/start",{

        method:"POST",

        headers:{
            "Authorization":"Bearer "+token
        }

    })

    if(response.ok){

        document.getElementById("status").innerText = "Camera: ON"

    }else{

        alert("Cannot start camera")

    }
}


async function stopCamera(){

    const token = localStorage.getItem("token")

    const response = await fetch("http://127.0.0.1:8000/camera/stop",{

        method:"POST",

        headers:{
            "Authorization":"Bearer "+token
        }

    })

    if(response.ok){

        document.getElementById("status").innerText = "Camera: OFF"

    }else{

        alert("Cannot stop camera")

    }
}