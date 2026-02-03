Inventory & Order Management System

A full-stack web application designed to manage inventory, orders, and users efficiently for small and medium-sized businesses.

Purpose

This system centralizes inventory and order operations, automates stock tracking, and provides basic analytics to reduce manual effort and operational errors.

Core Features

Product and inventory management
Order creation with automatic stock updates
User authentication with role-based access
Dashboard with basic business analytics
Secure REST API backend

Technology Stack and Usage Reason

Backend: Python with FastAPI – chosen for fast performance, clean API design, and automatic API documentation
Database: MongoDB – used for flexible and scalable document-based data storage
Frontend: HTML, CSS, and JavaScript – simple, lightweight interface without framework dependency
Charts: Chart.js – provides clear and interactive visual analytics
Authentication: JWT (JSON Web Tokens) – enables secure, stateless user authentication
Server: Uvicorn – high-performance ASGI server for running FastAPI applications
Version Control: Git and GitHub – used for source control and project collaboration

System Architecture

Frontend communicates with the FastAPI backend through REST APIs.
The backend processes business logic and authentication.
MongoDB stores product, order, and user data.

Setup Overview

Clone the repository from GitHub.
Install backend dependencies using pip.
Create an environment file to store MongoDB configuration.
Start the FastAPI server using Uvicorn.
Access the application and API documentation through the browser.

Environment Configuration

The application uses environment variables to store database configuration securely.
MongoDB connection URL and database name are stored in a local environment file and are not committed to GitHub.

User Roles

Admin – full access to users, products, orders, and reports
Manager – manage products, orders, and view reports
Staff – view products and create orders

Project Structure

Backend folder contains the FastAPI application and business logic.
Frontend folder contains HTML, CSS, and JavaScript files for the user interface.

Learning Outcomes

Understanding of FastAPI and REST API development
MongoDB integration in a backend application
JWT-based authentication and authorization
Full-stack project structure and workflow
Practical experience with Git and GitHub
