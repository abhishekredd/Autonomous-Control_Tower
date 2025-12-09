# 🚢 Autonomous Control Tower Manager

An AI-powered autonomous control tower for supply chain management that monitors end-to-end shipments, detects risks (port congestion, customs delays, quality holds), simulates mitigation options, executes actions like re-routing or mode-switching, and coordinates stakeholder communication.

## Features

- **Real-time Monitoring**: Track global shipments with live updates
- **AI Risk Detection**: Machine Learning and LLM-powered risk prediction
- **Digital Twin Simulation**: What-if analysis for mitigation strategies
- **Autonomous Actions**: Automated re-routing, mode-switching, and notifications
- **Multi-Agent System**: MCP-based specialized agents for different tasks
- **Stakeholder Coordination**: Intelligent communication with all parties

## Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **AI/ML**: OpenAI GPT-4, LangChain, custom ML models
- **Multi-Agent**: Model Context Protocol (MCP)
- **Database**: PostgreSQL with TimescaleDB
- **Cache**: Redis
- **Message Queue**: RabbitMQ + Celery
- **Frontend**: Streamlit
- **Deployment**: Docker, Kubernetes

## Quick Start

### Option 1: Using Docker (Recommended)
```bash
# Clone the repository
git clone https://github.com/yourusername/autonomous-control-tower.git
cd autonomous-control-tower

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up -d

# Initialize database
docker-compose exec api alembic upgrade head

# Seed sample data
docker-compose exec api python scripts/seed_data.py

# Access the application:
# Frontend: http://localhost:8501
# API Docs: http://localhost:8000/docs
# RabbitMQ Management: http://localhost:15672 (guest/guest)