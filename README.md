# How to deploy
# How to deploy

## Prerequisites

- Install the [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/)
- Create a [Fly.io account](https://fly.io/app/sign-up)
- Log in: `flyctl auth login`

## Initial Setup

1. **Initialize the Fly app** (first time only):
   ```bash
   flyctl launch
   ```
   Follow the prompts to configure your app. This creates a `fly.toml` configuration file.

2. **Set environment variables**:
   ```bash
   flyctl secrets set ALLOWED_ORIGINS=https://your-frontend-domain.com
   ```
   Add any other required secrets from your `.env` file.

## Deployment

Deploy your application with:
```bash
flyctl deploy
```

This will:
- Build your Docker container
- Push it to Fly.io
- Deploy the new version

## Verify Deployment

Check the status:
```bash
flyctl status
```

View logs:
```bash
flyctl logs
```

Open your app:
```bash
flyctl open
```

## Configuration

Your `fly.toml` should include:

```toml
app = "your-app-name"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
```

## Updating

To deploy updates, simply run:
```bash
flyctl deploy
```

## Additional Commands

- Scale app: `flyctl scale count 2`
- SSH into container: `flyctl ssh console`
- View dashboard: `flyctl dashboard`