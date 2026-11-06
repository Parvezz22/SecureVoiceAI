// ============================================================
// SECUREVOICE AI
// LIVE VOICE AUTHENTICATION + FILE UPLOAD
// FEATURE 3 - ADVANCED VOICE SIMILARITY ANALYSIS
// ============================================================


// ============================================================
// ELEMENTS
// ============================================================

const authenticationForm = document.getElementById("authenticationForm");
const resultBox = document.getElementById("result");

const usernameInput = document.getElementById("username");

const recordBtn = document.getElementById("recordBtn");
const recordingTimer = document.getElementById("recordingTimer");
const recordingStatus = document.getElementById("recordingStatus");

const audioPreview = document.getElementById("audioPreview");
const recordedAudio = document.getElementById("recordedAudio");

const retakeBtn = document.getElementById("retakeBtn");

const liveAuthenticateBtn = document.getElementById("liveAuthenticateBtn");
const liveResult = document.getElementById("liveResult");


// ============================================================
// RECORDING VARIABLES
// ============================================================

let mediaRecorder = null;
let audioChunks = [];

let microphoneStream = null;
let recordedBlob = null;
let recordedFile = null;

let recordingInterval = null;
let elapsedSeconds = 0;

let isRecording = false;

const MIN_RECORDING_SECONDS = 5;
const MAX_RECORDING_SECONDS = 30;


// ============================================================
// HTML ESCAPING
// ============================================================

function escapeHTML(value) {

    return String(value).replace(/[&<>"']/g, function (character) {

        return {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        }[character];

    });

}


// ============================================================
// TIMER
// ============================================================

function formatTime(seconds) {

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    return (
        String(minutes).padStart(2, "0") +
        ":" +
        String(remainingSeconds).padStart(2, "0")
    );

}


// ============================================================
// CONVERT AUDIO TO WAV
// ============================================================

function audioBufferToWav(audioBuffer) {

    const sampleRate = audioBuffer.sampleRate;
    const channelData = [];

    const channels = audioBuffer.numberOfChannels;

    for (let channel = 0; channel < channels; channel++) {

        channelData.push(audioBuffer.getChannelData(channel));

    }

    const samples = new Float32Array(audioBuffer.length);

    // Convert stereo to mono if necessary.

    for (let i = 0; i < audioBuffer.length; i++) {

        let sample = 0;

        for (let channel = 0; channel < channels; channel++) {

            sample += channelData[channel][i];

        }

        samples[i] = sample / channels;

    }


    // WAV configuration.

    const bytesPerSample = 2;
    const blockAlign = bytesPerSample;

    const buffer = new ArrayBuffer(44 + samples.length * bytesPerSample);
    const view = new DataView(buffer);


    function writeString(offset, string) {

        for (let i = 0; i < string.length; i++) {

            view.setUint8(offset + i, string.charCodeAt(i));

        }

    }


    writeString(0, "RIFF");

    view.setUint32(4, 36 + samples.length * bytesPerSample, true);

    writeString(8, "WAVE");

    writeString(12, "fmt ");

    view.setUint32(16, 16, true);

    view.setUint16(20, 1, true);

    view.setUint16(22, 1, true);

    view.setUint32(24, sampleRate, true);

    view.setUint32(28, sampleRate * blockAlign, true);

    view.setUint16(32, blockAlign, true);

    view.setUint16(34, 16, true);

    writeString(36, "data");

    view.setUint32(40, samples.length * bytesPerSample, true);


    let offset = 44;

    for (let i = 0; i < samples.length; i++) {

        let sample = Math.max(-1, Math.min(1, samples[i]));

        const value = sample < 0
            ? sample * 32768
            : sample * 32767;

        view.setInt16(offset, value, true);

        offset += 2;

    }


    return new Blob([buffer], { type: "audio/wav" });

}


// ============================================================
// MICROPHONE CLEANUP
// ============================================================

function stopMicrophone() {

    if (microphoneStream) {

        microphoneStream.getTracks().forEach(track => track.stop());

        microphoneStream = null;

    }

    if (recordingInterval) {

        clearInterval(recordingInterval);

        recordingInterval = null;

    }

    if (mediaRecorder && mediaRecorder.state !== "inactive") {

        mediaRecorder.stop();

    }

}


// ============================================================
// RESET RECORDING
// ============================================================

function resetRecording() {

    stopMicrophone();

    mediaRecorder = null;

    audioChunks = [];

    recordedBlob = null;
    recordedFile = null;

    elapsedSeconds = 0;

    isRecording = false;

    recordedAudio.removeAttribute("src");
    recordedAudio.load();

    audioPreview.style.display = "none";

    recordingTimer.textContent = "00:00";

    recordingStatus.textContent =
        "Waiting for your voice recording.";

    recordBtn.textContent = "● Start Recording";

    recordBtn.classList.remove("recording");

    liveAuthenticateBtn.disabled = true;

}


