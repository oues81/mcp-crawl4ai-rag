from setuptools import setup, find_packages

# Lire les dépendances depuis pyproject.toml
with open('pyproject.toml', 'r') as f:
    lines = f.readlines()
    
# Extraire les dépendances
dependencies = []
in_deps = False
for line in lines:
    line = line.strip()
    if line.startswith('dependencies = ['):
        in_deps = True
        continue
    if in_deps and line == ']':
        in_deps = False
        break
    if in_deps and line.startswith('"') and line.endswith('",'):
        dep = line.strip('"\'').rstrip(',').strip()
        if dep and not dep.startswith('#'):
            dependencies.append(dep)

# Configuration de base
setup(
    name="mcp-crawl4ai-rag",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=dependencies,
    python_requires=">=3.12",
    author="Windsurf Cascade",
    author_email="support@windsurf.ai",
    description="MCP Crawl4AI RAG Service",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/coleam00/mcp-crawl4ai-rag",
    classifiers=[
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
