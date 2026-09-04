# 🚨 Real-Time Emergency & Disaster Response Coordination System

A real-time emergency response coordination platform designed to manage incidents, prioritize emergencies, assign responders, and deliver live operational updates.

🔗 **Project Repository:** [View on GitHub](https://github.com/ankitatodkar1010/Emergency_Response_System)

## 🚀 Key Features

- JWT Authentication
- Role-Based Access Control (RBAC)
- Emergency Incident Management
- Automated Incident Priority Calculation
- Geospatial Nearest-Responder Selection
- Responder Availability & Location Tracking
- Responder Assignment & Reassignment
- PostgreSQL Transactions
- Row-Level Locking for Concurrency Control
- Redis Pub/Sub
- WebSocket Real-Time Communication
- Real-Time Incident/Event Feed
- Notifications
- Audit Logging
- Input Validation & Error Handling
- Dockerized Development Environment
- Automated Tests

## 🏗️ Architecture

Client  
↓  
FastAPI  
↓  
Service Layer  
↓  
PostgreSQL  

Redis Pub/Sub  
↓  
WebSocket Manager  
↓  
React Frontend

## 🔄 Emergency Response Flow

Citizen reports emergency  
→ Calculate incident priority  
→ Find available nearby responder  
→ Create assignment  
→ Notify responder  
→ Publish Redis event  
→ Deliver through WebSocket  
→ Update frontend in real time

## 🛠️ Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- WebSockets
- JWT

### Frontend

- React
- Vite
- JavaScript
- CSS

### DevOps & Tools

- Docker
- Docker Compose
- Alembic
- Git

## 🧪 Testing

The project includes tests for core incident and assignment service logic, along with manual WebSocket testing.

## ▶️ Running Locally

Start the application using Docker Compose:

```bash
docker compose up -d
