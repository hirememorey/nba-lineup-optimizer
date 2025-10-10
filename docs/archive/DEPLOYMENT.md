# NBA Lineup Optimizer - Production Deployment Guide

This guide covers deploying the NBA Lineup Optimizer to production with authentication, monitoring, and security features.

## Prerequisites

- Python 3.9+
- Docker and Docker Compose (for containerized deployment)
- Access to the NBA Stats API
- Sufficient disk space for data storage (minimum 2GB)

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd nba-lineup-optimizer

# Copy environment configuration
cp env.example .env

# Edit the environment file with your settings
nano .env
```

### 2. Data Pipeline

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements_streamlit.txt

# Run the data pipeline
python master_data_pipeline.py --season 2024-25

# Generate model coefficients
python run_production_model.py
```

### 3. Production Deployment

#### Option A: Docker Deployment (Recommended)

```bash
# Build and start the application
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop the application
docker-compose down
```

#### Option B: Direct Python Deployment

```bash
# Run the production dashboard
python run_production_dashboard.py
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Environment mode | `production` | Yes |
| `SECRET_KEY` | Secret key for sessions | - | Yes |
| `ENABLE_AUTH` | Enable authentication | `true` | No |
| `ADMIN_PASSWORD` | Admin user password | - | Yes (if auth enabled) |
| `USER_PASSWORD` | Regular user password | - | Yes (if auth enabled) |
| `DATABASE_PATH` | Path to database file | `src/nba_stats/db/nba_stats.db` | Yes |
| `MODEL_COEFFICIENTS_PATH` | Path to model coefficients | `model_coefficients.csv` | No |
| `API_RATE_LIMIT` | API rate limit (requests/hour) | `100` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Security Configuration

1. **Change Default Passwords**: Update `ADMIN_PASSWORD` and `USER_PASSWORD` in production
2. **Set Strong Secret Key**: Generate a secure `SECRET_KEY` for session management
3. **Enable HTTPS**: Use a reverse proxy (nginx) with SSL certificates
4. **Network Security**: Restrict access to the application port

## Monitoring

### Logs

- Application logs: `logs/app.log`
- Production runner logs: `logs/production.log`
- Metrics: `logs/metrics.json`

### Health Checks

- Application health: `http://localhost:8502/_stcore/health`
- Nginx health: `http://localhost/health`

### Metrics

The application tracks:
- Total requests
- Model evaluations
- Average response time
- Error rate
- System uptime

## Troubleshooting

### Common Issues

1. **Database Not Found**
   ```bash
   # Check if database exists
   ls -la src/nba_stats/db/nba_stats.db
   
   # Run data pipeline if missing
   python master_data_pipeline.py --season 2024-25
   ```

2. **Model Coefficients Missing**
   ```bash
   # Generate model coefficients
   python run_production_model.py
   ```

3. **Authentication Issues**
   ```bash
   # Check environment variables
   echo $ADMIN_PASSWORD
   echo $USER_PASSWORD
   
   # Disable auth for testing
   export ENABLE_AUTH=false
   ```

4. **Port Already in Use**
   ```bash
   # Check what's using port 8502
   lsof -i :8502
   
   # Kill the process or change port
   export STREAMLIT_SERVER_PORT=8503
   ```

### Performance Issues

1. **Slow Model Loading**
   - Check if model coefficients are cached
   - Monitor memory usage
   - Consider increasing `MODEL_CACHE_SIZE`

2. **High Memory Usage**
   - Reduce `MODEL_CACHE_SIZE`
   - Restart the application periodically
   - Monitor with `docker stats` or `htop`

## Security Considerations

### Production Checklist

- [ ] Changed default passwords
- [ ] Set strong secret key
- [ ] Enabled HTTPS with valid certificates
- [ ] Configured firewall rules
- [ ] Set up log rotation
- [ ] Implemented backup strategy
- [ ] Configured monitoring alerts
- [ ] Tested disaster recovery procedures

### Data Protection

- Database files contain sensitive player data
- Ensure proper file permissions (600 for database files)
- Regular backups of database and model files
- Secure transmission of all data

## Scaling

### Horizontal Scaling

- Use load balancer with multiple application instances
- Implement session storage (Redis) for authentication
- Use shared database storage

### Vertical Scaling

- Increase memory for larger model caches
- Use faster storage for database files
- Optimize model loading and caching

## Maintenance

### Regular Tasks

1. **Data Updates**: Run data pipeline for new seasons
2. **Model Retraining**: Update model coefficients periodically
3. **Log Rotation**: Implement log rotation to prevent disk space issues
4. **Security Updates**: Keep dependencies updated
5. **Backup Verification**: Test backup and recovery procedures

### Monitoring

- Set up alerts for high error rates
- Monitor disk space usage
- Track response times and user activity
- Monitor system resource usage

## Support

For issues and questions:
1. Check the logs for error messages
2. Review this documentation
3. Check the project's issue tracker
4. Contact the development team

## License

This project is licensed under the MIT License. See LICENSE file for details.
