// Simple login handler (cookie-based session)
document.getElementById("btnLogin").addEventListener("click", async () => {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const msg = document.getElementById("msg");
  msg.textContent = "";

  try {
    const res = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username, password })
    });
    if (!res.ok) { msg.textContent = "Credenciales inválidas."; return; }
    window.location.href = "/app";
  } catch {
    msg.textContent = "Error de red.";
  }
});
