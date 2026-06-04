"""model_asset detector 单元测试。

验证 SimulationFileTypeDetector 的文件类型检测逻辑，包括扩展名匹配、
OpenFAST 标记检测和 guess_from_filename 方法。

被验证对象：
- whale.model_asset.detector: SimulationFileTypeDetector

测试阶段：开发期验证 (unit，无外部依赖)。
不能证明：真实文件系统的文件头读取在各平台的一致性。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from whale.model_asset.detector import SimulationFileTypeDetector
from whale.model_asset.models import SimulationFileType


class TestSimulationFileTypeDetector:
    """SimulationFileTypeDetector 单元测试。"""

    def setup_method(self) -> None:
        """初始化检测器实例。"""
        self.detector = SimulationFileTypeDetector()

    # ---- 扩展名测试 ----

    def test_detect_fast_fst(self) -> None:
        """验证 .fst 文件检测为 FAST（不含 OpenFAST 标记时）。"""
        with tempfile.NamedTemporaryFile(suffix=".fst", mode="w", delete=False) as f:
            f.write("FAST simulation input")
        try:
            result = self.detector.detect(f.name)
            assert result == SimulationFileType.FAST
        finally:
            Path(f.name).unlink()

    def test_detect_fast_dot_fast(self) -> None:
        """验证 .fast 文件检测为 FAST。"""
        assert (
            self.detector.guess_from_filename("model.fast") == SimulationFileType.FAST
        )

    def test_detect_fast_fstf(self) -> None:
        """验证 .fstf 文件检测为 FAST。"""
        assert (
            self.detector.guess_from_filename("model.fstf") == SimulationFileType.FAST
        )

    def test_detect_openfast_yaml_with_marker(self) -> None:
        """验证含 OpenFAST 标记的 .yaml 文件检测为 OPENFAST。"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            f.write("openfast:\n  version: 3.5\n  inputs:")
        try:
            result = self.detector.detect(f.name)
            assert result == SimulationFileType.OPENFAST
        finally:
            Path(f.name).unlink()

    def test_detect_openfast_fst_with_marker(self) -> None:
        """验证含 OpenFAST 标记的 .fst 文件检测为 OPENFAST。"""
        with tempfile.NamedTemporaryFile(suffix=".fst", mode="w", delete=False) as f:
            f.write("OpenFAST 3.5.0\n\n---\n# input file")
        try:
            result = self.detector.detect(f.name)
            assert result == SimulationFileType.OPENFAST
        finally:
            Path(f.name).unlink()

    def test_detect_fst_without_openfast_marker(self) -> None:
        """验证不含 OpenFAST 标记的 .fst 文件检测为 FAST。"""
        with tempfile.NamedTemporaryFile(suffix=".fst", mode="w", delete=False) as f:
            f.write("------- FAST v8 INPUT FILE ------\nSome content")
        try:
            result = self.detector.detect(f.name)
            assert result == SimulationFileType.FAST
        finally:
            Path(f.name).unlink()

    def test_detect_openfast_fstproj(self) -> None:
        """验证 .fstproj 文件检测为 OPENFAST（含标记）。"""
        with tempfile.NamedTemporaryFile(suffix=".fstproj", mode="w", delete=False) as f:
            f.write('"openfast_project": "WF_001"')
        try:
            result = self.detector.detect(f.name)
            assert result == SimulationFileType.OPENFAST
        finally:
            Path(f.name).unlink()

    def test_detect_windfarm_wnd(self) -> None:
        """验证 .wnd 文件检测为 WINDFARM。"""
        assert (
            self.detector.guess_from_filename("farm.wnd") == SimulationFileType.WINDFARM
        )

    def test_detect_windfarm_wfp(self) -> None:
        """验证 .wfp 文件检测为 WINDFARM。"""
        assert (
            self.detector.guess_from_filename("layout.wfp") == SimulationFileType.WINDFARM
        )

    def test_detect_bladed_prj(self) -> None:
        """验证 .prj 文件检测为 BLADED。"""
        assert (
            self.detector.guess_from_filename("bladed.prj") == SimulationFileType.BLADED
        )

    def test_detect_bladed_bld(self) -> None:
        """验证 .bld 文件检测为 BLADED。"""
        assert (
            self.detector.guess_from_filename("bladed.bld") == SimulationFileType.BLADED
        )

    def test_detect_simulink_slx(self) -> None:
        """验证 .slx 文件检测为 SIMULINK。"""
        assert (
            self.detector.guess_from_filename("controller.slx") == SimulationFileType.SIMULINK
        )

    def test_detect_simulink_mdl(self) -> None:
        """验证 .mdl 文件检测为 SIMULINK。"""
        assert (
            self.detector.guess_from_filename("model.mdl") == SimulationFileType.SIMULINK
        )

    def test_detect_unknown_extension(self) -> None:
        """验证不支持的文件扩展名返回 UNSUPPORTED。"""
        assert (
            self.detector.guess_from_filename("data.csv") == SimulationFileType.UNSUPPORTED
        )
        assert (
            self.detector.guess_from_filename("readme.txt") == SimulationFileType.UNSUPPORTED
        )

    def test_detect_no_extension(self) -> None:
        """验证无扩展名文件返回 UNSUPPORTED。"""
        assert (
            self.detector.guess_from_filename("noextension") == SimulationFileType.UNSUPPORTED
        )

    # ---- guess_from_filename 测试 ----

    def test_guess_openfast_yaml(self) -> None:
        """验证 .yaml 文件名猜测为 OPENFAST（不访问文件系统）。"""
        assert (
            self.detector.guess_from_filename("config.yaml")
            == SimulationFileType.OPENFAST
        )

    def test_guess_fast_from_filename(self) -> None:
        """验证 .fst .fast .fstf 均猜为 FAST。"""
        assert (
            self.detector.guess_from_filename("test.fst") == SimulationFileType.FAST
        )
        assert (
            self.detector.guess_from_filename("test.fast") == SimulationFileType.FAST
        )
        assert (
            self.detector.guess_from_filename("test.fstf") == SimulationFileType.FAST
        )

    # ---- 边界情况 ----

    def test_detect_unreadable_file(self) -> None:
        """验证不可读文件返回 FAST（保守判断）。"""
        result = self.detector.detect("/nonexistent/path/file.fst")
        assert result == SimulationFileType.FAST

    def test_detect_empty_fst_file(self) -> None:
        """验证空 .fst 文件检测为 FAST。"""
        with tempfile.NamedTemporaryFile(suffix=".fst", mode="w", delete=False) as f:
            f.write("")
        try:
            result = self.detector.detect(f.name)
            assert result == SimulationFileType.FAST
        finally:
            Path(f.name).unlink()
