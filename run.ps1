Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
npm i react-router-dom react

