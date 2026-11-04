const enrollmentForm = document.getElementById("enrollmentForm");
const resultBox = document.getElementById("result");

enrollmentForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const voiceFile = document.getElementById("voice").files[0];

    if (!username || !voiceFile) {
        resultBox.className = "result-box error";
        resultBox.textContent = "Please enter a username and select a voice recording.";
        return;
    }

    const formData = new FormData();

    formData.append("username", username);
    formData.append("voice", voiceFile);

    resultBox.className = "result-box";
    resultBox.textContent = "Processing voice enrollment... Please wait.";

    const submitButton = enrollmentForm.querySelector("button");

    submitButton.disabled = true;
    submitButton.textContent = "Processing...";

    try {

        const response = await fetch("/enroll", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Enrollment failed.");
        }

        resultBox.className = "result-box success";

        resultBox.innerHTML = `
            <h3>Enrollment Successful!</h3>
            <p><strong>Username:</strong> ${data.username}</p>
            <p><strong>Status:</strong> ${data.status}</p>
            <p><strong>Embedding Dimensions:</strong> ${data.embedding_dimensions}</p>
            <p><strong>Processing Time:</strong> ${data.processing_time} seconds</p>
        `;

        enrollmentForm.reset();

    } catch (error) {

        resultBox.className = "result-box error";
        resultBox.textContent = "Error: " + error.message;

    } finally {

        submitButton.disabled = false;
        submitButton.textContent = "Enroll Voice";

    }

});