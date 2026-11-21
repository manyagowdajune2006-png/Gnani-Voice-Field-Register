
// ==================================
// LOGIN ELEMENTS
// ==================================

const loginScreen = document.getElementById("loginScreen");
const mainApp = document.getElementById("mainApp");

const loginForm = document.getElementById("loginForm");
const loginStatus = document.getElementById("loginStatus");
const loginBtn = document.getElementById("loginBtn");

const signupForm = document.getElementById("signupForm");
const signupStatus = document.getElementById("signupStatus");
const signupBtn = document.getElementById("signupBtn");

const loginSection = document.getElementById("loginSection");
const signupSection = document.getElementById("signupSection");

const showSignupBtn = document.getElementById("showSignupBtn");
const showLoginBtn = document.getElementById("showLoginBtn");

const logoutBtn = document.getElementById("logoutBtn");
const workerName = document.getElementById("workerName");


// ==================================
// VOICE ASSISTANT ELEMENTS
// ==================================

const connectBtn = document.getElementById("connectBtn");
const micBtn = document.getElementById("micBtn");
const stopBtn = document.getElementById("stopBtn");
const languageSelect = document.getElementById("language");
const statusText = document.getElementById("status");
const conversation = document.getElementById("conversation");
const visitDetails = document.getElementById("visitDetails");
const dangerStatus = document.getElementById("dangerStatus");

const historyBtn = document.getElementById("historyBtn");
const visitHistory = document.getElementById("visitHistory");

let socket = null;
let micStream = null;
let micContext = null;
let micSource = null;
let workletNode = null;
let playbackContext = null;
let nextPlayTime = 0;
let activeSources = [];
let isRecording = false;


// ==================================
// LOGIN AND SIGN UP SCREEN
// ==================================

function showLogin(message = "") {
    loginScreen.hidden = false;
    mainApp.hidden = true;

    loginSection.hidden = false;
    signupSection.hidden = true;

    loginStatus.textContent = message;
    signupStatus.textContent = "";
}

function showSignup() {
    loginSection.hidden = true;
    signupSection.hidden = false;

    signupStatus.textContent = "";
    loginStatus.textContent = "";
}

function showApp(username) {
    loginScreen.hidden = true;
    mainApp.hidden = false;

    workerName.textContent = username || "ASHA Worker";
}


// Switch to Sign Up
showSignupBtn.addEventListener("click", showSignup);


// Switch back to Login
showLoginBtn.addEventListener("click", () => {
    showLogin();
});


// ==================================
// CHECK LOGIN SESSION
// ==================================

async function checkLogin() {
    try {
        const response = await fetch("/api/me", {
            method: "GET",
            credentials: "same-origin",
            cache: "no-store"
        });

        if (!response.ok) {
            showLogin();
            return;
        }

        const data = await response.json();

        if (data.authenticated === false) {
            showLogin();
            return;
        }

        const username =
            data.username ||
            data.worker?.username ||
            data.worker ||
            "ASHA Worker";

        showApp(username);

    } catch (error) {
        console.error("Session check error:", error);
        showLogin("Unable to connect to the server. Please try again.");
    }
}


// ==================================
// WORKER SIGN UP
// ==================================

signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("signupUsername").value.trim();
    const password = document.getElementById("signupPassword").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    if (password !== confirmPassword) {
        signupStatus.textContent = "Passwords do not match.";
        return;
    }

    if (password.length < 10) {
        signupStatus.textContent =
            "Password must contain at least 10 characters.";
        return;
    }

    signupBtn.disabled = true;
    signupStatus.textContent = "Submitting account request...";

    try {
        const response = await fetch("/api/signup", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            signupStatus.textContent =
                data.detail || "Unable to create account.";
            return;
        }

        signupForm.reset();

        showLogin(
            "Account request submitted successfully! Please wait for administrator approval before logging in."
        );

    } catch (error) {
        console.error("Sign up error:", error);

        signupStatus.textContent =
            "Unable to connect to the server. Please try again.";

    } finally {
        signupBtn.disabled = false;
    }
});


// ==================================
// WORKER LOGIN
// ==================================

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    loginBtn.disabled = true;
    loginStatus.textContent = "Checking login details...";

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            loginStatus.textContent =
                data.detail || "Invalid username or password.";
            return;
        }

        document.getElementById("password").value = "";

        await checkLogin();

        if (mainApp.hidden) {
            loginStatus.textContent =
                "Login could not be verified. Please try again.";
        }

    } catch (error) {
        console.error("Login error:", error);

        loginStatus.textContent =
            "Unable to connect to the server. Please try again.";

    } finally {
        loginBtn.disabled = false;
    }
});


