🛒 Grocery Management System – README
📌 Overview:

The Grocery Management System is a full-stack web application designed to simulate real-world online grocery shopping platforms.
It includes a customer shopping interface and a secure admin dashboard for inventory management.

The system features category-wise product browsing, product details popup, real-time cart updates, stock management, discounts, search auto-suggest, and much more.

🚀 Features
🧑‍💻 Customer Features:

Category-wise product listing

Horizontal product slider

Product details popup (description + nutrition)

Add to cart

Increase / decrease quantity

Remove items

Stock indicators:

✔ In Stock

⚠ Low Stock

❌ Out of Stock

Discount system (badge + discounted price)

Search bar with auto-suggestions

Clean UI with images and banners

Background theme support

🔐 Admin Features:

Admin login page

Admin dashboard

Add new product

Update stock

Update price

Apply discount percentage

Delete product

Real-time sync with customer side

🗃️ Database Structure (SQLite):
Items Table
Column	Type	Description
id (PK)	INTEGER	Unique ID
name	TEXT	Product name
category	TEXT	Category name
price	REAL	Base price
quantity	INTEGER	Stock
discount_percent	INTEGER	Discount (0–100)
Cart Table
Column	Type	Description
id (PK)	INTEGER	Unique ID
product_name	TEXT	FK → items.name
price	REAL	Price after discount
quantity	INTEGER	Cart quantity
📊 UML / ER / Flowcharts

All documents are included:

Use Case Diagram

Class Diagram

Activity Diagram

ER Diagram

System Flowchart

🛠️ Technologies Used
Frontend:

HTML5

CSS3

JavaScript

Bootstrap

Backend:

Python

Flask Framework

Database:

SQLite

Tools:

VS Code

ReportLab (PDF generation)

PPTX (Python library for presentation)
