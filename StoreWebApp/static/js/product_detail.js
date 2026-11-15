document.addEventListener("DOMContentLoaded", () => {
    const editBtn = document.getElementById("editBtn")
    const editForm = document.getElementById("editForm")
    const cancelBtn = document.getElementById("cancelBtn")
    const message = document.getElementById("message")

    editBtn.addEventListener("click", () => {
        editForm.style.display = "block";

        editForm.scrollIntoView({
            behaviour: "smooth"
        });
    });

    cancelBtn.addEventListener("click", () => {

        editForm.style.display = "none";

        message.textContent = "";

    });

    editForm.addEventListener("submit", async (event) => {

        event.preventDefault();

        message.style.color = "black";
        message.textContent = "Updating product...";

        const productData = {

            product_name:
                document.getElementById("product_name").value,

            brand:
                document.getElementById("brand").value || null,

            product_description:
                document.getElementById("product_description").value,

            mrp:
                Number(document.getElementById("mrp").value),

            product_price:
                Number(document.getElementById("product_price").value),

            stock_quantity:
                Number(document.getElementById("stock_quantity").value),

            main_img_url:
                document.getElementById("main_img_url").value || null,

            discount_percentage:
                Number(document.getElementById("discount_percentage").value)

        };

        try {

            const response = await fetch(
                "/product/{{ product.id }}",
                {
                    method: "PATCH",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    credentials: "same-origin",

                    body: JSON.stringify(productData)
                }
            );

            const result = await response.json();

            if (!response.ok) {

                message.style.color = "red";

                message.textContent =
                    result.detail || "Product update failed.";

                return;
            }

            message.style.color = "green";

            message.textContent =
                "Product updated successfully!";

            setTimeout(() => {
                window.location.reload();
            }, 1000);

        } catch (error) {

            message.style.color = "red";

            message.textContent =
                "Unable to connect to the server.";

            console.error(error);

        }
    });
});