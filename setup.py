from setuptools import setup, find_packages

def parse_requirements(filename):
    """Parse les dépendances depuis un fichier requirements.txt."""
    requirements = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Gérer les options comme --index-url
            if line.startswith('--'):
                continue
            # Nettoyer la ligne
            requirement = line.split(';')[0].strip()
            if requirement:
                requirements.append(requirement)
    return requirements

# Installer PyTorch séparément avec ses options
install_requires = parse_requirements('requirements.txt')

# Ajouter PyTorch avec l'index spécifique
dependency_links = [
    'torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu'
]

setup(
    name="mcp-crawl4ai-rag",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=install_requires,
    dependency_links=dependency_links,
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "mcp-crawl4ai-rag=crawl4ai_mcp:main",
        ],
    },
)
