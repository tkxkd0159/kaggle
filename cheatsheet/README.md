# Set up

```sh
python3 -m venv kgenv
source kgenv/bin/activate
pip freeze > requirements.txt # optional
pip install -r requirements.txt

python -m unittest discover . -v
```