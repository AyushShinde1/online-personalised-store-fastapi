
document.addEventListener("DOMContentLoaded", () => {
    const registerForm = document.getElementById("registerForm");
    const registerMessage = document.getElementById("registerMessage");

    registerForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const formData = new FormData(registerForm);

        const userData = {
            username: formData.get("username"),
            password: formData.get("password"),
            first_name: formData.get("first_name"),
            last_name: formData.get("last_name"),
            role: formData.get("role"),
            phone_number: formData.get("phone_number"),
            email: formData.get("email")
        };

        try {
            registerMessage.textContent = "Registering...";

            const response = await fetch("/users/create-user", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(userData)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    result.msg || result.detail || "Registration failed."
                );
            }

            registerMessage.textContent = "User registered successfully!";
            registerForm.reset();

            console.log("API response:", result);

        } catch (error) {
            registerMessage.textContent = error.message;
            console.error("Registration error:", error);
        }
    });
});