// ==================================
// WORKER LOGOUT
// ==================================

logoutBtn.addEventListener("click", async () => {
    logoutBtn.disabled = true;

    try {
        await stopMicrophone();

        if (socket) {
            socket.close();
            socket = null;
        }

        stopPlayback();

        const response = await fetch("/api/logout", {
            method: "POST",
            credentials: "same-origin"
        });

        if (!response.ok) {
            throw new Error("Logout failed.");
        }

        loginForm.reset();
        signupForm.reset();

        showLogin("You have logged out successfully.");

    } catch (error) {
        console.error("Logout error:", error);
        alert("Unable to log out. Please try again.");

    } finally {
        logoutBtn.disabled = false;
    }
});


// Check login when page opens
checkLogin();


// ==================================
// VOICE ASSISTANT FUNCTIONS
// ==================================

function addMessage(label, message) {
    const paragraph = document.createElement("p");
    paragraph.textContent = `${label}: ${message}`;
    conversation.appendChild(paragraph);
}

function setStatus(message) {
    statusText.textContent = message;
}

function sendAudioFrame(buffer) {
    if (!socket || socket.readyState !== WebSocket.OPEN || !isRecording) {
        return;
    }

    const bytes = new Uint8Array(buffer);
    let binary = "";

    for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
    }

    socket.send(JSON.stringify({
        type: "audio",
        data: btoa(binary)
    }));
}

async function startMicrophone() {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        setStatus("Connect first.");
        return;
    }

    try {
        micStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });

        micContext = new AudioContext();
        await micContext.audioWorklet.addModule("/audio-worklet.js");

        micSource = micContext.createMediaStreamSource(micStream);
        workletNode = new AudioWorkletNode(micContext, "pcm-processor");

        workletNode.port.onmessage = (event) => {
            sendAudioFrame(event.data);
        };

        micSource.connect(workletNode);
        workletNode.connect(micContext.destination);

        isRecording = true;
        micBtn.disabled = true;
        stopBtn.disabled = false;
        setStatus("Listening... Speak now.");

    } catch (error) {
        console.error(error);
        setStatus("Microphone could not start. Check browser permission.");
        await stopMicrophone();
    }
}

async function stopMicrophone() {
    isRecording = false;

    if (workletNode) {
        workletNode.port.onmessage = null;
        workletNode.disconnect();
        workletNode = null;
    }

    if (micSource) {
        micSource.disconnect();
        micSource = null;
    }

    if (micStream) {
        micStream.getTracks().forEach(track => track.stop());
        micStream = null;
    }

    if (micContext) {
        await micContext.close();
        micContext = null;
    }

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "end_utterance" }));
    }

    micBtn.disabled = !socket || socket.readyState !== WebSocket.OPEN;
    stopBtn.disabled = true;

    if (mainApp && !mainApp.hidden) {
        setStatus("Processing your speech...");
    }
}

async function playAudio(base64Audio) {
    try {
        if (!playbackContext) {
            playbackContext = new AudioContext({ sampleRate: 24000 });
        }

        await playbackContext.resume();

        const binary = atob(base64Audio);
        const samples = new Int16Array(binary.length / 2);

        for (let i = 0; i < samples.length; i++) {
            const low = binary.charCodeAt(i * 2);
            const high = binary.charCodeAt(i * 2 + 1);
            let value = (high << 8) | low;

            if (value >= 32768) {
                value -= 65536;
            }

            samples[i] = value;
        }

        const audioBuffer = playbackContext.createBuffer(
            1,
            samples.length,
            24000
        );

        const channel = audioBuffer.getChannelData(0);

        for (let i = 0; i < samples.length; i++) {
            channel[i] = samples[i] / 32768;
        }

        const source = playbackContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(playbackContext.destination);

        const startAt = Math.max(
            playbackContext.currentTime,
            nextPlayTime
        );

        source.start(startAt);
        nextPlayTime = startAt + audioBuffer.duration;

        activeSources.push(source);

        source.onended = () => {
            activeSources = activeSources.filter(item => item !== source);
        };

    } catch (error) {
        console.error("Audio playback error:", error);
    }
}

function stopPlayback() {
    for (const source of activeSources) {
        try {
            source.stop();
        } catch {}
    }

    activeSources = [];

    if (playbackContext) {
        nextPlayTime = playbackContext.currentTime;
    }
}


// ==================================
// CONNECT TO VOICE ASSISTANT
// ==================================

