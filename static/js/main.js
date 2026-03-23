const form = document.getElementById("registrationForm");
const message = document.getElementById("formMessage");

if (form) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);

    try {
      const res = await fetch("/register", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (data.success) {
        // ✅ POPUP ALERT
        alert("✅ REGISTRATION SUCCESSFUL");

        form.reset();

        message.style.color = "green";
        message.textContent = "Registration successful!";
      } else {
        alert("❌ Failed. Try again.");
      }
    } catch (err) {
      alert("❌ Error occurred");
    }
  });
}
