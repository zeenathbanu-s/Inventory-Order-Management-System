📦 Inventory & Order Management System

A full-stack web application to manage inventory, orders, and users efficiently for small and medium-scale businesses.

🎯 Purpose

✔ Centralizes inventory and order operations
✔ Automates stock tracking and updates
✔ Reduces manual errors and effort
✔ Provides basic business analytics

✨ Key Features

📦 Product and inventory management
🧾 Order creation with automatic stock deduction
👥 User authentication with role-based access
📊 Dashboard with analytics and charts
🔐 Secure REST API backend

🛠 Technology Stack (with reason)

🔹 Backend: Python + FastAPI — fast, modern API framework with automatic documentation
🔹 Database: MongoDB — flexible and scalable document-based storage
🔹 Frontend: HTML, CSS, JavaScript — lightweight and framework-free UI
🔹 Charts: Chart.js — interactive and simple data visualization
🔹 Authentication: JWT — secure, stateless user authentication
🔹 Server: Uvicorn — high-performance ASGI server
🔹 Version Control: Git & GitHub — source control and collaboration

🏗 System Architecture

🖥 Frontend → ⚙ FastAPI Backend → 🗄 MongoDB Database

⚙ Setup & Run Instructions

📌 Prerequisites
✔ Python 3.8 or higher
✔ MongoDB installed and running
✔ Git installed

📌 Steps to Run

➡ Clone the repository from GitHub
➡ Navigate to the backend folder
➡ Install required Python dependencies
➡ Create an environment file for MongoDB configuration
➡ Start the FastAPI server using Uvicorn

📌 Server Run Command

▶ uvicorn app.main:app --reload

📌 Access in Browser

🌐 Application: http://localhost:8000

📘 API Docs: http://localhost:8000/docs

🔐 Environment Configuration

🔑 Environment variables are used to store MongoDB details securely.
📁 The environment file is kept local and not pushed to GitHub.

Variables used:
• MongoDB connection URL
• Database name

👥 User Roles

🛡 Admin — full system access
📋 Manager — manage products and orders
🧑 Staff — view products and create orders

📂 Project Structure

📁 backend — FastAPI application and business logic
📁 frontend — HTML, CSS, and JavaScript files

🎓 Learning Outcomes

✅ REST API development using FastAPI
✅ MongoDB integration in backend applications
✅ JWT authentication and authorization
✅ Full-stack project workflow
✅ Git and GitHub version control
