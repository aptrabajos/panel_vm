#!/usr/bin/env python3
"""
Setup script para Panel de VMs Manjaro
Permite instalación con: pip install .
"""

from setuptools import setup, find_packages
import os

# Leer el README para la descripción larga
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

setup(
    name='manjaro-vm-panel',
    version='1.0.0',
    description='Panel de control moderno para máquinas virtuales QEMU/KVM',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    author='Manjaro VM Panel Team',
    author_email='',
    url='https://github.com/tu-usuario/manjaro-vm-panel',
    license='MIT',
    
    # Módulos Python
    py_modules=[
        'main',
        'vm_manager',
        'ui',
        'notifications',
        'widgets',
        'debug_memory'
    ],
    
    # Dependencias
    install_requires=[
        'PyGObject>=3.42.0',
        'pycairo>=1.20.0',
    ],
    
    # Dependencias del sistema (informativo)
    extras_require={
        'system': [
            'gtk4',
            'libadwaita',
            'libvirt',
            'qemu',
        ],
    },
    
    # Archivos de datos
    data_files=[
        ('share/applications', ['manjaro-vm-panel.desktop']),
        ('share/manjaro-vm-panel', ['style.css']),
        ('share/doc/manjaro-vm-panel', [
            'README.md',
            'CHANGELOG_ERRORES.md',
            'CONFIGURACION_MANUAL.md',
            'comando.md'
        ]),
    ],
    
    # Scripts ejecutables
    entry_points={
        'console_scripts': [
            'manjaro-vm-panel=main:main',
        ],
    },
    
    # Clasificadores PyPI
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Systems Administration',
    ],
    
    python_requires='>=3.8',
    
    # Palabras clave
    keywords='qemu kvm libvirt virtualization vm manjaro gtk4 adwaita',
    
    # Incluir archivos adicionales
    include_package_data=True,
)
