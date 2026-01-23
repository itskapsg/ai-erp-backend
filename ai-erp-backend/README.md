# Scalable ERP System

A robust ERP system with dynamic versioning and parallel deployment support, built with FastAPI and PostgreSQL.

## 🚀 Features

- **Dynamic Port Mapping**: Run multiple instances simultaneously on different ports
- **Parallel Deployment**: Launch multiple versions (v1, v2, etc.) for testing and rollbacks
- **Health Monitoring**: Built-in health check endpoints
- **Database Integration**: PostgreSQL with SQLAlchemy ORM
- **Development Ready**: Hot reload, CORS enabled, comprehensive logging

## 📁 Project Structure

```
├── app/
│   └── main.py              # FastAPI application
├── docker-compose.yml       # Docker services configuration
├── Dockerfile              # Python application container
├── launch_erp.sh           # Parallel instance launcher
├── stop_erp.sh             # Instance stopper
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## 🛠️ Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Launch an Instance

```bash
# Launch development instance on port 8000
./launch_erp.sh dev 8000

# Launch version 1 on port 8001
./launch_erp.sh v1 8001

# Launch version 2 on port 8002
./launch_erp.sh v2 8002
```

### Stop an Instance

```bash
# Stop the development instance
./stop_erp.sh dev
```

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/

# API status
curl http://localhost:8000/api/v1/status
```

## 🔧 Development

### Running Without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Environment Variables

- `APP_PORT`: Application port (default: 8000)
- `DATABASE_URL`: PostgreSQL connection string
- `ENVIRONMENT`: Environment name (development/staging/production)

## 🐳 Docker Commands

```bash
# View running instances
docker compose -p <instance_name> ps

# View logs
docker compose -p <instance_name> logs -f

# Execute commands in container
docker compose -p <instance_name> exec backend bash
```

## 📊 Monitoring

The application provides several endpoints for monitoring:

- `/health` - Service health status
- `/` - Welcome message with basic info
- `/api/v1/status` - Detailed API status
- `/docs` - Interactive API documentation (Swagger UI)
- `/redoc` - Alternative API documentation

## 🔄 Version Control & Rollbacks

The parallel deployment system allows for:

1. **Blue-Green Deployments**: Run old and new versions simultaneously
2. **Safe Testing**: Test new versions on different ports
3. **Quick Rollbacks**: Switch traffic between versions instantly
4. **Zero Downtime**: Deploy without service interruption

## 🚦 Next Steps

1. Add database migrations with Alembic
2. Implement authentication and authorization
3. Add comprehensive logging and monitoring
4. Set up CI/CD pipeline
5. Add unit and integration tests
6. Configure production-ready settings