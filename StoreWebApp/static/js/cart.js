document.addEventListener("DOMContentLoaded", () => {

    const cartContainer = document.getElementById("cartContainer");
    const cartTotal = document.getElementById("cartTotal");

    async function loadCart() {
        
        try {
            const response = await fetch("/cart/", {
                credentials: "same-origin"
            });

            if (response.status === 401) {
                window.location.href = "/auth/login-page";
                return;
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Unable to load cart");
            }

            renderCart(data);
        }
        catch (error) {
            cartContainer.textContent = error.message;
        }
    }

    function renderCart(data) {
        
        cartContainer.replaceChildren();

        if (data.items.length === 0) {
            cartContainer.textContent = "Your cart is empty.";
            cartTotal.textContent = "₹0.00";
            return;
        }

        data.items.forEach(item => {
            const div = document.createElement("div")
            const name = document.createElement("h3");
            name.textContent = item.product_name;

            const price = document.createElement("p");
            price.textContent = `₹${Number(item.price).toFixed(2)}`;

            const quantity = document.createElement("input");

            quantity.type = "number";
            quantity.min = "1";
            quantity.value = item.quantity;

            const subtotal = document.createElement("p");
            subtotal.textContent =
                `Subtotal: ₹${Number(item.subtotal).toFixed(2)}`;

            const updateBtn = document.createElement("button");
            updateBtn.textContent = "Update Quantity";

            updateBtn.addEventListener("click", async () => {

                const response = await fetch(
                    `/cart/update/${item.cart_item_id}?quantity=${quantity.value}`,
                    {
                        method: "PUT",
                        credentials: "same-origin"
                    }
                );

                const result = await response.json();

                if (!response.ok) {
                    alert(result.detail || "Update failed");
                    return;
                }

                loadCart();

            });

            const removeBtn = document.createElement("button");
            removeBtn.textContent = "Remove";

            removeBtn.addEventListener("click", async () => {

                const response = await fetch(
                    `/cart/remove/${item.cart_item_id}`,
                    {
                        method: "DELETE",
                        credentials: "same-origin"
                    }
                );

                if (!response.ok) {
                    alert("Unable to remove item");
                    return;
                }

                loadCart();

            });

            div.append(
                name,
                price,
                quantity,
                subtotal,
                updateBtn,
                removeBtn
            );

            cartContainer.appendChild(div);
        
        });

        cartTotal.textContent =
            `₹${Number(data.total_price).toFixed(2)}`;
    }


    // CHECKOUT

    document.getElementById("checkoutBtn")
        .addEventListener("click", async () => {

            const response = await fetch("/orders/checkout", {
                method: "POST",
                credentials: "same-origin"
            });

            const result = await response.json();

            if (!response.ok) {
                alert(result.detail || "Checkout failed");
                return;
            }

            alert(
                `Order created successfully!\nOrder ID: ${result.order_id}\nTotal: ₹${result.total_amount}`
            );

            loadCart();

        });


    loadCart();
});