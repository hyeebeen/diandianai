# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-driven logistics management platform called "diandianai" - a full-stack web application with real-time GPS tracking, intelligent chat features, and comprehensive shipment management capabilities.

## CRITICAL RULES

**YOU MUST遵循这些核心约束**：

Critical Rules ￼

1: Minimum Change Principle
 • Precisely identify root cause and fix within the smallest scope.
 • Avoid refactoring unrelated modules when fixing bugs.
 • Ensure changes have controllable, verifiable impact.

2: Schema-First Development
 • Let data models drive design; share a unified schema across frontend and backend.
 • Define API contracts upfront with end-to-end type safety.
 • Centralize validation rules to prevent data inconsistencies.

3: Defensive Programming
 • Assume all external inputs can be faulty.
 • Include boundary checks and robust fallback strategies.
 • Practice progressive enhancement: the system should remain functional under partial failures.


## Architecture

### Full-Stack Structure
- **Frontend**: React 18 + TypeScript + Vite + shadcn/ui + TailwindCSS
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL + Redis + Celery
- **Infrastructure**: Docker Compose with PostgreSQL, Redis, RabbitMQ, Nginx, Prometheus, Grafana
- **Testing**: Playwright for E2E, performance, load, and security testing

### Backend Architecture (`backend/src/`)
```
backend/src/
├── api/                    # FastAPI route handlers
│   ├── auth.py            # Authentication endpoints
│   ├── logistics.py       # Shipment management APIs
│   ├── ai.py             # AI assistant endpoints
│   ├── simple_ai.py      # Simplified AI chat service
│   ├── sse.py            # Server-Sent Events for real-time data
│   └── admin.py          # Admin management APIs
├── core/                  # Core application components
│   ├── config.py         # Pydantic settings management
│   ├── database.py       # SQLAlchemy async database setup
│   ├── security.py       # JWT and authentication utilities
│   └── celery_app.py     # Celery task queue configuration
├── models/               # SQLAlchemy database models
│   ├── users.py         # User and authentication models
│   ├── logistics.py     # Shipment and logistics models
│   ├── gps.py          # GPS tracking models
│   └── ai_models.py    # AI conversation models
├── services/            # Business logic layer
│   ├── auth_service.py      # Authentication business logic
│   ├── logistics_service.py # Shipment management logic
│   ├── gps_service.py      # GPS tracking service
│   ├── ai_service.py       # AI assistant service
│   └── simple_chat_service.py # Simplified chat logic
├── tasks/               # Celery background tasks
│   ├── gps_tasks.py    # GPS data processing tasks
│   ├── ai_tasks.py     # AI processing tasks
│   └── notification_tasks.py # Notification delivery
└── integrations/        # External API integrations
    ├── g7_api.py       # G7 GPS platform integration
    ├── wechat_api.py   # WeChat messaging integration
    ├── sms_api.py      # SMS notification service
    └── ai_providers/   # AI model providers (OpenAI, domestic models)
```

### Frontend Architecture (`src/`)
```
src/
├── components/          # React components
│   ├── ui/             # shadcn/ui component library
│   ├── auth/           # Authentication components
│   ├── common/         # Shared utility components
│   └── notifications/  # Real-time notification components
├── pages/              # Route-level page components
├── contexts/           # React Context providers (Auth, etc.)
├── hooks/              # Custom React hooks
└── services/           # API client services
```

## Development Commands

### Frontend Development
```bash
# Install dependencies
npm install

# Start development server (runs on http://localhost:3000)
npm run dev

# Build for production
npm run build

# Build for development environment
npm run build:dev

# Lint code
npm run lint

# Preview production build
npm run preview
```

### Backend Development
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start development server (runs on http://localhost:8000)
python -m src.main
# OR from src directory:
cd src && python main.py
```

### Docker Development
```bash
# Start all services (PostgreSQL, Redis, RabbitMQ, Backend, Frontend, Nginx, Prometheus, Grafana)
docker-compose up -d

# Development mode
docker-compose -f docker-compose.dev.yml up -d

# Production mode
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Testing Commands
```bash
# Run all E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Run E2E tests with browser visible
npm run test:e2e:headed

# Run performance tests
npm run test:performance

# Run load tests
npm run test:load

# Run security tests
npm run test:security

# Run all tests with HTML report
npm run test:all
```

## Configuration

### Environment Variables
Key environment variables for backend (`.env`):
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: AI model API key
- `OPENAI_BASE_URL`: AI API endpoint (defaults to Kimi K2)
- `JWT_SECRET_KEY`: JWT signing secret
- `ENVIRONMENT`: development/production

### Database
- **Primary DB**: PostgreSQL with asyncpg driver
- **Cache**: Redis for caching and real-time data
- **Message Queue**: RabbitMQ for Celery tasks

### AI Integration
- **Default Provider**: Kimi K2 (moonshot.cn API)
- **Supported Models**: OpenAI GPT models, domestic providers (Qwen, Wenxin, Zhipu)
- **Features**: Chat conversations, context-aware responses, logistics-specific AI assistance

## Key Features & Workflows

### Authentication & Authorization
- JWT-based authentication with refresh tokens
- Multi-tenant architecture support
- Protected routes with role-based access

### Logistics Management
- Shipment tracking and management
- Real-time GPS location updates via SSE
- Integration with G7 GPS platform
- Status history and workflow management

### AI Assistant
- Context-aware chat interface
- Logistics domain-specific responses
- Multiple AI provider support
- Real-time streaming responses

### Real-time Features
- Server-Sent Events (SSE) for live updates
- WebSocket support for instant notifications
- Real-time GPS tracking visualization
- Live chat with AI assistant

## Testing Strategy

### Test Structure
- **E2E Tests**: Authentication, shipment workflows, AI chat, real-time features
- **Performance Tests**: API response time validation (< 2s for auth, < 1.5s for shipments)
- **Load Tests**: Concurrent user testing (10-200 users)
- **Security Tests**: Authentication security, multi-tenant isolation, input validation

### Test Requirements
- Frontend server: http://localhost:8080
- Backend API: http://localhost:8000
- Test user: test@example.com / testpassword

## Development Notes

### Code Style
- **Frontend**: TypeScript strict mode, React 18 patterns, shadcn/ui components
- **Backend**: Python type hints, async/await patterns, Pydantic models
- **Database**: SQLAlchemy 2.0 async style, Alembic migrations

### Common Patterns
- **API Routes**: FastAPI routers with dependency injection
- **Database Access**: Async context managers for session handling
- **Error Handling**: Structured exception handling with proper HTTP status codes
- **Real-time Data**: SSE streams for live updates, WebSocket fallback

### External Integrations
- **G7 Platform**: GPS device data integration
- **WeChat API**: Notification delivery
- **AI Providers**: Multiple model support with fallback strategies

## Service Ports
- Frontend (Vite): 3000
- Backend (FastAPI): 8000
- PostgreSQL: 5432
- Redis: 6379
- RabbitMQ: 5672 (management: 15672)
- Nginx: 80/443
- Prometheus: 9090
- Grafana: 3001

## Multi-language Support
The application includes Chinese language support and is designed for logistics operations in China, with integration to local services like WeChat and domestic AI providers.
