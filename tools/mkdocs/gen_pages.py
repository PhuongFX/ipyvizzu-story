"""A module for generating pages."""

import os
from pathlib import Path
from typing import Union, Optional, List
import re

import yaml
import mkdocs_gen_files  # type: ignore


class MkdocsConfig:
    """A class for loading mkdocs configuration."""

    # pylint: disable=too-few-public-methods

    @staticmethod
    def _format_url(url: Optional[str]) -> Optional[str]:
        if url and url.endswith("/"):
            return url[:-1]
        return url

    @staticmethod
    def _format(config: dict) -> dict:
        if "site_url" in config:
            config["site_url"] = MkdocsConfig._format_url(config["site_url"])
        return config

    @staticmethod
    def load(config: Path) -> dict:
        """
        A method for loading mkdocs configuration from yaml file.

        Args:
            config: The path of the yaml configuration file.

        Returns:
            A dictionary that contains the mkdocs configuration.
        """

        with open(config, "rt", encoding="utf8") as f_yml:
            return MkdocsConfig._format(yaml.load(f_yml, Loader=yaml.FullLoader))


class IndexPages:
    """A class for creating navigation index files."""

    # pylint: disable=too-few-public-methods

    @staticmethod
    def _write_index_file(file: str, toc: list) -> None:
        for item in toc:
            if isinstance(item, str):
                IndexPages._write_str_index(file, item)
            elif isinstance(item, dict):
                IndexPages._write_dict_index(file, item)
            else:
                raise NotImplementedError(f"{item}")

    @staticmethod
    def _write_str_index(file: str, item: str) -> None:
        with mkdocs_gen_files.open(file, "a") as f_index:
            parts = item.split("/")
            part = parts[-1].replace(".md", "").capitalize()
            link = Path(item).relative_to(Path(file).parent)
            f_index.write(f"* [{part}]({link})\n")

    @staticmethod
    def _write_dict_index(file: str, item: dict) -> None:
        with mkdocs_gen_files.open(file, "a") as f_index:
            for key in item:
                if isinstance(item[key], str):
                    link = Path(os.path.relpath(item[key], Path(file).parent))
                    f_index.write(f"* [{key}]({link})\n")
                    continue
                if item[key] and isinstance(item[key], list):
                    if isinstance(item[key][0], str):
                        if item[key][0].endswith("index.md"):
                            link = Path(item[key][0]).relative_to(Path(file).parent)
                            f_index.write(f"* [{key}]({link})\n")
                            continue
                raise NotImplementedError(f"{item}")

    @staticmethod
    def generate(nav_item: Union[list, dict, str]) -> None:
        """
        A method for creating section indices for the navigation.

        Args:
            nav_item: Part of the navigation.
        """

        if isinstance(nav_item, list):
            if (
                nav_item
                and isinstance(nav_item[0], str)
                and nav_item[0].endswith("index.md")
            ):
                original = Path("docs", nav_item[0])
                if original.exists():
                    mkdocs_gen_files.set_edit_path(nav_item[0], nav_item[0])
                with mkdocs_gen_files.open(nav_item[0], "a") as f_index:
                    f_index.write("\n")
                IndexPages._write_index_file(file=nav_item[0], toc=nav_item[1:])
            for item in nav_item:
                IndexPages.generate(nav_item=item)
        elif isinstance(nav_item, dict):
            for key in nav_item:
                IndexPages.generate(nav_item=nav_item[key])


class Page:
    """A class for creating a page from a file outside the docs folder."""

    # pylint: disable=too-few-public-methods

    @staticmethod
    def generate(
        src: Path, dst: str, site: str, ipynbs: Optional[List[str]] = None
    ) -> None:
        """
        A method for generating a page.

        Args:
            src: Source path.
            dst: Destination path.
            site: Site url.
            ipynbs: List of html links that are ipynb files.
        """

        if ipynbs is None:
            ipynbs = []

        with open(src, "rt", encoding="utf8") as f_src:
            content = f_src.read()

        for match in re.finditer(
            rf"\[([^]]*)\]\(({site}/)([^]]*)(.html)([^]]*)?\)",
            content,
        ):
            if match[0] in ipynbs:
                content = content.replace(
                    match[0], f"[{match[1]}]({match[3]}.ipynb{match[5]})"
                )
            else:
                content = content.replace(
                    match[0], f"[{match[1]}]({match[3]}.md{match[5]})"
                )

        content = content.replace(f"{site}/", "./").replace(f"{site}", "./")

        mkdocs_gen_files.set_edit_path(dst, ".." / Path(dst).parent / Path(src).name)
        with mkdocs_gen_files.open(dst, "w") as f_dst:
            f_dst.write(content)


def main() -> None:
    """
    The main method.
    It prepares files for the documentation site.
    """

    config = MkdocsConfig.load(Path(__file__).parent / "mkdocs.yml")

    IndexPages.generate(nav_item=config["nav"])

    Page.generate(
        src=Path(__file__).parent / ".." / ".." / "README.md",
        dst="index.md",
        site=config["site_url"],
        ipynbs=[f"[HTML]({config['site_url']}/examples/complex/complex.html)"],
    )

    Page.generate(
        src=Path(__file__).parent / ".." / ".." / "CONTRIBUTING.md",
        dst="CONTRIBUTING.md",
        site=config["site_url"],
    )

    Page.generate(
        src=Path(__file__).parent / ".." / ".." / "CODE_OF_CONDUCT.md",
        dst="CODE_OF_CONDUCT.md",
        site=config["site_url"],
    )

    Page.generate(
        src=Path(__file__).parent / ".." / ".." / "LICENSE",
        dst="LICENSE.md",
        site=config["site_url"],
    )


main()