// ============================================================
// START / STOP RECORDING
// ============================================================

async function startRecording() {

    try {

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {

            throw new Error(
                "Microphone access is not supported by this browser."
            );

        }

        microphoneStream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });


        audioChunks = [];

        elapsedSeconds = 0;

        mediaRecorder = new MediaRecorder(microphoneStream);


        mediaRecorder.ondataavailable = function (event) {

            if (event.data.size > 0) {

                audioChunks.push(event.data);

            }

        };


        mediaRecorder.onstop = async function () {

            try {

                stopMicrophone();

                recordBtn.classList.remove("recording");

                if (elapsedSeconds < MIN_RECORDING_SECONDS) {

                    recordingStatus.textContent =
                        "Recording too short. Please record at least 5 seconds.";

                    recordBtn.textContent = "● Record Again";

                    return;

                }


                recordingStatus.textContent =
                    "Preparing your voice recording...";


                const originalBlob = new Blob(audioChunks, {
                    type: mediaRecorder.mimeType
                });


                const audioContext = new AudioContext();

                try {

                    const arrayBuffer = await originalBlob.arrayBuffer();

                    const decodedAudio =
                        await audioContext.decodeAudioData(arrayBuffer);

                    const wavBlob = audioBufferToWav(decodedAudio);

                    recordedBlob = wavBlob;

                    recordedFile = new File(
                        [wavBlob],
                        "authentication_voice.wav",
                        { type: "audio/wav" }
                    );

                } finally {

                    await audioContext.close();

                }


                const audioURL = URL.createObjectURL(recordedBlob);

                recordedAudio.src = audioURL;

                audioPreview.style.display = "flex";

                liveAuthenticateBtn.disabled = false;

                recordBtn.textContent = "● Record Again";

                recordingStatus.textContent =
                    "Recording ready! Play it back or authenticate your voice.";


            } catch (error) {

                console.error(error);

                recordingStatus.textContent =
                    "Could not process recording. Please try again.";

                liveAuthenticateBtn.disabled = true;

            }

        };


        mediaRecorder.start();

        isRecording = true;

        recordBtn.textContent = "■ Stop Recording";

        recordBtn.classList.add("recording");

        recordingStatus.textContent = "Recording your voice...";

        liveAuthenticateBtn.disabled = true;


        recordingInterval = setInterval(function () {

            elapsedSeconds++;

            recordingTimer.textContent = formatTime(elapsedSeconds);

            if (elapsedSeconds >= MAX_RECORDING_SECONDS) {

                stopRecording();

            }

        }, 1000);


    } catch (error) {

        console.error(error);

        recordingStatus.textContent =
            "Microphone access failed: " + error.message;

        stopMicrophone();

    }

}


function stopRecording() {

    if (!mediaRecorder || mediaRecorder.state === "inactive") {

        return;

    }

    isRecording = false;

    recordBtn.disabled = true;

    mediaRecorder.stop();

    stopMicrophone();

    recordBtn.textContent = "● Processing Recording...";

    setTimeout(() => {

        recordBtn.disabled = false;

    }, 500);

}


// ============================================================
// RECORD BUTTON
// ============================================================

recordBtn.addEventListener("click", function () {

    if (isRecording) {

        stopRecording();

    } else {

        resetRecording();

        startRecording();

    }

});


// ============================================================
// RETAKE RECORDING
// ============================================================

retakeBtn.addEventListener("click", function () {

    resetRecording();

    liveResult.className = "result-box";

    liveResult.textContent = "";

});


// ============================================================
// LIVE AUTHENTICATION
// ============================================================

liveAuthenticateBtn.addEventListener("click", async function () {

    const username = usernameInput.value.trim();

    if (!username) {

        liveResult.className = "result-box error";

        liveResult.textContent = "Please enter your username.";

        usernameInput.focus();

        return;

    }

    if (!recordedFile) {

        liveResult.className = "result-box error";

        liveResult.textContent = "Please record your voice first.";

        return;

    }


    const formData = new FormData();

    formData.append("username", username);

    formData.append("voice", recordedFile);


    liveResult.className = "result-box";

    liveResult.textContent =
        "Verifying your voice... Please wait.";


    liveAuthenticateBtn.disabled = true;

    liveAuthenticateBtn.textContent = "Verifying...";


    try {

        const response = await fetch("/authenticate", {

            method: "POST",

            body: formData

        });


        const data = await response.json();


        if (!response.ok) {

            throw new Error(data.detail || "Authentication failed.");

        }


        displayAuthenticationResult(data, liveResult);


    } catch (error) {

        liveResult.className = "result-box error";

        liveResult.textContent = "Error: " + error.message;

    } finally {

        liveAuthenticateBtn.disabled = false;

        liveAuthenticateBtn.textContent = "Authenticate My Voice";

    }

});


