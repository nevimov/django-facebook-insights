import os
from setuptools import setup, find_packages

if __name__ != '__main__':
    exit()

root_dir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(root_dir, 'README.rst')) as readme_file:
    long_description = readme_file.read()

with open(os.path.join(root_dir, 'VERSION')) as version_file:
    version = version_file.read().strip()

# Allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-facebook-insights',
    packages=find_packages(exclude=['tests']),
    install_requires=['facebook-sdk>=1,<3'],
    include_package_data=True,
    zip_safe=False,
    version=version,
    license='MIT',
    description='Collect and store Facebook Insights metrics using Django '
                'models.',
    long_description=long_description,
    author='nevimov',
    author_email='nevimov@gmail.com',
    url='https://github.com/nevimov/django-facebook-insights',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.7',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
    ],
    keywords='django facebook insights metrics stats statistics',
)
