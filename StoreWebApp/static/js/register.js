
document.addEventListener("DOMContentLoaded", () => {
    const registerForm = document.getElementById("registerForm");
    const registerMessage = document.getElementById("registerMessage");

    //clearing all errorr fields
    function clearErrors() {
        const fileds = [
            "username",
            "password",
            "first_name",
            "last_name",
            "role",
            "phone_number",
            "email"
        ];

        fileds.forEach(field => {
            const errorElement = document.getElementById(`${field}_error`);

            if(errorElement) {
                errorElement.textContent = "";
                errorElement.style.color = "";
            }

            const input = document.getElementById(field);

            if (input) {
                input.removeAttribute("aria-invalid");
            }
        });

        registerMessage.textContent = "";
        registerMessage.style.color = "";
    }

    //Display an error below its corresponding field
    function showFieldError(field, message) {
        const errorElement = document.getElementById(`${field}_error`);
        const input = document.getElementById(field);

        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.color = "red";
        } else {
            // Fallback for errors without a matching field containger
            registerMessage.textContent += `${field}: ${message}\n`;
            registerMessage.style.color = "red";
        }

        if (input) {
            input.setAttribute("aria-invalid","true");
        }
    }

    // Display HTML validation errors below the relevant fields
    registerForm.querySelectorAll("input, select").forEach(input => {
        input.addEventListener("invalid", () => {
            const errorElement = document.getElementById(
                `${input.id}_error`
            );
        
            if (errorElement) {
                errorElement.textContent = input.validationMessage;
                errorElement.style.color = "red";
            }
        
            input.setAttribute("aria-invalid", "true");
        });
    });


    //newcode start
    // Validate when leaving a field, without blocking navigation
    registerForm.querySelectorAll("input, select").forEach(input => {
        input.addEventListener("blur", () => {
            if (input.value !== "" && !input.checkValidity()) {
                const errorElement = document.getElementById(
                    `${input.id}_error`
                );

                if (errorElement) {
                    errorElement.textContent = input.validationMessage;
                    errorElement.style.color = "red";
                }

                input.setAttribute("aria-invalid", "true");
            }
        });
    });
    //newcode end



    registerForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearErrors();

        //Run HTmL validation before sendingthe request
        if (!registerForm.checkValidity()) {
            registerForm.reportValidity();
            return;

        }

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
                // Format 1: { errors: [{ field, message }] }
                if (Array.isArray(result.errors)) {
                    result.errors.forEach(error => {
                        showFieldError(error.field, error.message);
                    });

                    registerMessage.textContent =
                        "Please correct the errors below.";
                    registerMessage.style.color = "red";

                // Format 2: FastAPI/Pydantic { detail: [...] }
                } else if (Array.isArray(result.detail)) {
                    result.detail.forEach(error => {
                        const field = error.loc?.at(-1);

                        if (field) {
                            showFieldError(field, error.msg);
                        }
                    });

                    registerMessage.textContent =
                        "Please correct the errors below.";
                    registerMessage.style.color = "red";

                // Format 3: { detail: "User already exists" }
                } else if (typeof result.detail === "string") {
                    registerMessage.textContent = result.detail;
                    registerMessage.style.color = "red";

                // Other error formats
                } else {
                    registerMessage.textContent =
                        result.msg || "Registration failed.";
                    registerMessage.style.color = "red";
                }

                return;
            }

            registerMessage.textContent = "User registered successfully!";
            registerMessage.style.color = "green";
            registerForm.reset();

            console.log("API response:", result);

        } catch (error) {
            registerMessage.textContent =
                "Unable to connect to the server. Please try again.";
            registerMessage.style.color = "red";

            console.error("Registration error:", error);
        }
    });

    // Clear an individual field's error when the user edits it
    registerForm.querySelectorAll("input, select").forEach(input => {
        input.addEventListener("input", () => {
            const errorElement = document.getElementById(
                `${input.id}_error`
            );

            if (errorElement) {
                errorElement.textContent = "";
            }

            input.removeAttribute("aria-invalid");
        });
    });
});
