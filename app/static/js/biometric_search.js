let videoStream = null;

// 1. USB/OTG Biometric Scanner Capture (Mantra RD Service Standard Port: 11100)
function captureUSBScanner() {
    const statusDiv = document.getElementById("usb-status");
    statusDiv.innerHTML = "<span class='text-blue-600 font-bold'>स्कॅनर शोधत आहे... कृपया बोट ठेवा (Waiting for finger)...</span>";

    // Standard local RD service call for Indian biometric USB hardware (Mantra/Morpho)
    fetch("https://127.0.0.1:11100/rd/capture", {
        method: "CAPTURE",
        headers: { "Content-Type": "text/xml" }
    })
    .then(response => response.text())
    .then(data => {
        statusDiv.innerHTML = "<span class='text-green-600 font-bold'>अंगठा स्कॅन यशस्वी! टेम्पलेट प्राप्त झाले.</span>";
        sendMinutiaeToBackend(data, "USB_SCANNER");
    })
    .catch(err => {
        // Fallback for Phase 1 simulation testing
        statusDiv.innerHTML = "<span class='text-amber-600 font-bold'>RD सर्व्हिस ऑफलाइन (Simulation Mode Active)</span>";
        sendMinutiaeToBackend("MOCK_ISO_MINUTIAE_TEMPLATE", "USB_SCANNER");
    });
}

// 2. Touchless Mobile Rear Camera with Flashlight (WebRTC)
async function startTorchCamera() {
    const video = document.getElementById("touchless-video");
    const placeholder = document.getElementById("camera-placeholder");

    try {
        // Request rear camera (environment facing) with torch capability
        videoStream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { ideal: "environment" },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        });

        video.srcObject = videoStream;
        video.classList.remove("hidden");
        placeholder.classList.add("hidden");

        // Attempt to turn on hardware flashlight
        const track = videoStream.getVideoTracks()[0];
        const capabilities = track.getCapabilities ? track.getCapabilities() : {};
        if (capabilities.torch) {
            await track.applyConstraints({ advanced: [{ torch: true }] });
        }
    } catch (err) {
        alert("कॅमेरा सुरू करण्यात अडचण: " + err.message);
    }
}

// Capture Macro Thumb Image from Video Stream
function captureMacroThumb() {
    if (!videoStream) {
        alert("कृपया प्रथम कॅमेरा सुरू करा.");
        return;
    }
    const video = document.getElementById("touchless-video");
    const canvas = document.getElementById("touchless-canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const base64Image = canvas.toDataURL("image/jpeg");
    sendMinutiaeToBackend(base64Image, "MOBILE_CAMERA");
}

// Send Minutiae/Image to Internal Server for 1:N Verification
function sendMinutiaeToBackend(payload, source) {
    const resultsPanel = document.getElementById("results-panel");
    const resultsContent = document.getElementById("results-content");

    fetch("/search/api/match-fingerprint", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: source, data: payload })
    })
    .then(res => res.json())
    .then(data => {
        resultsPanel.classList.remove("hidden");
        resultsContent.innerHTML = `
            <div class="p-3 bg-blue-50 border border-blue-200 rounded text-blue-900">
                <strong>स्रोत:</strong> ${data.source}<br>
                <strong>स्थिती:</strong> ${data.message} (Phase 2 SourceAFIS Engine Hook ready)
            </div>
        `;
    });
}

// 3. Submit Face Image for Search
function submitFaceSearch() {
    const fileInput = document.getElementById("faceInput");
    if (!fileInput.files[0]) {
        alert("कृपया चेहऱ्याचा फोटो निवडा.");
        return;
    }

    const formData = new FormData();
    formData.append("face_image", fileInput.files[0]);

    fetch("/search/api/match-face", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        const resultsPanel = document.getElementById("results-panel");
        const resultsContent = document.getElementById("results-content");
        resultsPanel.classList.remove("hidden");
        resultsContent.innerHTML = `
            <div class="p-3 bg-purple-50 border border-purple-200 rounded text-purple-900">
                <strong>तपासणी:</strong> ${data.message}
            </div>
        `;
    });
}