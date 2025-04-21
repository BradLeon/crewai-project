from setuptools import setup, find_packages

setup(
    name="video_analysis_copy_write",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "crewai",
        "pydantic",
        "alibabacloud-quanmiaolightapp20240801",
        "alibabacloud-tea-openapi",
        "alibabacloud-tea-util",
        "alibabacloud-credentials",
    ],
    python_requires=">=3.8",
) 