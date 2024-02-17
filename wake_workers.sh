echo "======================================================================"
echo "Welcome to the local workers setup for My Basket App"
echo "This will setup the local celery workers."
echo "Workers will be listening for tasks to be run."
echo "======================================================================"

if [ -d "env" ];
then
   echo "Enabling virtual env"
else
   echo "No Virtual env. Please run tools.sh first"
   exit N
fi

# Activate virtual env
. env/bin/activate
export ENV=LocalDevelopmentConfig
celery -A main:celery worker --loglevel=info -P gevent
deactivate