// ============================================================
// FEATURE 3 - ADVANCED AUTHENTICATION RESULT
// ============================================================

function displayAuthenticationResult(data, box) {

    const username = escapeHTML(data.username);
    const result = escapeHTML(data.authentication);
    const confidence = escapeHTML(data.confidence);

    const score = Number(data.similarity_score);
    const threshold = Number(data.threshold);
    const processingTime = Number(data.processing_time);


    // Validate numerical values.

    if (
        !Number.isFinite(score) ||
        !Number.isFinite(threshold) ||
        !Number.isFinite(processingTime)
    ) {

        box.className = "result-box error";

        box.textContent = "Invalid authentication result received.";

        return;

    }


    // Cosine similarity is displayed on a 0-100 visual scale.
    // This is NOT a probability.

    const percentage = Math.max(0, Math.min(100, score * 100));

    const thresholdPercentage =
        Math.max(0, Math.min(100, threshold * 100));


    const isSuccess = data.same_speaker === true;

    const statusClass = isSuccess ? "success" : "failed";


    const statusText = isSuccess
        ? "AUTHENTICATION SUCCESSFUL"
        : "AUTHENTICATION FAILED";


    const message = isSuccess

        ? "The submitted voice sample meets the configured similarity threshold and matches the registered voice profile."

        : "The submitted voice sample did not meet the configured similarity threshold. The registered voice could not be verified.";


    box.className = "result-box";


    box.innerHTML = `

        <div class="similarity-result">

            <div class="similarity-header">

                <h3>Voice Verification Analysis</h3>

                <span class="verification-status ${statusClass}">
                    ${statusText}
                </span>

            </div>


            <div class="similarity-score-section">

                <div class="similarity-label">
                    VOICE SIMILARITY SCORE
                </div>

                <div class="similarity-score">
                    ${percentage.toFixed(2)}%
                </div>

                <div class="similarity-label">
                    Scaled cosine similarity score (not a probability)
                </div>

            </div>


            <div class="similarity-meter">

                <div
                    class="similarity-fill"
                    style="width: ${percentage}%"
                ></div>

                <div
                    class="threshold-marker"
                    style="left: ${thresholdPercentage}%"
                ></div>

            </div>


            <div class="meter-labels">

                <span>0%</span>

                <span>
                    Threshold: ${thresholdPercentage.toFixed(0)}%
                </span>

                <span>100%</span>

            </div>


            <div class="similarity-details">


                <div class="similarity-detail-card">

                    <span>REGISTERED USER</span>

                    <strong>${username}</strong>

                </div>


                <div class="similarity-detail-card">

                    <span>CONFIDENCE LEVEL</span>

                    <strong>${confidence}</strong>

                </div>


                <div class="similarity-detail-card">

                    <span>PROCESSING TIME</span>

                    <strong>${processingTime.toFixed(4)} sec</strong>

                </div>


                <div class="similarity-detail-card">

                    <span>SIMILARITY SCORE</span>

                    <strong>${score.toFixed(4)}</strong>

                </div>


                <div class="similarity-detail-card">

                    <span>REQUIRED THRESHOLD</span>

                    <strong>${threshold.toFixed(2)}</strong>

                </div>


                <div class="similarity-detail-card">

                    <span>VERIFICATION RESULT</span>

                    <strong>${result}</strong>

                </div>


            </div>


            <div class="verification-message ${statusClass}">

                <strong>Verification Summary</strong>

                <p>${message}</p>

            </div>


        </div>

    `;

}


// ============================================================
// EXISTING FILE UPLOAD AUTHENTICATION
// ============================================================

authenticationForm.addEventListener("submit", async function (event) {

    event.preventDefault();


    const username = usernameInput.value.trim();

    const voiceFile = document.getElementById("voice").files[0];


    if (!username || !voiceFile) {

        resultBox.className = "result-box error";

        resultBox.textContent =
            "Please enter your username and select a voice recording.";

        return;

    }


    const formData = new FormData();

    formData.append("username", username);

    formData.append("voice", voiceFile);


    resultBox.className = "result-box";

    resultBox.textContent =
        "Verifying your voice... Please wait.";


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


        displayAuthenticationResult(data, resultBox);


        authenticationForm.reset();


    } catch (error) {

        resultBox.className = "result-box error";

        resultBox.textContent = "Error: " + error.message;

    } finally {

        submitButton.disabled = false;

        submitButton.textContent = "Authenticate Using Upload";

    }

});