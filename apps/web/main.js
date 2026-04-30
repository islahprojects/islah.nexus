const API_BASE = window.ISLAH_API_BASE || "http://127.0.0.1:8000";

const statusEl = document.querySelector("#api-status");
const form = document.querySelector("#mirror-form");
const input = document.querySelector("#mirrorPrompt");

async function sha512(value) {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-512", bytes);
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

async function checkSpine() {
  try {
    const response = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    if (!response.ok) throw new Error("health check failed");
    const data = await response.json();
    statusEl.textContent = data?.state === "living_spine_active" ? "living spine active" : "spine reachable";
    statusEl.classList.add("online");
  } catch (error) {
    statusEl.textContent = "local mirror ready / API pending";
    statusEl.classList.remove("online");
  }
}

async function createMirror(prompt) {
  const mirrorEvent = {
    type: "MIRROR_ASCEND",
    prompt,
    timestamp: new Date().toISOString(),
    source: "apps/web/create-mirror",
    covenant: "Walang Maiiwan",
  };

  const commitment = await sha512(JSON.stringify(mirrorEvent));
  localStorage.setItem("islah.mirror.last", JSON.stringify({ ...mirrorEvent, commitment }));

  try {
    await fetch(`${API_BASE}/bridge/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: "apps/web/create-mirror",
        commitment,
        ciphertext: null,
        metadata: {
          event_type: mirrorEvent.type,
          prompt_length: prompt.length,
          privacy_mode: "local_first",
        },
      }),
    });
    statusEl.textContent = "mirror sealed to bridge";
    statusEl.classList.add("online");
  } catch (error) {
    statusEl.textContent = "mirror sealed locally";
  }
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const prompt = input.value.trim() || "Create my mirror";
  await createMirror(prompt);
  input.value = "";
});

checkSpine();
