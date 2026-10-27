document.addEventListener("DOMContentLoaded", ()=> {
    const loginForm = document.getElementById("loginForm")
    const loginMessage = document.getElementById("loginMessage")

    function clearErrors() {
        const fields = [
            "username",
            "password"
        ];

        fields.forEach(field => {
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

        loginMessage.textContent = "";
        loginMessage.style.color = "";
    }

    function showFieldError(field, message) {
        const errorElement = document.getElementById(`${field}_error`);
        const input = document.getElementById(field);

        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.color = "red";
        } else {
            // Fallback for errors without a matching field containger
            loginMessage.textContent += `${field}: ${message}\n`;
            loginMessage.style.color = "red";
        }

        if (input) {
            input.setAttribute("aria-invalid","true");
        }
    }

    // Display HTML validation errors below the relevant fields
    loginForm.querySelectorAll("input, select").forEach(input => {
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
    loginForm.querySelectorAll("input, select").forEach(input => {
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

    loginForm.addEventListener("submit", async (event) =>{
        event.preventDefault();
        clearErrors();

        if(!loginForm.checkValidity()){
            loginForm.reportValidity();
            return;
        }

        const formData = new FormData(loginForm);

        const userData = {
            username: formData.get("username"),
            password: formData.get("password")
        }

        try {
            loginMessage.textContent = 'Log in...';

            const response = await fetch("/auth/login",{
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

                    loginMessage.textContent =
                        "Please correct the errors below.";
                    loginMessage.style.color = "red";

                // Format 2: FastAPI/Pydantic { detail: [...] }
                } else if (Array.isArray(result.detail)) {
                    result.detail.forEach(error => {
                        const field = error.loc?.at(-1);

                        if (field) {
                            showFieldError(field, error.msg);
                        }
                    });

                    loginMessage.textContent =
                        "Please correct the errors below.";
                    loginMessage.style.color = "red";

                // Format 3: { detail: "User already exists" }
                } else if (typeof result.detail === "string") {
                    loginMessage.textContent = result.detail;
                    loginMessage.style.color = "red";

                // Other error formats
                } else {
                    loginMessage.textContent =
                        result.msg || "Login failed.";
                    loginMessage.style.color = "red";
                }

                return;
            }

            loginMessage.textContent = "User Logged In Successfully";
            loginMessage.style.color = "green";
            
            /*
            // Save access token for this browser tab
            sessionStorage.setItem("access_token", result.access_token);
            Why sessionStorage?

            It keeps the token available while the browser tab is open.
            The token is cleared when the tab's session ends.
            It is generally preferable to localStorage if you don't need the token to persist across browser sessions.
            Note that JavaScript-accessible storage can be exposed by cross-site scripting (XSS). For a production application, an HttpOnly, Secure, appropriately configured SameSite cookie is usually safer.

            // Redirect to the home page
            window.location.href = "/home";

            //We will use cookies
            */

            window.location.href = "/auth/home";

            loginForm.reset();

            console.log("API response:", result)
            console.log("Access Token", result.access_token)

        } catch (error) {
            loginMessage.textContent = "Unable to connect to the server. Please try again.";
            loginMessage.style.color = "red";

            console.error("Login error:", error);
        }
    });

    // Clear an individual field's error when the user edits it (Not needed here)
    loginForm.querySelectorAll("input, select").forEach(input => {
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

})