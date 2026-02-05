const chatBox = document.getElementById("chatBox");
const input = document.getElementById("userInput");

// Load chat history
window.onload = () => {
    const history = JSON.parse(sessionStorage
.getItem("chatHistory")) || [];
    history.forEach(msg => renderMessage(msg.sender, msg.text));
};
function showTyping() {
    const typing = document.createElement("div");
    typing.id = "typing";
    typing.className = "msg ai-msg";
    typing.innerText = "Typing...";
    chatBox.appendChild(typing);
    chatBox.scrollTop = chatBox.scrollHeight;
}
function removeTyping() {
    const typing = document.getElementById("typing");
    if (typing) typing.remove();
}
function saveMessage(sender, text) {
    const history = JSON.parse(sessionStorage.getItem("chatHistory")) || [];
    history.push({ sender, text });
    sessionStorage.setItem("chatHistory", JSON.stringify(history));
}


function sendMessage() {
    const message = input.value;

    if (!message.trim()) return;

    renderMessage("user", message);
    saveMessage("user", message);

    input.value = "";              // ✅ clear textarea
    input.style.height = "auto";   // optional UI fix

    showTyping();

    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
    })
    .then(res => res.json())
    .then(data => {
        removeTyping();

        const reply = data.reply || "⚠️ No response received";
        renderMessage("ai", reply);
        saveMessage("ai", reply);
    })
    .catch(err => {
        removeTyping();
        console.error(err);
        renderMessage("ai", "❌ Server not responding. Try again.");
    });
}
userInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});



function renderMessage(sender, text) {
    const msg = document.createElement("div");
    msg.className = sender === "user" ? "msg user-msg" : "msg ai-msg";

    const content = document.createElement("div");
    content.className = "msg-text";

    if (sender === "ai") {
        // AI: allow markdown
        content.innerHTML = marked.parse(text);
    } else {
        // USER: preserve new lines safely
        content.textContent = text;
    }

    msg.appendChild(content);

    if (sender === "ai") {
        const copyBtn = document.createElement("button");
        copyBtn.innerText = "📋 Copy";
        copyBtn.className = "copy-btn";
        copyBtn.onclick = () => navigator.clipboard.writeText(text);
        msg.appendChild(copyBtn);
    }

    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}
