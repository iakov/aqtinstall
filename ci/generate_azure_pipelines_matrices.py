"""
This sets variables for a matrix of QT versions to test downloading against with Azure Pipelines
"""
import collections
import json
import secrets as random
import re
from itertools import product
from typing import Dict, Optional

MIRRORS = [
    "https://ftp.jaist.ac.jp/pub/qtproject",
    "https://ftp1.nluug.nl/languages/qt",
    "https://mirrors.dotsrc.org/qtproject",
]


class BuildJob:
    def __init__(
        self,
        command,
        qt_version,
        host,
        target,
        arch,
        archdir,
        *,
        module=None,
        mirror=None,
        subarchives=None,
        output_dir=None,
        list_options=None,
        spec=None,
        mingw_variant: str = "",
        is_autodesktop: bool = False,
        tool_options: Optional[Dict[str, str]] = None,
        check_output_cmd: Optional[str] = None,
        emsdk_version: str = "sdk-fastcomp-1.38.27-64bit@3.1.29",
        autodesk_arch_folder: Optional[str] = None,
    ):
        self.command = command
        self.qt_version = qt_version
        self.host = host
        self.target = target
        self.arch = arch
        self.archdir = archdir
        self.module = module
        self.mirror = mirror
        self.subarchives = subarchives
        self.mingw_variant: str = mingw_variant
        self.is_autodesktop: bool = is_autodesktop
        self.list_options = list_options if list_options else {}
        self.tool_options: Dict[str, str] = tool_options if tool_options else {}
        # `steps.yml` assumes that qt_version is the highest version that satisfies spec
        self.spec = spec
        self.output_dir = output_dir
        self.check_output_cmd = check_output_cmd
        self.emsdk_version = emsdk_version
        self.autodesk_arch_folder = autodesk_arch_folder

    def qt_bindir(self, *, sep='/') -> str:
        out_dir = f"$(Build.BinariesDirectory){sep}Qt" if not self.output_dir else self.output_dir
        version_dir = "5.9" if self.qt_version == "5.9.0" else self.qt_version
        return f"{out_dir}{sep}{version_dir}{sep}{self.archdir}{sep}bin"

    def win_qt_bindir(self) -> str:
        return self.qt_bindir(sep='\\')

    def autodesk_qt_bindir(self, *, sep='/') -> str:
        out_dir = f"$(Build.BinariesDirectory){sep}Qt" if not self.output_dir else self.output_dir
        version_dir = "5.9" if self.qt_version == "5.9.0" else self.qt_version
        return f"{out_dir}{sep}{version_dir}{sep}{self.autodesk_arch_folder or self.archdir}{sep}bin"

    def win_autodesk_qt_bindir(self) -> str:
        return self.autodesk_qt_bindir(sep='\\')

    def mingw_folder(self) -> str:
        if not self.mingw_variant:
            return ""
        match = re.match(r"^win(\d+)_(mingw\d+)$", self.mingw_variant)
        return f"{match[2]}_{match[1]}"


class PlatformBuildJobs:
    def __init__(self, platform, build_jobs):
        self.platform = platform
        self.build_jobs = build_jobs


python_versions = [
    "3.9",
]

qt_versions = ["5.13.2", "5.15.2"]

linux_build_jobs = []
mac_build_jobs = []
windows_build_jobs = []

all_platform_build_jobs = [
    PlatformBuildJobs("windows", windows_build_jobs),
]


# Windows Desktop
windows_build_jobs.extend(
    [
        BuildJob(
            "install-qt",
            "5.11.3",
            "windows",
            "desktop",
            "win64_msvc2015_64",
            "msvc2015_64",
            subarchives="qttools qtbase qtwinextras qtmultimedia",
            mirror=random.choice(MIRRORS),
        ),
        BuildJob(
            "install-qt",
            "5.11.3",
            "windows",
            "desktop",
            "win32_mingw53",
            "mingw53_32",
            mingw_variant="win32_mingw530",
#            module="qtcharts qtnetworkauth qtscript",
            subarchives="qttools qtbase qtwinextras qtmultimedia",
            mirror=random.choice(MIRRORS),
        )
    ]
)


