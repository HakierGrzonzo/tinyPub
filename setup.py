import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name = "tinypub-HakierGrzonzo",
    version = "2.0",
    author = "Grzegorz Koperwas",
    author_email = "Grzegorz.Koperwas.dev@gmail.com",
    description = "A console based epub ebook reader.",
    long_description = long_description,
    ong_description_content_type="text/markdown",
    url='https://github.com/HakierGrzonzo/tinyPub',
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop"
    ],
    entry_points={
        'console_scripts': [
            'tinypub=tinyPub.__main__:main'
          ]
    },
    python_requires='>=3.8.1'
)
