from setuptools import find_packages, setup

setup(
    name="tutor_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "google-genai>=0.1.0",
        "rich>=13.0.0",
        "opentelemetry-api>=1.20.0",
        "opentelemetry-sdk>=1.20.0",
    ],
    entry_points={
        "console_scripts": [
            "tutor-agent=tutor_agent.cli:main",
        ],
    },
    python_requires=">=3.9",
)
