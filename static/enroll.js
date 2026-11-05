// ============================================================
// SECUREVOICE AI - VOICE ENROLLMENT
// Live microphone recording + existing file upload
// ============================================================


// ============================================================
// COMMON ELEMENTS
// ============================================================

const usernameInput = document.getElementById("username");

const liveResult = document.getElementById("liveResult");

const enrollmentForm = document.getElementById("enrollmentForm");
const uploadResult = document.getElementById("result");


// ============================================================
// RECORDING STATE
// ============================================================

const recordings = {
    1: null,
    2: null
};

const recordingStates = {
    1: null,
    2: null
};


// ============================================================
// HELPER: ESCAPE HTML
// ============================================================

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[character]);
}


// ============================================================
// CONVERT AUDIO BUFFER TO WAV
// ============================================================

function audioBufferToWav(audioBuffer) {

    const sampleRate = audioBuffer.sampleRate;
    const samples = audioBuffer.getChannelData(0);

    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    function writeString(offset, text) {
        for (let i = 0; i < text.length; i++) {
            view.setUint8(offset + i, text.charCodeAt(i));
        }
    }

    // WAV HEADER
    writeString(0, "RIFF");
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(8, "WAVE");

    // FORMAT CHUNK
    writeString(12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);

    // DATA CHUNK
    writeString(36, "data");
    view.setUint32(40, samples.length * 2, true);

    let offset = 44;

    for (let i = 0; i < samples.length; i++) {

        let sample = Math.max(-1, Math.min(1, samples[i]));

        const pcm = sample < 0
            ? sample * 32768
            : sample * 32767;

        view.setInt16(offset, pcm, true);

        offset += 2;
    }

    return new Blob([buffer], {
        type: "audio/wav"
    });
}


// ============================================================
// RECORDING TIMER
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
// UPDATE ENROLLMENT PROGRESS
// ============================================================

function updateProgress() {

    document.getElementById("progress1")
        .classList.toggle("completed", !!recordings[1]);

    document.getElementById("progress2")
        .classList.toggle("completed", !!recordings[2]);

    document.getElementById("liveEnrollBtn").disabled =
        !(recordings[1] && recordings[2]);
}


// ============================================================
// RECORD VOICE SAMPLE
// ============================================================

async function startRecording(number) {

    const recordButton = document.getElementById(`recordBtn${number}`);
    const timerElement = document.getElementById(`timer${number}`);
    const statusElement = document.getElementById(`status${number}`);

    if (recordingStates[number]) {

        recordingStates[number].recorder.stop();

        return;
    }

    if (!navigator.mediaDevices ||
        !navigator.mediaDevices.getUserMedia) {

        statusElement.textContent =
            "Microphone recording is not supported by this browser.";

        return;
    }

    let stream;
    let audioContext;

    try {

        statusElement.textContent =
            "Requesting microphone permission...";

        stream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        audioContext = new AudioContext();

        const recorder = new MediaRecorder(stream);

        const audioChunks = [];

        const startTime = Date.now();

        let elapsedSeconds = 0;

        recorder.ondataavailable = event => {

            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        recordingStates[number] = {
            recorder: recorder,
            stream: stream,
            audioContext: audioContext,
            chunks: audioChunks,
            timer: null
        };

        recordButton.textContent = "■ Stop Recording";
        recordButton.classList.add("recording");

        statusElement.textContent =
            "Recording... Speak clearly and naturally.";

        recorder.start();

        const timer = setInterval(() => {

            elapsedSeconds = Math.floor(
                (Date.now() - startTime) / 1000
            );

            timerElement.textContent =
                formatTime(elapsedSeconds);

            if (elapsedSeconds >= 30) {
                recorder.stop();
            }

        }, 250);

        recordingStates[number].timer = timer;

        recorder.onstop = async () => {

            clearInterval(timer);

            stream.getTracks().forEach(track => track.stop());

            recordButton.textContent = "● Start Recording";
            recordButton.classList.remove("recording");

            try {

                if (elapsedSeconds < 5) {

                    statusElement.textContent =
                        "Recording too short. Please record for at least 5 seconds.";

                    return;
                }

                statusElement.textContent =
                    "Converting recording to WAV...";

                const recordedBlob = new Blob(audioChunks, {
                    type: recorder.mimeType
                });

                const arrayBuffer = await recordedBlob.arrayBuffer();

                const decodedAudio =
                    await audioContext.decodeAudioData(arrayBuffer);

                // Convert to mono if necessary.
                let monoBuffer = decodedAudio;

                if (decodedAudio.numberOfChannels > 1) {

                    const offlineContext = new OfflineAudioContext(
                        1,
                        decodedAudio.length,
                        decodedAudio.sampleRate
                    );

                    const source = offlineContext.createBufferSource();

                    source.buffer = decodedAudio;

                    source.connect(offlineContext.destination);
                    source.start();

                    monoBuffer = await offlineContext.startRendering();
                }

                const wavBlob = audioBufferToWav(monoBuffer);

                recordings[number] = new File(
                    [wavBlob],
                    `voice_sample_${number}.wav`,
                    {
                        type: "audio/wav"
                    }
                );

                const preview = document.getElementById(
                    `preview${number}`
                );

                const audioPlayer = document.getElementById(
                    `audio${number}`
                );

                if (audioPlayer.dataset.url) {
                    URL.revokeObjectURL(audioPlayer.dataset.url);
                }

                const audioURL = URL.createObjectURL(wavBlob);

                audioPlayer.src = audioURL;
                audioPlayer.dataset.url = audioURL;

                preview.style.display = "block";

                statusElement.textContent =
                    "Recording ready. Play it back before continuing.";

                if (number === 1) {

                    document.getElementById("recordBtn2").disabled = false;

                    document.getElementById("status2").textContent =
                        "First recording complete. You can now record sample two.";
                }

                updateProgress();

            } catch (error) {

                recordings[number] = null;

                statusElement.textContent =
                    "Could not process recording: " + error.message;

                updateProgress();

            } finally {

                await audioContext.close();

                recordingStates[number] = null;
            }
        };

    } catch (error) {

        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }

        if (audioContext && audioContext.state !== "closed") {
            await audioContext.close();
        }

        recordingStates[number] = null;

        recordButton.textContent = "● Start Recording";

        statusElement.textContent =
            "Microphone error: " + error.message;
    }
}


