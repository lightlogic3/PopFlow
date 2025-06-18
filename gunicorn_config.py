import os
import sys
from dotenv import load_dotenv

# Get environment configuration file path
env_file = os.environ.get('ENV_FILE', '.env.prod')

# Check if environment variables have been loaded
if os.environ.get('ENV_LOADED') != 'true':
    print(f"Loading environment configuration: {env_file}")
    if not os.path.exists(env_file):
        print(f"Error: Environment configuration file {env_file} does not exist")
        sys.exit(1)

    try:
        load_dotenv(env_file, override=True)
        # Mark environment variables as loaded to prevent reloading
        os.environ['ENV_LOADED'] = 'true'
        print(f"Environment configuration loaded successfully: {env_file}")
    except Exception as e:
        print(f"Failed to load environment configuration: {e}")
        sys.exit(1)
else:
    print("Environment configuration already loaded, skipping reload")

# Prevent circular imports and duplicate configuration loading
os.environ['GUNICORN_WORKER'] = 'true'

# Get configuration from environment variables
daemon = True  # Ensure running in background
bind = f"{os.environ.get('APP_HOST', '0.0.0.0')}:{os.environ.get('APP_PORT', '8888')}"
# Change to single process multi-threaded mode
workers = 1  # Only use 1 worker process
threads = int(os.environ.get('GUNICORN_THREADS', '8'))  # Increase thread count to 8
worker_connections = int(os.environ.get('GUNICORN_WORKER_CONNECTIONS', '2000'))
loglevel = 'debug'  # Use debug level to log everything

# Set process file directory
pidfile = os.environ.get('GUNICORN_PIDFILE', './gunicorn.pid')
chdir = os.environ.get('GUNICORN_CHDIR', './') # Working directory

# Worker mode
worker_class = 'uvicorn.workers.UvicornWorker'  # Use asynchronous worker

# Set access log format
access_log_format = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'

# Set paths for access log and error log
log_dir = os.environ.get('GUNICORN_LOG_DIR', "./log")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
    
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', f"{log_dir}/gunicorn_access.log")
errorlog = os.environ.get('GUNICORN_ERROR_LOG', f"{log_dir}/gunicorn_error.log")
capture_output = True  # Capture application's stdout and stderr

# Preload application to avoid duplicate loading in worker processes
preload_app = os.environ.get('GUNICORN_PRELOAD', 'true').lower() == 'true' 