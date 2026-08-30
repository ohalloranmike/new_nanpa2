from urllib.parse import urlencode

from fastapi import Request
from starlette.templating import Jinja2Templates


templates: Jinja2Templates | None = None


def init_templates(template_dir) -> Jinja2Templates:
    global templates
    templates = Jinja2Templates(directory=str(template_dir))
    return templates


def _path_param_names(request: Request, name: str) -> set[str]:
    for route in request.app.routes:
        if getattr(route, "name", None) == name and hasattr(route, "param_convertors"):
            return set(route.param_convertors.keys())
    return set()


def make_url_for(request: Request):
    def url_for(name: str, **kwargs):
        if name == "static":
            return f"/{kwargs['filename']}"

        path_names = _path_param_names(request, name)
        path_params = {key: value for key, value in kwargs.items() if key in path_names}
        query_params = {key: value for key, value in kwargs.items() if key not in path_names}

        base = str(request.url_for(name, **path_params))
        if query_params:
            return f"{base}?{urlencode(query_params)}"
        return base

    return url_for


def render(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    if templates is None:
        raise RuntimeError("Templates not initialized")

    ctx = dict(context or {})
    ctx["request"] = request
    ctx["db_last_updated"] = request.app.state.db_last_updated
    ctx["url_for"] = make_url_for(request)
    return templates.TemplateResponse(
        name,
        ctx,
        status_code=status_code,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )
