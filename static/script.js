// Toggle login popup

function toggleLogin(){

const box = document.getElementById("loginBox")

if(box.style.display === "block"){
box.style.display = "none"
}else{
box.style.display = "block"
}

}


// Handle login request

async function login(){

const email = document.getElementById("email").value
const password = document.getElementById("password").value

const res = await fetch("/login",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
email:email,
password:password
})
})

const data = await res.json()

if(data.status === "success"){

// hide popup
document.getElementById("loginBox").style.display="none"

// replace Sign-in button with user profile
const userBox = document.getElementById("userBox")

userBox.innerHTML = `
<div class="user-pill">

<div class="avatar">${data.user.name[0].toUpperCase()}</div>

<div class="user-info">
<div class="user-name">${data.user.name}</div>
<div class="user-email">${data.user.email}</div>
</div>

</div>
`

}else{

alert("Invalid login")

}

}