qt_creator_bin_path = "./Tools/QtCreator/bin/"
qt_creator_mac_bin_path = "./Qt Creator.app/Contents/MacOS/"
qt_ifw_bin_path = "./Tools/QtInstallerFramework/*/bin/"
tool_options = {
    "TOOL1_ARGS": "tools_qtcreator qt.tools.qtcreator",
    "LIST_TOOL1_CMD": f"ls {qt_creator_bin_path}",
    "TEST_TOOL1_CMD": f"{qt_creator_bin_path}qbs --version",
    "TOOL2_ARGS": "tools_ifw",
    "TEST_TOOL2_CMD": f"{qt_ifw_bin_path}archivegen --version",
    "LIST_TOOL2_CMD": f"ls {qt_ifw_bin_path}",
}
# Mac Qt Creator is a .app, or "Package Bundle", so the path is changed:
tool_options_mac = {
    **tool_options,
    "TEST_TOOL1_CMD": f'"{qt_creator_mac_bin_path}qbs" --version',
    "LIST_TOOL1_CMD": f'ls "{qt_creator_mac_bin_path}"',
}
matrices = {}

for platform_build_job in all_platform_build_jobs:
    matrix_dictionary = collections.OrderedDict()

    for build_job, python_version in product(
        platform_build_job.build_jobs, python_versions
    ):
        key = "{} {} {} for {}".format(
            build_job.command, build_job.qt_version, build_job.arch, build_job.target
        )
        if build_job.spec:
            key = '{} (spec="{}")'.format(key, build_job.spec)
        if build_job.module:
            key = "{} ({})".format(key, build_job.module)
        if build_job.subarchives:
            key = "{} ({})".format(key, build_job.subarchives)
        if build_job.output_dir:
            key = "{} ({})".format(key, build_job.output_dir)
        matrix_dictionary[key] = collections.OrderedDict(
            [
                ("PYTHON_VERSION", python_version),
                ("SUBCOMMAND", build_job.command),
                ("QT_VERSION", build_job.qt_version),
                ("HOST", build_job.host),
                ("TARGET", build_job.target),
                ("ARCH", build_job.arch),
                ("ARCHDIR", build_job.archdir),
                ("MODULE", build_job.module if build_job.module else ""),
                ("QT_BASE_MIRROR", build_job.mirror if build_job.mirror else ""),
                ("SUBARCHIVES", build_job.subarchives if build_job.subarchives else ""),
                ("SPEC", build_job.spec if build_job.spec else ""),
                ("MINGW_VARIANT", build_job.mingw_variant),
                ("MINGW_FOLDER", build_job.mingw_folder()),
                ("IS_AUTODESKTOP", str(build_job.is_autodesktop)),
                ("HAS_WASM", build_job.list_options.get("HAS_WASM", "True")),
                ("OUTPUT_DIR", build_job.output_dir if build_job.output_dir else ""),
                ("QT_BINDIR", build_job.qt_bindir()),
                ("WIN_QT_BINDIR", build_job.win_qt_bindir()),
                ("EMSDK_VERSION", (build_job.emsdk_version+"@main").split('@')[0]),
                ("EMSDK_TAG",  (build_job.emsdk_version+"@main").split('@')[1]),
                ("WIN_AUTODESK_QT_BINDIR", build_job.win_autodesk_qt_bindir()),
                ("TOOL1_ARGS", build_job.tool_options.get("TOOL1_ARGS", "")),
                ("LIST_TOOL1_CMD", build_job.tool_options.get("LIST_TOOL1_CMD", "")),
                ("TEST_TOOL1_CMD", build_job.tool_options.get("TEST_TOOL1_CMD", "")),
                ("TOOL2_ARGS", build_job.tool_options.get("TOOL2_ARGS", "")),
                ("LIST_TOOL2_CMD", build_job.tool_options.get("LIST_TOOL2_CMD", "")),
                ("TEST_TOOL2_CMD", build_job.tool_options.get("TEST_TOOL2_CMD", "")),
                ("CHECK_OUTPUT_CMD", build_job.check_output_cmd or "")
            ]
        )

    matrices[platform_build_job.platform] = matrix_dictionary

print("Setting Variables below")
print(
    f"##vso[task.setVariable variable=windows;isOutput=true]{json.dumps(matrices['windows'])}"
)
print(
    f"##vso[task.setVariable variable=linux;isOutput=true]{''}"
)
print(
    f"##vso[task.setVariable variable=mac;isOutput=true]{''}"
)