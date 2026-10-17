const userFile = document.getElementById("fileUpload").addEventListener("submit", uploadFile);
const login = document.getElementById("loginButton").addEventListener("click", openLogin);

var codeEditor = document.getElementById('codeEditor');

function uploadFile(){
    codeEditor.contentWindow.postMessage({
        eventType: "populateCode",
        language: "python",
        files: [
            {
                "name": "fileName.py",
                "content": "../FlowBridgeScript.s"
            }
        ]
    }, "*")
}

function openLogin(){
    window.open(
        //https://theadaptablescapstone.com/html/FlowBridgeLogin
        "./FlowBridgeLogin.html",
        "Login Or Sign-Up",
        "width=600, height=200, resizable=yes"
        
    );
}