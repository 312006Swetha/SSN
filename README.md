# SSN
Seamless Medicine Stock Monitoring

# Admin Login
User name = admin@123

# Medicine Inventory Management

This project is a Medicine Inventory Management System designed to track and manage medicines efficiently. It provides stock monitoring, product analytics of each item, sales prediction, and automated restocking. It utilizes machine learning to predict inventory needs based on historical data, ensuring efficient stock management and preventing shortages or overstocking.
The system is built using Flask and provides a user-friendly web-based dashboard that offers real-time insights into inventory levels. Owners can upload and manage stock data through Excel integration, making it easy to update records. This feature enhances accessibility and simplifies inventory tracking for healthcare professionals.

XTrackMeds also includes a notification system that alerts users based on stock conditions. It automatically generates notifications for:

Order Notification – When stock is running low and requires replenishment.
Low Stock Notification – When inventory drops below a critical threshold.
Restock Notification – When stock has been successfully replenished.
It also generates report and sent to admin's mail weekly once.

## Features
- Track medicine stock in real-time  
- Sales prediction using machine learning  
- Analytics dashboard to monitor stock levels  
- Automated restocking when stock falls below the threshold  
- Email notifications for weekly reports  


## Tech Stack
- Frontend: HTML, CSS, JavaScript  
- Backend: Python (Flask)  
- Database: SQLAlchemy
- Machine Learning: Random Forest (for sales prediction)  
- Notifications: Flask-Mail for emails  


## Setup Instructions
1. Clone the repository  
   ```bash
   git clone https://github.com/yourusername/medicine-inventory.git
   cd medicine-inventory

## Conclusion
The ultimate goal of the xtrackmed is is to efficiently manage stock levels and prevent understock situations. This can be achieved through real-time stock monitoring, predictive analytics, and automated restocking alerts. By leveraging machine learning, such as logistic regression, the system can forecast demand and ensure timely replenishment.
