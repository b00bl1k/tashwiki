
import logging
from pathlib import Path
from shutil import copytree
from importlib import resources

from markdown import Markdown
from jinja2 import Environment, PackageLoader, TemplateNotFound

from tashwiki.categories import Categories
from tashwiki.config import Config
from tashwiki.utils import page_name_to_label, label_to_page_name
from tashwiki.wikilinks import WikiLinkExtension

logger = logging.getLogger()
env = Environment(
    loader=PackageLoader("tashwiki"),
)


def render_page(out_path: Path, template: str, context: dict):
    template = env.get_template(template)
    html = template.render(context)
    out_path.write_text(html, encoding="utf-8")


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


def prepare_context(config: Config) -> dict:
    return {
        "author": config.site_author,
        "baseurl": config.site_baseurl,
        "language": config.site_language,
        "main_page": config.site_main_page,
        "categories_page": config.site_categories_page,
        "categories_url": label_to_page_name(config.site_categories_page) + ".html",
        "category_page": config.site_categories_page,
        "category_url": label_to_page_name(config.site_categories_page) + ".html",
    }


def build(config: Config):
    source_dir = Path(config.site_source_dir)
    output_dir = Path(config.site_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Building site to folder '{output_dir}'...")

    def build_link_class(page):
        page_name = label_to_page_name(page)
        page_path = (source_dir / page_name).with_suffix(".md")
        return "notfound" if not page_path.exists() else ""

    glob_context = prepare_context(config)
    categories = Categories(config.site_category_page)
    md = Markdown(extensions=[
        "meta",
        WikiLinkExtension(
            base_url=config.site_baseurl,
            end_url=".html",
            html_class=build_link_class,
        )
    ])

    # render each page

    for md_file in source_dir.rglob("*.md"):
        page_content = md.convert(md_file.read_text(encoding="utf-8"))
        page_name = md_file.stem
        page_title = page_name_to_label(page_name)
        page_context = {
            "page_content": page_content,
            "title": page_title,
        }
        page_context.update(glob_context)

        meta = validate_meta(md.Meta)
        page_template = meta.pop("template", "page.html")
        category_names = meta.pop("categories", [])
        page_context.update(meta)

        page_categories = []
        for category_name in category_names:
            category = categories.get_or_create(category_name)
            category.add_page(page_title)
            page_categories.append(category)

        page_context.update({"categories": page_categories})

        out_path = output_dir / md_file.with_suffix(".html").name
        render_page(out_path, page_template, page_context)

    # render categories index
    categories_template = "categories.html"
    categories_context = {
        "categories": list(categories),
        "title": config.site_categories_page,
    }
    categories_context.update(glob_context)
    out_path = (output_dir / config.site_categories_page).with_suffix(".html")
    render_page(out_path, categories_template, categories_context)

    # render each category
    for category in categories:
        category_template = "category.html"
        category_context = {
            "category": category,
            "title": f"{config.site_category_page}: {category.name}"
        }
        category_context.update(glob_context)
        out_path = output_dir / category.url
        render_page(out_path, category_template, category_context)

    copy_static(output_dir)
