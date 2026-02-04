# MelonMind - Network Operations AI Assistant

Backend management system based on Django, integrating LangChain/LangGraph intelligent agents and Mulves knowledge base, designed as an operations assistant platform for network engineers.

## Features

### 🤖 Intelligent Agents
- Intelligent process orchestration based on LangChain/LangGraph
- Automated network device operations
- Configuration backup and recovery
- Health status monitoring
- Automatic fault diagnosis

### 📚 Knowledge Base Management
- Integrated Mulves knowledge base system
- Intelligent search and recommendation
- Network operations best practices
- Troubleshooting guides
- Configuration template library

### 🔧 Core Functions
- RESTful API interfaces
- Asynchronous task processing (Celery)
- Permission management and authentication
- Operation log recording
- Data statistics and analysis

## Tech Stack

- **Backend Framework**: Django 5.1+
- **API Framework**: Django REST Framework
- **AI Framework**: LangChain, LangGraph
- **Knowledge Base**: Mulves
- **Async Processing**: Celery + Redis
- **Database**: PostgreSQL
- **Dependency Management**: Poetry

## Quick Start

### 1. Environment Setup

```bash
# Clone project
git clone <repository-url>
cd MelonMind

# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 2. Environment Variables Configuration

```bash
# Copy environment configuration template
cp .env.example .env

# Edit configuration file
vim .env
```

### 3. Database Initialization

```bash
# Create database
createdb melonmind

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Initialize knowledge base
python scripts/setup_knowledge_base.py
```

### 4. Start Services

```bash
# Start Django development server
python manage.py runserver

# Start Celery worker (new terminal)
celery -A config worker --loglevel=info

# Start Celery beat (new terminal, if scheduled tasks needed)
celery -A config beat --loglevel=info
```

## Project Structure

```
MelonMind/
├── config/                 # Django configuration
├── apps/                   # Application modules
│   ├── agents/            # Intelligent agents application
│   ├── knowledge_base/    # Knowledge base application
│   └── common/            # Common utilities
├── tests/                 # Test files
├── scripts/               # Script files
├── logs/                  # Log files
└── manage.py             # Django management script
```

## API Interfaces

### Agent Flow Management
- `POST /api/agents/flows/` - Create flow
- `GET /api/agents/flows/` - Get flow list
- `POST /api/agents/flows/{id}/execute/` - Execute flow

### Knowledge Base Query
- `POST /api/knowledge/query/search/` - Search knowledge
- `GET /api/knowledge/entries/` - Get knowledge entries
- `POST /api/knowledge/entries/` - Create knowledge entry

## Development Guide

### Code Standards
- Follow PEP 8 Python coding standards
- Use type hints
- Write unit tests

### Running Tests
```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_agents/

# Generate test coverage report
pytest --cov=apps
```

## Deployment Instructions

### Production Environment Configuration
1. Set `DEBUG=False`
2. Configure production database
3. Set appropriate SECRET_KEY
4. Configure HTTPS
5. Set proper permissions and firewall rules

### Docker Deployment (Optional)
```bash
# Build image
docker-compose build

# Start services
docker-compose up -d
```

## Contribution Guidelines

1. Fork the project
2. Create feature branch
3. Commit changes
4. Submit Pull Request

## License

MIT License

## Contact

For any issues, please contact the project maintainer.