const userFile = document.getElementById("userFile");
const descriptionText = document.getElementById("buttonDescription")

function uploadFile(){
    descriptionText.textContent = "Button clicked";
}

userFile.addEventListener("click", uploadFile);