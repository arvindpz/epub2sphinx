import ebooklib
import jinja2
import os
import shutil
import click

from .book import Book
from .chapter import Chapter
from concurrent.futures import ThreadPoolExecutor
from jinja2 import Environment, PackageLoader
from tqdm import tqdm

templates_directory = os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates")

def extract_file(item, source_directory, extract_style):
    """Extracts the Image, CSS or Font file

    :param item: EpubItem to extract
    :type item: class:`ebook.epub.EpubItem`

    :param source_directory: Source directory to extract the file to
    :type source_directory: str

    :param extract_style: Decides if CSS and Font items should be extracted
    :type extract_style: bool
    """
    item_type = item.get_type()
    if (item_type == ebooklib.ITEM_IMAGE or item_type == ebooklib.ITEM_COVER):
        file_path = os.path.join(source_directory, item.file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as ext_file:
            ext_file.write(item.content)
    elif (extract_style and (item_type == ebooklib.ITEM_STYLE or item_type == ebooklib.ITEM_FONT)):
        file_path = os.path.join(source_directory, "_static", item.file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as ext_file:
            ext_file.write(item.content)
        return item.file_name

def generate_chapter(chapter_id, book, source_directory):
    """Generate ReST for each chapter and write to output file

    :param chapter_id: ID of the chapter
    :type chapter_id: str

    :param book: Book instance
    :type book: class:`ebook.epub.EpubItem`

    :param source_directory: Source directory to extract the file to
    :type source_directory: str
    """
    chapter = Chapter(book, chapter_id[0])
    # Create any parent directories as given in the filename
    os.makedirs(os.path.dirname(os.path.join(source_directory, chapter.file)), exist_ok=True)
    # Convert HTML to ReST
    if not chapter.convert():
        # Omit chapter from toctree
        return None
    chapter.write(source_directory)
    return chapter.file

class Converter:

    def __init__(self, file_name, output_directory, sphinx_theme_name,include_custom_css):
        self.book = Book(file_name)
        self.output_directory = output_directory
        self.source_directory = os.path.join(output_directory, 'source')
        self.static_files_directory = os.path.join(self.source_directory, '_static')
        self.theme = sphinx_theme_name
        self.include_custom_css = include_custom_css
        self.css_files = None

    def convert(self):
        # Create output directory structure
        click.echo("Creating directory structure")
        shutil.copytree(os.path.join(templates_directory,"makefiles"),
                        self.output_directory)
        os.makedirs(self.static_files_directory)

        with ThreadPoolExecutor() as executor:
            # Generate ReST file for each chapter in ebook
            self.book.toctree = list(filter(None, tqdm(
                executor.map(lambda x: generate_chapter(x, self.book, self.source_directory),
                             self.book.epub.spine),
                total=len(self.book.epub.spine),
                desc="Generating ReST files",
                colour='Blue')))
            # Extract other files from epub
            click.echo("Extracting images")
            self.css_files = list(filter(None, executor.map(
                lambda x: extract_file(x, self.source_directory, self.include_custom_css),
                self.book.epub.get_items())))
            print(self.css_files)

        # Render jinja templates
        click.echo("Generating conf.py and index.rst")
        jinja_env = Environment(
            loader=PackageLoader("epub2sphinx")
        )
        with open(os.path.join(self.source_directory,'conf.py'), 'x') as cf:
            if self.include_custom_css:
                cf.write(jinja_env.get_template('conf.py').render(book=self.book, theme=self.theme, css_files=self.css_files))
            else:
                cf.write(jinja_env.get_template('conf.py').render(book=self.book, theme=self.theme))
        with open(os.path.join(self.source_directory,'index.rst'), 'x') as of:
            of.write(jinja_env.get_template('index.rst').render(book=self.book))
