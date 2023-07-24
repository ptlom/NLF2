# psu-quant-portfolio

## Installation

1. Download the projects.
2. Create a virtual environment. Run `pip install -r requirements.txt` to install dependencies. Run `pip freeze > requirements.txt` to add dependency.
```ssh
git clone https://github.com/artemmiyy/psu-quant-portfolio.git
pip install -r requirements.txt
```

## Credentials

1. Credentials are stored in `.streamlit/secrets.toml`. Make sure you have the `.streamlit/secrets.toml` before running any code.

### .streamlit/secrets.toml
```toml
DB_HOST=<Enter credentials here!>
DB_USER=<Enter credentials here!>
DB_PSWD=<Enter credentials here!>
DB_NAME="tradedb"
```

## Run streamlit app 
```ssh
streamlit run App.py
```
> Resources: https://docs.streamlit.io/

## Website
Website: https://psuquants.streamlit.app

