from pathlib import Path

from setuptools import setup


MODULE_NAME = "z_wizard_employee"
PACKAGE_ROOT = f"trytond.modules.{MODULE_NAME}"
BASE_DIR = Path(__file__).parent


setup(
    name=MODULE_NAME,
    version="4.2.0",
    description="GNU Health quick employee and party creation wizard",
    long_description=(BASE_DIR / "README.rst").read_text(encoding="utf-8"),
    long_description_content_type="text/x-rst",
    author="ALFA Custom",
    python_requires=">=3.10,<3.11",
    packages=[
        PACKAGE_ROOT,
        f"{PACKAGE_ROOT}.wizard",
    ],
    package_dir={
        PACKAGE_ROOT: ".",
        f"{PACKAGE_ROOT}.wizard": "wizard",
    },
    package_data={
        PACKAGE_ROOT: [
            "tryton.cfg",
            "README.rst",
            "view/*.xml",
            "wizard/*.xml",
            "data/messages/*.xml",
            "locale/*.po",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "trytond>=6.0,<6.1",
        "trytond_company>=6.0,<6.1",
        "gnuhealth==4.2.0",
        "trytond-z-health-employee-custom>=6.0,<6.1",
    ],
    entry_points={
        "trytond.modules": [
            f"{MODULE_NAME} = {PACKAGE_ROOT}",
        ],
    },
)
