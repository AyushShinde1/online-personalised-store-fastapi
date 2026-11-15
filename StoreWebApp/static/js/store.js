document.addEventListener("DOMContentLoaded", () => {

    //----------------------------
    //DOM ELEMENTS
    //----------------------------

    const ownerActions =
        document.getElementById("ownerActions");

    const storeSelectorContainer =
        document.getElementById("storeSelectorContainer");

    const storeDropdown =
        document.getElementById("storeDropdown");

    const singleStoreName =
        document.getElementById("singleStoreName");

    const storeHeader =
        document.getElementById("storeHeader");

    const storeTitle =
        document.getElementById("storeTitle");

    const storeBackground =
        document.getElementById("storeBackground");

    const storeDP =
        document.getElementById("storeDP");

    const storeDescription =
        document.getElementById("storeDescription");

    const productsContainer =
        document.getElementById("productsContainer");

    const productsHeading =
        document.getElementById("productsHeading");

    const productCount =
        document.getElementById("productCount");

    const loadingMessage =
        document.getElementById("loadingMessage");

    const errorMessage =
        document.getElementById("errorMessage");

    const emptyMessage =
        document.getElementById("emptyMessage");

    const logoutBtn =
        document.getElementById("logoutBtn");

    const addProductBtn =
        document.getElementById("addProductBtn");

    const productModal =
        document.getElementById("productModal");

    const productForm =
        document.getElementById("productForm");

    const productFormMessage =
        document.getElementById("productFormMessage");

    const productStoreName =
        document.getElementById("productStoreName");

    const cartButton = 
        document.getElementById("cartButton");


    //-----------------------------------------
    //PAGE INFORMATION
    //-----------------------------------------
    const currentPath = decodeURIComponent(
        window.location.pathname
    );

    console.log("CurrentPath: ",currentPath)

    const pathParts = currentPath.split("/").filter(Boolean);

    const selectedStoreName = pathParts.length > 1 ? pathParts[1] : null;

    let currentUserRole = null;
    let currentUserId = null;
    let currentStore = null;
    let ownerStores = [];

    // ---------------------------------
    // HELPER FUNCTIONS
    // ---------------------------------

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.hidden = false;
    }

    function hideError() {
        errorMessage.textContent = ""
        errorMessage.hidden = true;
    }

    function createElement(tag, className, text) {
        const element = document.createElement(tag);

        if (className) {
            element.className = className;
        }

        if (text !== undefined) {
            element.textContent = text;
        }

        return element;
    }

    // ---------------------------------
    // FETCH STORE DATA
    // ---------------------------------

    async function loadStoreData() {
        
        try {

            loadingMessage.hidden = false;

            hideError();

            const apiURL = selectedStoreName 
                    ? `/store/api/${encodeURIComponent(selectedStoreName)}`
                    : "/store/api";

            const response = await fetch(apiURL, {
                method: "GET",
                credentials: "same-origin"
            })

            if (response.status === 401) {

                window.location.href = "/auth/login-page";
                return;
            }

            if (!response.ok) {
                const result = await response.json();

                throw new Error(
                    result.detail ||"Unable to load store"
                );
            }

            const data = await response.json();

            console.log(data);

            currentUserRole = data.userrole;
            currentUserId = data.current_user_id;

            ownerStores = data.stores || [];

            currentStore = data.store || null;

            renderNavigation(data);

            renderStoreHeader(data);

            renderProducts(data.products);

            productsHeading.textContent = currentStore 
                    ? `${currentStore.storename} Products`
                    : "All Products";

            productCount.textContent = `${data.total_products} products available`;
        
        }
        catch (error) {
            console.error("Store loading error:", error);

            showError(error.message);
        }
        finally {
            loadingMessage.hidden = true
        }

    };

    // ---------------------------------
    // NAVIGATION
    // ---------------------------------
    
    function renderNavigation(data) {
        const isBusinessOwner = currentUserRole === "Business Owner";
        // console.log("isBusinessOwner: ",isBusinessOwner)
        // console.log("currentUserRole: ",currentUserRole)
        // console.log("Role type:", typeof currentUserRole);
        // console.log("Role value:", JSON.stringify(currentUserRole));
        // console.log("Is Business Owner:", currentUserRole === "Business Owner");
        //hideall ownere controls for normal users

        ownerActions.hidden = !isBusinessOwner;

        if (!isBusinessOwner) {
            
            storeSelectorContainer.hidden = true;
            cartButton.hidden = false

            return;
        }

        // Populate owners stores

        storeDropdown.innerHTML = ""

        ownerStores.forEach(store => {
            const option = document.createElement("option");

            option.value = store.storename;
            option.textContent = store.storename;

            if ( currentStore && currentStore.id === store.id) {
                option.selected = true;
            }

            storeDropdown.appendChild(option);
        });

        // show dropdown only if owner has multiple stores
        if (ownerStores.length > 1) {
            storeSelectorContainer.hidden = false;
            storeDropdown.hidden = false;

            singleStoreName.hidden = true;
        }

        else if (ownerStores.length === 1) {
            storeSelectorContainer.hidden = false;
            storeDropdown.hidden = true;

            singleStoreName.hidden = false;

            singleStoreName.textContent = ownerStores[0].storename;
        }

        else {
            storeSelectorContainer.hidden = true;
        }
    }

    // ---------------------------------
    // STORE DROPDOWN
    // ---------------------------------

    storeDropdown.addEventListener("change", () => {
        const selectedStore = storeDropdown.value;

        if (selectedStore) {
            window.location.href = `/store/${encodeURIComponent(selectedStore)}`;
        }
    });

    // ---------------------------------
    // STORE HEADER
    // ---------------------------------    

    function renderStoreHeader(data) {
        
        if (!data.store) {
            storeHeader.hidden = true;
            storeTitle.textContent = "My Online Store";

            return;
        }
        
        const store = data.store;

        storeHeader.hidden = false;

        storeTitle.textContent = store.storename;
        storeDescription.textContent = store.store_description || "";


        if (store.store_background_img_path) {
            storeBackground.src = store.store_background_img_path;
            storeBackground.hidden = false;
        } else {
            storeBackground.hidden = true;
            storeDP.hidden = false;
        }


        if (store.store_dp_path) {
            storeDP.src = store.store_dp_path;
        } else {
            storeDP.hidden = true;
        }

    }

    // ---------------------------------
    // PRODUCT CARDS
    // ---------------------------------

    function renderProducts(products) {
        
        productsContainer.replaceChildren();

        emptyMessage.hidden = products.length > 0;

        if (products.length === 0){
            return;
        }

        products.forEach(product => {
            const card = createElement("div","product-card");
            const image = createElement("img", "product-image");

            image.src = product.main_img_url || "/static/images/default-product.png";
            image.alt = product.product_name;
            image.loading = "lazy";
            
            image.onerror = () => {
                image.onerror = null;
                image.src = "/static/images/default-product.jpg"
            };


            const details = createElement("div", "product-details");
            const name = createElement("h3", "", product.product_name);
            const price = createElement("span", "product-price", `₹${Number(product.product_price).toFixed(2)}`);

            details.appendChild(name);

            const priceContainer = createElement("div");

            priceContainer.appendChild(price);

            if (product.mrp > product.product_price) {
                const mrp = createElement("span","product-mrp",`₹${Number(product.mrp).toFixed(2)}`);
                priceContainer.appendChild(mrp);
            }

            details.appendChild(priceContainer);

            const stock = createElement("p", "product-stock", product.stock_quantity > 0 ? `In Stock: ${product.stock_quantity}` : "Out of Stock");
            details.appendChild(stock);

            const viewButton = createElement("a", "view-product-btn", "View Product");

            viewButton.href= `/product/${product.id}`;
            details.appendChild(viewButton);

            const addToCartBtn = createElement("button", "view-product-btn", "Add to Cart");
            addToCartBtn.type = "button";

            addToCartBtn.addEventListener("click", async () => {
                try {
                    const response = await fetch(
                        `/cart/add/${product.id}?quantity=1`,
                        {
                            method: "POST",
                            credentials: "same-origin"
                        }
                    );

                    const result = await response.json();

                    if (response.status === 401) {
                        window.location.href = "/auth/login-page";
                        return;
                    }

                    if (!response.ok) {
                        alert(result.detail || "Unable to add product");
                        return;
                    }

                    alert("Product added to cart!");
                
                }
                catch (error) {
                    console.error(error);
                    alert("Unable to connect to server");
                }

            });

            details.appendChild(addToCartBtn);

            card.appendChild(image);
            card.appendChild(details);

            productsContainer.appendChild(card);
        })
    }

    // ---------------------------------
    // ADD PRODUCT START
    // ---------------------------------
    
    // ---------------------------------
    // ADD PRODUCT MODAL
    // ---------------------------------

    addProductBtn.addEventListener("click", () => {
        if (currentUserRole !== "Business Owner") {
            return;
        }
        console.log("Click addProductBtn")
        let selectedStore = null;

        if (currentStore) {
            if (currentStore.user_id_fk !== currentUserId) {
                alert("You can only add products to your own store.");
                return;
            }

            selectedStore = currentStore.storename;

        } else {

            if (ownerStores.length === 0) {
                alert("Please create a store first.");
                return;
            }

            if (ownerStores.length === 1) {
                selectedStore = ownerStores[0].storename;
            } else {
                selectedStore = storeDropdown.value;

                if  (!selectedStore) {
                    alert("Please select a store first.");
                    return;
                }
            }
        }

        productForm.reset();

        productStoreName.value = selectedStore;

        productFormMessage.textContent ="";

        productModal.hidden = false;
    });

    // ---------------------------------
    // CLOSE PRODUCT MODAL
    // --------------------------------

    document.getElementById("closeProductModal").addEventListener("click", () => {
        productModal.hidden = true;
    });

    // ---------------------------------
    // CREATE PRODUCT
    // ---------------------------------

    productForm.addEventListener("submit", async(event) => {
        event.preventDefault();

        productFormMessage.textContent = "";

        const formData = new FormData(productForm);

        const productData = {

            product_name:
                formData.get("product_name").trim(),
             
            sku:
                formData.get("sku").trim(),
             
            brand:
                formData.get("brand") || null,
             
            product_description:
                formData.get("product_description").trim(),
             
            mrp:
                Number(formData.get("mrp")),
             
            product_price:
                Number(formData.get("product_price")),
             
            stock_quantity:
                Number(formData.get("stock_quantity")),
             
            main_img_url:
                formData.get("main_img_url") || null,
             
            storename:
                formData.get("storename"),
            
            is_active: true,
            
            is_returnable: false
        };

        const saveButton = document.getElementById("saveProductBtn");

        saveButton.disabled = true;

        saveButton.textContent = "Creating Product...";

        try {

            const response = await fetch("/product/create",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            credentials: "same-origin",
                            body: JSON.stringify(productData)
                        }
            );

            const result = await response.json();

            if (response.status ===  401) {
                window.location.href = "auth/login-page";
                return;
            }

            if (!response.ok) {
                throw new Error(
                    result.details || "Product creationg failed"
                );
            }

            alert("Product created successfully!");

            productModal.hidden = true;
            
            productForm.reset();

            await loadStoreData();

        }
        catch (error) {

            productFormMessage.textContent = error.message;
        }
        finally {
            saveButton.disabled = false;

            saveButton.textContent = "Create Product";
        }
    });

    // ---------------------------------
    // ADD PRODUCT END
    // ---------------------------------

    // ---------------------------------
    // LOGOUT
    // ---------------------------------

    logoutBtn.addEventListener("click", async () => {
        try {
            const response = await fetch(
                "/auth/logout",
                {
                    method:"POST",
                    credentials: "same-origin"
                }
            );

            if (response.ok) {
                window.location.href = "/auth/login-page"
            } else {
                alert("Unable to logout. Please try again.");
            }
        }
        catch (error) {

            console.error("Logout error:", error);
        }
    });


    // ---------------------------------
    // CART BUTTON
    // ---------------------------------
    cartButton.addEventListener("click", () => {
        window.location.href = "/cart/page"
    })


    loadStoreData();











})