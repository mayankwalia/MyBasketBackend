# MyBasket (Grocery Store) 
- Project submitted by **Mayank Walia** 21f1004343.
- A My Basket web app as part of the IITM MAD-2 Diploma Project. 

# Description
The MyBasket app is a comprehensive grocery shopping platform developed using Flask and Vue.js, providing users with a seamless experience to browse, order, and track grocery items. The application encompasses features for users, administrators, and store managers, offering a wide range of functionalities such as product browsing, cart management, order placement, and reporting.
# Technologies Used
- Flask: A micro web framework in Python for building the backend.
- Vue.js: A JavaScript framework for interactive user interfaces.
- SQLalchemy: A Python SQL toolkit and ORM library for managing database operations.
- Flask-JWT-Extended: Provides JSON Web Token (JWT) authentication support.
- Flask-Restful: Simplifies the creation of RESTful APIs.
- Flask-Cors: Handles Cross-Origin Resource Sharing.
- SMTP and Flask-Mail: Utilized for sending emails.
- Redis: An in-memory data store for caching and background jobs.
- Celery: A distributed task queue system for managing background jobs.
- Axios: A JavaScript library for asynchronous HTTP requests.
- Chart JS: A JavaScript library for data visualization using charts.
- Logging: Implemented for debugging purposes.
- Dotenv, httplib, json, os, datetime, CSV: Used for various utility functions.
- Vue-CLI, Vue3, Vue-Router@4: Tools and libraries for Vue.js development.

# Database Schema Design
The database schema design includes three roles: Admin, Store Manager, and Customer. Users are associated with a single role in a one-to-one relationship. Each user has one cart (one-to-one relationship). Categories can contain multiple products (one-to-many relationship), and users can have multiple products in their cart. Each order can encompass multiple products with varying quantities, necessitating the "Items Ordered" table to capture this data, including the selling price at the time of order for dynamic pricing. Customers can place multiple orders (one-to-many relationship).

For feedback and ratings, the "Feedback" table has a many-to-one relationship with the "Products" table. Manager requests, such as those applied during signup or for adding, editing, and removing categories, are stored in the "Manager Requests" table. Admins can approve or decline these requests.



# API Design
The API design of the MyBasket app, implemented using Flask-RESTful, features a comprehensive set of endpoints to facilitate key functionalities. Endpoints have been established for user-related operations, encompassing signup and login, as demonstrated by the code snippet provided. Additionally, the API supports CRUD operations for managing essential entities such as Users, Products, Categories, Requests, Feedback, Orders, and Items Ordered. Product and category management endpoints allow users to create, read, update, and delete product and category data. The API also supports feedback and ratings with corresponding CRUD operations. For order management, endpoints for placing and tracking orders are in place, along with functionalities for exporting order data to CSV format. Monthly report generation and fetching summary data are seamlessly integrated, ensuring a robust and comprehensive API design for the MyBasket grocery store application.
Architecture and Features

The MyBasket app adopts a Model-View-Controller (MVC) architecture to ensure a well-organized and scalable structure. The architecture separates concerns, with controllers managing routing and logic, Vue.js handling templates for dynamic user interface updates, and models interacting with the database through SQLalchemy. This approach enhances maintainability and facilitates the addition of new features. The default features of the application include user authentication, product and category listing, search and sorting functionalities, order management, and manager requests for category modifications. Notably, the app goes beyond the basics by incorporating advanced features such as dynamic pricing from the admin dashboard, the ability to switch between HTML or PDF monthly reports, and visualizations of data in charts for administrators and store managers. The MyBasket app's architecture and feature-rich design collectively contribute to a user-friendly and efficient grocery shopping experience.

# Features
- User signup and login (using RBAC)
- Mandatory Admin Login (using RBAC)
- Store Manager Signup and Login (using RBAC)
- Category and Product Management
- Search for Category/Product
- Buy products from one or multiple Categories
- Backend Jobs
- Export Jobs
- Reporting Jobs
- Alert Jobs
- Backend Performance

# Other Special Features
- User Account Management:
    - Users can change their passwords.
    - Admin can deactivate or reactivate a user.
- Customers can deactivate their accounts at any time.
- Order Management:
    - Admin and store managers can change the order status.
    - Customers can cancel orders until delivery.
- Product Management:
    - Admin can toggle the visibility of a product easily.
    - Advanced Search and Filtering:
    - Users can search and filter products based on parameters like popularity, latest, and trending.
- Dynamic Pricing:
    - Admin can update discounts for particular products from the dashboard.
- Reporting:
   - Users can switch between HTML or PDF monthly reports.
   - Admin and store managers have access to visualizations of data in charts.



# Local Setup
- Create virtual environment. On VS Code terminal execute `python -m venv env`
- Activate virtual environment. On VS Code terminal execute ` source env/bin/activate` 
- Run `pip install -r requirements.txt` to install all dependencies
- Install other dependencies in case not present on your system

# Local Development Run
- `python -m main` It will start the flask app in `development`. Suited for local development. 


# Accessing API

- Refer to the YAML file for making API requests to retrieve data.

# Demo link
- A demonstration of how the app was made and is to be used is provided [here](https://drive.google.com/file/d/1d0gzGRI-lDv6kOpwo7zrQg6R08efc0uq/view)

# Folder Structure

- `mybasket.db` is the sqlite DB. 
- `/` is where our application code is
- `static` - default `static` files folder. It serves at '/static' path.
- `templates` - Default flask templates folder

