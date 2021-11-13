import ebooklib
from ebooklib import epub

def create_directory_structure(book):
    # Abort with error if a directory already exists
    # Else create directories for source and build
    pass

def generate_conf(book):
    # Generate conf.py for sphinx by extracting title, author name, etc
    pass

def generate_rst(input_epub):
    # Generate ReST file for each chapter in ebook
    pass

def generate_index(input_epub):
    # Generate index.rst
    pass

def extract_images(input_epub):
    # Extract images from epub
    pass

def convert_epub(name, output_directory, sphinx_theme_name):
    # Read epub
    input_epub = epub.read_epub(name)
    # Create output directory structure
    create_directory_structure(output_directory)
    # Generate conf.py
    generate_conf(input_epub)
    # Generate ReST file for each chapter in ebook
    generate_rst(input_epub)
    # Generate index.rst
    generate_index(input_epub)
    # Extract images from epub
    extract_images(input_epub)