// ============================================================
// RECORDING BUTTONS
// ============================================================

document.getElementById("recordBtn1").addEventListener(
    "click",
    () => startRecording(1)
);

document.getElementById("recordBtn2").addEventListener(
    "click",
    () => startRecording(2)
);


// ============================================================
// RETAKE RECORDINGS
// ============================================================

function clearRecording(number) {

    recordings[number] = null;

    const preview = document.getElementById(`preview${number}`);
    const audioPlayer = document.getElementById(`audio${number}`);

    if (audioPlayer.dataset.url) {

        URL.revokeObjectURL(audioPlayer.dataset.url);

        delete audioPlayer.dataset.url;
    }

    audioPlayer.removeAttribute("src");
    audioPlayer.load();

    preview.style.display = "none";

    document.getElementById(`timer${number}`).textContent = "00:00";

    document.getElementById(`status${number}`).textContent =
        "Waiting for your recording.";

    updateProgress();
}


document.getElementById("retakeBtn1").addEventListener("click", () => {

    clearRecording(1);

    // The second sample must be recorded again
    // after changing the first sample.

    clearRecording(2);

    document.getElementById("recordBtn2").disabled = true;

    document.getElementById("status2").textContent =
        "Complete the first recording to unlock this step.";
});


document.getElementById("retakeBtn2").addEventListener("click", () => {

    clearRecording(2);
});


// ============================================================
// LIVE TWO-RECORDING ENROLLMENT
// ============================================================

document.getElementById("liveEnrollBtn").addEventListener(
    "click",
    async function () {

        const username = usernameInput.value.trim();

        if (!/^[a-zA-Z0-9_-]{3,30}$/.test(username)) {

            liveResult.className = "result-box error";

            liveResult.textContent =
                "Enter a valid username (3-30 letters, numbers, underscores or hyphens).";

            return;
        }

        if (!recordings[1] || !recordings[2]) {

            liveResult.className = "result-box error";

            liveResult.textContent =
                "Please complete both voice recordings.";

            return;
        }

        const formData = new FormData();

        formData.append("username", username);
        formData.append("voice1", recordings[1]);
        formData.append("voice2", recordings[2]);

        const button = this;

        button.disabled = true;
        button.textContent = "Creating Voice Profile...";

        liveResult.className = "result-box";
        liveResult.textContent =
            "Processing both recordings. Please wait...";

        try {

            const response = await fetch("/enroll-live", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Enrollment failed.");
            }

            liveResult.className = "result-box success";

            liveResult.innerHTML = `
                <h3>Voice Enrollment Successful!</h3>
                <p><strong>Username:</strong> ${escapeHTML(data.username)}</p>
                <p><strong>Status:</strong> ${escapeHTML(data.status)}</p>
                <p><strong>Embedding Dimensions:</strong> ${data.embedding_dimensions}</p>
                <p><strong>Recordings Used:</strong> ${data.recordings_used}</p>
                <p><strong>Processing Time:</strong> ${data.processing_time} seconds</p>
            `;

            clearRecording(1);
            clearRecording(2);

            usernameInput.value = "";

            document.getElementById("recordBtn2").disabled = true;

        } catch (error) {

            liveResult.className = "result-box error";
            liveResult.textContent = "Error: " + error.message;

        } finally {

            button.textContent = "Complete Voice Enrollment";

            updateProgress();
        }
    }
);


// ============================================================
// EXISTING FILE UPLOAD ENROLLMENT
// ============================================================

enrollmentForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const username = usernameInput.value.trim();
    const voiceFile = document.getElementById("voice").files[0];

    if (!/^[a-zA-Z0-9_-]{3,30}$/.test(username) || !voiceFile) {

        uploadResult.className = "result-box error";

        uploadResult.textContent =
            "Enter a valid username and select a voice recording.";

        return;
    }

    const formData = new FormData();

    formData.append("username", username);
    formData.append("voice", voiceFile);

    uploadResult.className = "result-box";
    uploadResult.textContent =
        "Processing voice enrollment... Please wait.";

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

        uploadResult.className = "result-box success";

        uploadResult.innerHTML = `
            <h3>Enrollment Successful!</h3>
            <p><strong>Username:</strong> ${escapeHTML(data.username)}</p>
            <p><strong>Status:</strong> ${escapeHTML(data.status)}</p>
            <p><strong>Embedding Dimensions:</strong> ${data.embedding_dimensions}</p>
            <p><strong>Processing Time:</strong> ${data.processing_time} seconds</p>
        `;

        enrollmentForm.reset();

    } catch (error) {

        uploadResult.className = "result-box error";
        uploadResult.textContent = "Error: " + error.message;

    } finally {

        submitButton.disabled = false;
        submitButton.textContent = "Enroll Using Upload";
    }
});