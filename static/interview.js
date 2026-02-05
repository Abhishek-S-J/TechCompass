function startVoice() {
    const recognition = new webkitSpeechRecognition() || new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.start();

    recognition.onresult = function(event) {
        const text = event.results[0][0].transcript;
        const textarea = document.getElementById("answer");
        textarea.value = textarea.value + " " + text;
    };
}
function speakAI() {
    const aiText = document.getElementById("ai-output");

    if (!aiText || aiText.innerText.trim() === "") {
        alert("No AI response to speak!");
        return;
    }

    const utterance = new SpeechSynthesisUtterance(aiText.innerText);
    utterance.lang = "en-US";
    utterance.rate = 1;
    utterance.pitch = 1;

    speechSynthesis.cancel(); // stop previous speech
    speechSynthesis.speak(utterance);
}


