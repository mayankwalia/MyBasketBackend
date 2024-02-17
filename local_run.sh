#! /bin/sh
echo "======================================================================"
echo "This will run the main.py in the virtual env." 
echo "----------------------------------------------------------------------"
if [ -d "env" ];
then
    echo "Enabling virtual env"
else
    echo "No Virtual env. Please run setup.sh first"
    exit N
fi

# Activate virtual env
. env/bin/activate
export ENV=LocalDevelopmentConfig
python -m main
deactivate
