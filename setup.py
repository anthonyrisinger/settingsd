# encoding: utf8


from setuptools import setup


setup(
    zip_safe=True,
    name='settingsd',
    version='0.8.7',
    description='settings.d',
    long_description='settings.d',
    url='https://github.com/xtfxme/settingsd',
    author='C Anthony Risinger',
    author_email='c@anthonyrisinger.com',
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        ],
    packages=[
        'settingsd',
        'settingsd.extras',
        ],
    )