connectBtn.addEventListener("click", () => {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";

    socket = new WebSocket(`${protocol}//${location.host}/ws/voice`);

    setStatus("Connecting...");

    socket.onopen = () => {
        socket.send(JSON.stringify({
            type: "start",
            language: languageSelect.value
        }));
    };

    socket.onmessage = async (event) => {
        if (typeof event.data !== "string") return;

        let message;

        try {
            message = JSON.parse(event.data);
        } catch {
            return;
        }

        if (message.type === "ready") {
            setStatus("Connected and ready.");
            micBtn.disabled = false;
            connectBtn.disabled = true;
        }

        if (message.type === "transcript") {
            if (message.final) {
                addMessage("You", message.text || "");
            }
        }

        if (message.type === "response_text" || message.type === "say") {
            addMessage("Gnani", message.text || "");
        }

        if (message.type === "audio") {
            await playAudio(message.data || "");
        }

        if (message.type === "update") {
            visitDetails.textContent = JSON.stringify(
                message.form || {},
                null,
                2
            );

            dangerStatus.textContent = message.danger_flag
                ? "Safety alert: Please follow the referral guidance."
                : "No safety alert reported.";

            if (!isRecording) {
                micBtn.disabled = false;
                stopBtn.disabled = true;
                setStatus("Ready for the next response.");
            }
        }

        if (message.type === "interrupted") {
            stopPlayback();
            setStatus("Audio interrupted.");
        }

        if (message.type === "error") {
            setStatus(message.message || "Connection error");
        }
    };

    socket.onclose = async () => {
        await stopMicrophone();
        setStatus("Disconnected.");
        micBtn.disabled = true;
        stopBtn.disabled = true;
        connectBtn.disabled = false;
    };

    socket.onerror = () => {
        setStatus("Connection error.");
    };
});

micBtn.addEventListener("click", startMicrophone);
stopBtn.addEventListener("click", stopMicrophone);


// ==================================
// VISIT HISTORY FEATURE
// ==================================

function addHistoryText(parent, label, value) {
    const paragraph = document.createElement("p");

    paragraph.textContent = `${label}: ${
        value === undefined || value === null || value === ""
            ? "Not available"
            : String(value)
    }`;

    parent.appendChild(paragraph);
}

historyBtn.addEventListener("click", async () => {
    historyBtn.disabled = true;
    historyBtn.textContent = "Loading...";

    visitHistory.replaceChildren();

    try {
        const response = await fetch("/api/visits", {
            credentials: "same-origin",
            cache: "no-store"
        });

        if (response.status === 401 || response.status === 403) {
            showLogin("Please log in again.");
            return;
        }

        if (!response.ok) {
            throw new Error("Could not load visit history.");
        }

        const data = await response.json();
        const visits = data.visits || [];

        if (visits.length === 0) {
            const paragraph = document.createElement("p");
            paragraph.textContent =
                "No saved visits found. Complete and confirm a visit first.";

            visitHistory.appendChild(paragraph);
            return;
        }

        const heading = document.createElement("h3");
        heading.textContent = `Total saved visits: ${visits.length}`;
        visitHistory.appendChild(heading);

        visits.forEach((visit, index) => {
            const card = document.createElement("div");
            card.className = "history-card";

            const title = document.createElement("h3");
            title.textContent = `Visit ${index + 1}`;
            card.appendChild(title);

            addHistoryText(card, "Saved date", visit.created_at);

            const record = visit.record || {};
            const session = record.session || {};
            const form = session.form || {};

            addHistoryText(card, "Visit date", form.visit_date);
            addHistoryText(card, "Village", form.village);
            addHistoryText(card, "Household ID", form.household_id);
            addHistoryText(card, "Person name", form.person_name);
            addHistoryText(card, "Age", form.age);
            addHistoryText(card, "Main concern", form.main_concern);
            addHistoryText(card, "Notes", form.notes);

            if (record.transcript) {
                const transcriptHeading = document.createElement("h4");
                transcriptHeading.textContent = "Conversation transcript";
                card.appendChild(transcriptHeading);

                const transcript = document.createElement("p");
                transcript.textContent = record.transcript;
                card.appendChild(transcript);
            }

            visitHistory.appendChild(card);
        });

    } catch (error) {
        console.error("Visit history error:", error);

        const paragraph = document.createElement("p");
        paragraph.textContent =
            "Unable to load visit history. Please check the backend.";

        visitHistory.appendChild(paragraph);

    } finally {
        historyBtn.disabled = false;
        historyBtn.textContent = "View Visit History";
    }
});


// ==================================
// SERVICE WORKER
// ==================================

if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register("/sw.js").catch(() => {});
    });
}
