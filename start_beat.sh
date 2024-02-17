echo "======================================================================"
echo "Welcome to the local beat setup for My Basket App"
echo "This will setup the local celery beat scheduler."
echo "Interval scheduled tasks for My Basket App will be run by this."
echo "======================================================================"

if [ -d "env" ];
then
   echo "Enabling virtual env"
else
   echo "No Virtual env. Please do the required configuration"
   exit N
fi

# Activate virtual env
. env/bin/activate
export ENV=LocalDevelopmentConfig
celery -A main:celery beat --max-interval 2 -l info
deactivate