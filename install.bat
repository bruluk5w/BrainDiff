rem(){ :;};rem '
@goto batch
'

#bash
sudo apt-get update
sudo apt install python3-pip
sudo apt install python3.9-venv
python3.9 -m venv ./venv
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt
exit

:batch
pip install virtualenv
python -m venv ./venv
call venv/Scripts/activate
pip install --no-cache-dir -r requirements.txt --use-feature=in-tree-build
