const uploadFileButton = document.getElementById("uploadFileButton");
const descriptionText = document.getElementById("buttonDescription")

function uploadFile(){
    heading.textContent = "Button clicked";
}

uploadFileButton.addEventListener("click", uploadFile);