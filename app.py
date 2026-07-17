import streamlit as st
import os
import pandas as pd

PRODUCT_FILE = "products.txt"

def load_products():
    products = {}
    if os.path.exists(PRODUCT_FILE):
        with open(PRODUCT_FILE) as f:
            for line in f:
                try:
                    pid, name, cat, price, qty, image = line.strip().split(",")
                    products[pid] = {"name": name, "cat": cat,
                                     "price": float(price), "qty": int(qty),
                                     "image": image}
                except ValueError:
                    pass
    return products

def save_products(products):
    with open(PRODUCT_FILE, "w") as f:
        for pid, d in products.items():
            f.write(f"{pid},{d['name']},{d['cat']},{d['price']},{d['qty']},{d['image']}\n")

def update_cart(products, cart, pid, qty):
    if pid in products:
        current_in_cart = cart.get(pid, 0)
        products[pid]["qty"] += current_in_cart
        if qty <= products[pid]["qty"]:
            cart[pid] = qty
            products[pid]["qty"] -= qty
            save_products(products)

def display_bill(products, cart):
    total = 0
    if not cart:
        st.write("🛒 Cart is empty.")
        return 0

    # List items with subtotals
    for pid, qty in cart.items():
        if qty > 0:
            price = products[pid]["price"]
            subtotal = price * qty
            total += subtotal
            st.write(f"**{products[pid]['name']}** | Unit: ₹{price} | Qty: {qty} | Subtotal: ₹{subtotal}")

    if total > 0:
        col1, col2 = st.columns([2,1])
        with col1:
            st.subheader(f"💰 Total Bill: ₹{total}")
        with col2:
            # Proceed to Pay triggers payment flow
            if st.button("Proceed to Pay"):
                st.session_state.show_payment = True

        # Show payment options only if Proceed clicked
        if st.session_state.get("show_payment", False):
            method = st.radio("Select Payment Method", ["Cash", "UPI", "Net Banking"])
            if st.button("Confirm Payment"):
                st.success(f"Payment via {method} successful! 🎉")
                st.markdown("### 🙏 Thanks for shopping, do visit us again!")

                # Record sale in dashboard
                if "sales" not in st.session_state:
                    st.session_state.sales = []
                for pid, qty in cart.items():
                    if qty > 0:
                        d = products[pid]
                        st.session_state.sales.append({
                            "Product": d["name"],
                            "Category": d["cat"],
                            "Price": d["price"],
                            "QtySold": qty,
                            "Revenue": d["price"] * qty,
                            "PaymentMethod": method
                        })

                # Auto-clear cart after payment
                for pid in list(cart.keys()):
                    products[pid]["qty"] += cart[pid]
                cart.clear()
                save_products(products)
                st.session_state.show_payment = False  # hide payment flow after confirmation

        # Manual Clear Cart button at bottom
        if st.button("Clear Cart"):
            for pid in list(cart.keys()):
                products[pid]["qty"] += cart[pid]
            cart.clear()
            save_products(products)
            st.warning("🧹 Cart cleared!")

    return total


def generate_dashboard(products, cart):
    if "sales" not in st.session_state or not st.session_state.sales:
        st.info("No sales yet.")
        return
    df = pd.DataFrame(st.session_state.sales)
    st.metric("Total Revenue", f"₹{df['Revenue'].sum():,.0f}")
    st.metric("Items Sold", int(df['QtySold'].sum()))
    st.metric("Avg Order Value", f"₹{df['Revenue'].mean():,.0f}")
    st.subheader("📊 Category Sales")
    st.bar_chart(df.groupby("Category")["Revenue"].sum())
    st.subheader("📈 Product Performance")
    st.line_chart(df.set_index("Product")["QtySold"])
    st.download_button("Download Sales Report (CSV)", df.to_csv(index=False), "sales_report.csv")

st.set_page_config(page_title="AI E-Commerce", layout="wide")
st.title("🛒 AI‑Enhanced E-Commerce App")

products = load_products()
if "cart" not in st.session_state:
    st.session_state.cart = {}

view = st.sidebar.radio("Choose View", ["Store", "Dashboard", "Manage Products"])

search_term = st.text_input("🔍 Search product by name")
if search_term:
    st.subheader("Search Results")
    for pid, d in products.items():
        if search_term.lower() in d["name"].lower():
            st.image(d["image"], caption=f"{d['name']} ({d['cat']})", width=250)
            st.write(f"💲 Price: ₹{d['price']} | 📦 Stock: {d['qty']}")

if view == "Store":
    st.header("✨ Product Showcase")
    categories = list(set(d["cat"] for d in products.values()))
    choice = st.selectbox("Filter by Category", ["All"] + categories)

    cols = st.columns(3)
    for i, (pid, d) in enumerate(products.items()):
        if choice == "All" or d["cat"].lower() == choice.lower():
            with cols[i % 3]:
                st.image(d["image"], caption=f"{d['name']} ({d['cat']})", width=250)
                st.write(f"💲 Price: ₹{d['price']} | 📦 Stock: {d['qty']}")
                qty = st.number_input(f"Qty for {d['name']}", min_value=0,
                                      max_value=d['qty']+st.session_state.cart.get(pid,0),
                                      step=1, key=f"qty_{pid}")
                update_cart(products, st.session_state.cart, pid, qty)

    st.header("🧾 Cart & Bill")
    if st.session_state.cart:
        display_bill(products, st.session_state.cart)
    else:
        st.write("Cart is empty.")

elif view == "Dashboard":
    st.header("📊 Sales Dashboard")
    generate_dashboard(products, st.session_state.cart)

elif view == "Manage Products":
    st.header("📦 Manage Products (CRUD)")
    crud_choice = st.radio("Choose Action", ["Add", "Update", "Delete"])
    pid = st.text_input("Product ID")
    name = st.text_input("Product Name")
    cat = st.text_input("Category")
    price = st.number_input("Price", min_value=0.0, step=1.0)
    qty = st.number_input("Quantity", min_value=0, step=1)
    image = st.text_input("Image URL")

    if st.button("Execute CRUD"):
        if crud_choice == "Add":
            products[pid] = {"name": name, "cat": cat, "price": price, "qty": qty, "image": image}
            save_products(products)
            st.success("Product added!")
        elif crud_choice == "Update":
            if pid in products:
                if name: products[pid]["name"] = name
                if cat: products[pid]["cat"] = cat
                if price: products[pid]["price"] = price
                if qty: products[pid]["qty"] = qty
                if image: products[pid]["image"] = image
                save_products(products)
                st.success("Product updated!")
            else:
                st.error("Product not found.")
        elif crud_choice == "Delete":
            if pid in products:
                del products[pid]
                save_products(products)
                st.warning("Product deleted!")
            else:
                st.error("Product not found.")
