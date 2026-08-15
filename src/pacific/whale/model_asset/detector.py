"""仿真文件类型检测器。

根据文件扩展名和内容标记（magic bytes 或 YAML header）判断仿真文件类型，
不执行深度解析，仅基于表面特征分类。

支持的文件格式：
- .fst .fast .fstf -> FAST
- .fst .yaml .fstproj with OpenFAST marker -> OPENFAST
- .wnd .wfp -> WINDFARM
- .prj .bld -> BLADED
- .slx .mdl -> SIMULINK
- unknown -> OTHER / UNSUPPORTED
"""

from __future__ import annotations

from pathlib import Path

from pacific.whale.model_asset.models import SimulationFileType

# OpenFAST YAML 文件头标记（用于区分 FAST 和 OpenFAST 的 .fst 文件）
_OPENFAST_MARKER = "openfast"


class SimulationFileTypeDetector:
    """仿真文件类型检测器。

    根据文件扩展名和头部标记判断文件类型。不执行深度解析，
    仅基于表面特征（扩展名、miminal header）做出最佳判断。

    扩展名映射优先级：精确扩展名 > 宽松扩展名 > 标记检测。
    """

    # 精确扩展名映射：后缀 -> SimulationFileType
    _EXTENSION_MAP: dict[str, SimulationFileType] = {
        ".fast": SimulationFileType.FAST,
        ".fstf": SimulationFileType.FAST,
        ".wnd": SimulationFileType.WINDFARM,
        ".wfp": SimulationFileType.WINDFARM,
        ".prj": SimulationFileType.BLADED,
        ".bld": SimulationFileType.BLADED,
        ".slx": SimulationFileType.SIMULINK,
        ".mdl": SimulationFileType.SIMULINK,
    }

    # 可能同时匹配 FAST 和 OpenFAST 的扩展名
    _AMBIGUOUS_EXTENSIONS = {".fst", ".yaml", ".fstproj"}

    def detect(self, file_path: str | Path) -> SimulationFileType:
        """检测单个文件的仿真文件类型。

        先按精确扩展名匹配，再对歧义扩展名读取文件头判断是否为 OpenFAST。

        Args:
            file_path: 文件路径或名称。

        Returns:
            检测到的 SimulationFileType。无法识别时返回 UNSUPPORTED。
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        # 精确扩展名匹配
        if suffix in self._EXTENSION_MAP and suffix not in self._AMBIGUOUS_EXTENSIONS:
            return self._EXTENSION_MAP[suffix]

        # 歧义扩展名：尝试读取文件头区分 FAST 和 OpenFAST
        if suffix in self._AMBIGUOUS_EXTENSIONS:
            return self._detect_openfast_or_fast(path)

        # .fst 没有后缀的处理
        if suffix == ".fst":
            return self._detect_openfast_or_fast(path)

        return SimulationFileType.UNSUPPORTED

    def _detect_openfast_or_fast(self, path: Path) -> SimulationFileType:
        """区分 OpenFAST 和传统 FAST 文件。

        读取文件头部（前 2KB），搜索 OpenFAST 标记。
        如果文件不可读或太小，默认归类为 FAST。

        Args:
            path: 文件路径。

        Returns:
            OPENFAST 或 FAST。
        """
        try:
            # 只读前 2KB 用于标记检测，避免加载大文件
            content = path.read_text(encoding="utf-8", errors="replace")[:2048]
            if self._has_openfast_marker(content):
                return SimulationFileType.OPENFAST
            return SimulationFileType.FAST
        except (OSError, UnicodeDecodeError):
            # 不可读或非文本文件，归类为 FAST（保守判断）
            return SimulationFileType.FAST

    @staticmethod
    def _has_openfast_marker(content: str) -> bool:
        """检查文本内容是否包含 OpenFAST 标记。

        在大小写不敏感模式下匹配 openfast 关键字。

        Args:
            content: 文件头部文本内容。

        Returns:
            True 表示检测到 OpenFAST 标记。
        """
        return _OPENFAST_MARKER in content.lower()

    @staticmethod
    def guess_from_filename(filename: str) -> SimulationFileType:
        """仅根据文件名（不访问文件系统）猜测文件类型。

        适用于只有文件名字符串但无文件系统访问的场景（如 API 请求校验）。

        Args:
            filename: 文件名（可带路径，只用后缀判断）。

        Returns:
            猜测的 SimulationFileType。无法识别时返回 UNSUPPORTED。
        """
        suffix = Path(filename).suffix.lower()
        fast_extensions = {".fst", ".fast", ".fstf"}
        openfast_extensions = {".yaml", ".fstproj"}
        windfarm_extensions = {".wnd", ".wfp"}
        bladed_extensions = {".prj", ".bld"}
        simulink_extensions = {".slx", ".mdl"}

        if suffix in fast_extensions:
            return SimulationFileType.FAST
        if suffix in openfast_extensions:
            return SimulationFileType.OPENFAST
        if suffix in windfarm_extensions:
            return SimulationFileType.WINDFARM
        if suffix in bladed_extensions:
            return SimulationFileType.BLADED
        if suffix in simulink_extensions:
            return SimulationFileType.SIMULINK
        return SimulationFileType.UNSUPPORTED
