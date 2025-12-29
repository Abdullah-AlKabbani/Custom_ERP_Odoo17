/** @odoo-module **/

console.log("🔥 [INIT] show_password_final.js LOADED");

/**
 * Attach password toggle behavior to a wrapper
 * @param {HTMLElement} wrapper
 */
function attachPasswordToggle(wrapper) {
    console.log("🔹 Processing wrapper:", wrapper);

    const input = wrapper.querySelector("input");
    const peek = wrapper.querySelector(".o_password_peek");
    const icon = peek?.querySelector("i");

    if (!input) return console.error("❌ No input found inside wrapper", wrapper);
    if (!peek) return console.error("❌ No .o_password_peek found inside wrapper", wrapper);

    console.log("🧱 Input and peek icon found");

    // تأكد أن الحقل مخفي افتراضياً
    input.type = "password";
    console.log("🔒 input.type set to 'password' by default");

    // أحداث الضغط المؤقت على الأيقونة
    peek.addEventListener("mousedown", () => {
        input.type = "text";
        icon?.classList.replace("fa-eye", "fa-eye-slash");
        console.log("👁️ input.type changed to 'text' (showing password)");
    });

    peek.addEventListener("mouseup", () => {
        input.type = "password";
        icon?.classList.replace("fa-eye-slash", "fa-eye");
        console.log("🔒 input.type changed back to 'password'");
    });

    peek.addEventListener("mouseleave", () => {
        input.type = "password";
        icon?.classList.replace("fa-eye-slash", "fa-eye");
        console.log("🔒 Mouse left icon, input.type reset to 'password'");
    });

    console.log("🟢 Event listeners attached for peek icon successfully");
}

/**
 * Initialize password toggler
 */
function initPasswordToggler() {
    const body = document.body;
    if (!body) {
        console.warn("⚠️ document.body not yet ready, retrying...");
        setTimeout(initPasswordToggler, 50);
        return;
    }

    console.log("🟢 Body is ready, setting MutationObserver");

    const observer = new MutationObserver((mutationsList, obs) => {
        const wrappers = document.querySelectorAll(".o_password_wrapper");
        if (wrappers.length > 0) {
            console.log("📦 Wrappers found dynamically:", wrappers.length);
            wrappers.forEach(wrapper => attachPasswordToggle(wrapper));
            obs.disconnect();
            console.log("🛑 MutationObserver disconnected after applying toggles");
        }
    });

    observer.observe(body, { childList: true, subtree: true });
    console.log("🟡 MutationObserver set to watch DOM for .o_password_wrapper");
}

// بدء التنفيذ
initPasswordToggler();
