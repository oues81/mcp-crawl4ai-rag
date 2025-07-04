"""
Configuration de setuptools pour la compatibilité avec les outils qui ne prennent pas encore en charge pyproject.toml.

Ce fichier est généré automatiquement et ne devrait pas être modifié manuellement.
Pour mettre à jour les dépendances, modifiez pyproject.toml et exécutez :

    poetry update
"""

import re
from pathlib import Path
from typing import Dict, List

from setuptools import find_packages, setup

# Fonction pour lire le contenu d'un fichier
def read_file(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8")

# Lire les métadonnées depuis pyproject.toml
def get_metadata() -> Dict[str, str]:
    pyproject_content = read_file("pyproject.toml")
    
    # Extraire les métadonnées de base
    metadata = {}
    
    # Extraire la version
    version_match = re.search(r'^version = "([^"]+)"', pyproject_content, re.MULTILINE)
    if version_match:
        metadata["version"] = version_match.group(1)
    
    # Extraire la description
    description_match = re.search(r'^description = "([^"]+)"', pyproject_content, re.MULTILINE)
    if description_match:
        metadata["description"] = description_match.group(1)
    
    # Extraire les auteurs
    authors_match = re.search(r'^authors = \[\s*\{\s*name = "([^"]+)"\s*,\s*email = "([^"]+)"\s*\}\s*\]', pyproject_content, re.MULTILINE | re.DOTALL)
    if authors_match:
        metadata["author"] = authors_match.group(1)
        metadata["author_email"] = authors_match.group(2)
    
    return metadata

# Lire les dépendances depuis pyproject.toml
def get_dependencies() -> List[str]:
    pyproject_content = read_file("pyproject.toml")
    
    # Trouver la section des dépendances
    deps_section_match = re.search(
        r'^\[tool\.poetry\.dependencies\]([^\[]*)\[',
        pyproject_content,
        re.MULTILINE | re.DOTALL
    )
    
    if not deps_section_match:
        return []
    
    deps_section = deps_section_match.group(1)
    
    # Extraire les dépendances
    dependencies = []
    for line in deps_section.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Ignorer les lignes qui ne sont pas des dépendances
        if '=' not in line or 'python' in line.lower():
            continue
        
        # Extraire le nom et la contrainte de version
        dep_match = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*["\']?([^\n\r"\']+)["\']?', line)
        if dep_match:
            dep_name = dep_match.group(1)
            dep_constraint = dep_match.group(2)
            
            # Nettoyer la contrainte de version
            dep_constraint = dep_constraint.strip('"\'')
            
            # Ajouter la dépendance
            dependencies.append(f"{dep_name}{dep_constraint}" if dep_constraint != "*" else dep_name)
    
    return dependencies

# Obtenir les métadonnées et les dépendances
metadata = get_metadata()
dependencies = get_dependencies()

# Configuration de setuptools
setup(
    name="mcp-crawl4ai-rag",
    version=metadata.get("version", "0.1.0"),
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=dependencies,
    python_requires=">=3.12",
    author=metadata.get("author", "Windsurf Cascade"),
    author_email=metadata.get("author_email", "support@windsurf.ai"),
    description=metadata.get("description", "MCP Crawl4AI RAG Service"),
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/coleam00/mcp-crawl4ai-rag",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="mcp crawl4ai rag nlp ai machine-learning",
    include_package_data=True,
    zip_safe=False,
)
