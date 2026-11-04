const authenticationForm = document.getElementById("authenticationForm");
const resultBox = document.getElementById("result");

authenticationForm.addEventListener("submit", async function (event) {

event.preventDefault();

const username = document.getElementById("username").value.trim();
const voiceFile = document.getElementById("voice").files[0];

if (!username || !voiceFile) {
    resultBox.className = "result-box error";
    resultBox.textContent = "Please enter your username and select a voice recording.";
    return;
}

const formData = new FormData();

formData.append("username", username);
formData.append("voice", voiceFile);

resultBox.className = "result-box";
resultBox.textContent = "Verifying your voice... Please wait.";

const submitButton = authenticationForm.querySelector("button");

submitButton.disabled = true;
submitButton.textContent = "Verifying...";

try {

    const response = await fetch("/authenticate", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Authentication failed.");
    }

    if (data.same_speaker) {

        resultBox.className = "result-box success";

        resultBox.innerHTML = `
            <h3>Authentication Successful!</h3>
            <p><strong>Username:</strong> ${data.username}</p>
            <p><strong>Result:</strong> ${data.authentication}</p>
            <p><strong>Similarity Score:</strong> ${data.similarity_score}</p>
            <p><strong>Threshold:</strong> ${data.threshold}</p>
            <p><strong>Confidence:</strong> ${data.confidence}</p>
            <p><strong>Processing Time:</strong> ${data.processing_time} seconds</p>
        `;

    } else {

        resultBox.className = "result-box error";

        resultBox.innerHTML = `
            <h3>Authentication Failed!</h3>
            <p><strong>Username:</strong> ${data.username}</p>
            <p><strong>Result:</strong> ${data.authentication}</p>
            <p><strong>Similarity Score:</strong> ${data.similarity_score}</p>
            <p><strong>Threshold:</strong> ${data.threshold}</p>
            <p><strong>Confidence:</strong> ${data.confidence}</p>
        `;

    }

    authenticationForm.reset();

} catch (error) {

    resultBox.className = "result-box error";
    resultBox.textContent = "Error: " + error.message;

} finally {

    submitButton.disabled = false;
    submitButton.textContent = "Authenticate Voice";

}

});