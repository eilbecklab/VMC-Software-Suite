function togglePreview() {
    let x = document.getElementById("preview");
    if (x.style.display === "none") {
        x.style.display = "block";
    } else {
        x.style.display = "none";
    }
}

function toggleSchema() {
    let x = document.getElementById("schema");
    if (x.style.display === "none") {
        x.style.display = "block";
    } else {
        x.style.display = "none";
    }
}

function changeFileName(){
    let name = document.getElementById('fileName');
    let f = document.cookie.split(';');
    for (let cookie of f) {
        let parts = cookie.trim().split('=');
        if (parts[0] === 'filename') {
            name.innerHTML = parts[1];
            break
        }
    }
}

function showGIF(){
    let non = document.getElementById('non-loading');
    non.style.opacity = "0.1";
    let loading = document.getElementById("loading");
    loading.style.display = "block";
}

function copy(){
    let copyText = document.getElementById("hgvs_json").textContent;
    let textArea = document.createElement('textarea');
    textArea.textContent = copyText;
    document.body.append(textArea);
    textArea.select();
    document.execCommand("copy");
    /* Alert the copied text */
    alert("Copied to clipboard");
}