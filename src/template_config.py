# src/template_config.py
import os

from fastapi.templating import Jinja2Templates

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# ROOT_PATH for subpath deployment (e.g. /tools3/taxi)
# Empty string in development, set via env var in production
root_path = os.environ.get("ROOT_PATH", "")

# Make root_path available in all templates as {{ root_path }}
templates.env.globals["root_path"] = root_path
