
import logging
from pathlib import Path
from shutil import copytree
from importlib import resources

from markdown import Markdown
from jinja2 import Environment, PackageLoader, TemplateNotFound

from tashwiki.config import Config
from tashwiki.utils import page_name_to_label
from tashwiki.wikilinks import WikiLinkExtension

logger = logging.getLogger()
env = Environment(
    loader=PackageLoader("tashwiki"),
)


def render_page(template, context):
    template = env.get_template(template)
    html = template.render(context)
    return html


def validate_meta(meta: dict) -> dict:
    for key, value in meta.items():
        if key in ("title", "author"):
            meta[key] = value[0]
        elif key == "template":
            tpl = value[0]
            try:
                env.get_template(tpl)
                meta[key] = tpl
            except TemplateNotFound:
                raise ValueError(f"Template '{tpl}' not found.")
        elif key == "categories":
            pass
        else:
            raise ValueError(f"Unknown meta field '{key}'.")
    return meta


def copy_static(output_dir: Path):
    with resources.as_file(resources.files("tashwiki.static")) as src_path:
        copytree(src_path, output_dir, dirs_exist_ok=True)


def build(config: Config):
    source_dir = Path(config.site_source_dir)
    output_dir = Path(config.site_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Building site to folder '{output_dir}'...")

    md = Markdown(extensions=[
        "meta",
        WikiLinkExtension(base_url="", end_url=".html")
    ])

    for md_file in source_dir.rglob("*.md"):
        html_content = md.convert(md_file.read_text(encoding="utf-8"))

        context = {
            "content": html_content,
            "title": page_name_to_label(md_file.stem),
            "author": config.site_author,
        }

        meta = validate_meta(md.Meta)
        template = meta.pop("template", "base.html")
        context.update(meta)

        rendered = render_page(template, context)

        out_path = output_dir / md_file.with_suffix(".html").name
        out_path.write_text(rendered, encoding="utf-8")

    copy_static(output_dir)
