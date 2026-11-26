"""Check study lock and GPU/mount isolation without launching Docker."""
import fcntl
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class StudyLaneShellTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copy(Path(__file__).resolve().parents[1] / "run.sh", self.root)
        fakebin = self.root / "bin"
        fakebin.mkdir()
        for name, body in {"docker": 'printf "%s\\n" "$@"',
                           "git": 'if [ "$1" = rev-parse ]; then echo aabbccdd; fi'}.items():
            script = fakebin / name
            script.write_text("#!/bin/sh\n" + body + "\n")
            script.chmod(0o755)
        self.env = {"PATH": str(fakebin) + ":" + os.environ["PATH"], "STRETCH4_OPERATOR_STDIN": "1",
                    "PHYRC_STUDY_GPU_UUID": "GPU-abcd-1234"}
        for lane in ("demo33", "demo34", None):
            runtime = self.root / ".runtime"
            if lane:
                runtime = runtime / "study-lanes" / lane
            (runtime / "RCareWorld-2.0").mkdir(parents=True)
            garment = runtime / "PhyRC_Sim/Assets/Garment/Tops/Modelink/t_shirt_short.usd"
            garment.parent.mkdir(parents=True)
            garment.touch()

    def invoke(self, lane=None, command="python"):
        environment = dict(self.env)
        if lane:
            environment["PHYRC_STUDY_LANE"] = lane
        return subprocess.run(["bash", str(self.root / "run.sh"), command, "/scripts/collect_operator.py"],
                              env=environment, capture_output=True, text=True, timeout=5)

    def test_same_gpu_separate_writable_paths_keep_default_command_intact(self):
        for lane in ("demo33", "demo34", None):
            with self.subTest(lane=lane):
                result = self.invoke(lane)
                self.assertEqual(result.returncode, 0, result.stderr)
                argv = result.stdout.splitlines()
                expected_gpu = "device=GPU-abcd-1234" if lane else "all"
                self.assertEqual(argv[argv.index("--gpus") + 1], expected_gpu)
                self.assertIn("-i", argv)
                suffix = Path("study-lanes", lane) if lane else Path()
                self.assertIn(f"{self.root / '.runtime' / suffix}/PhyRC_Sim:/workspace/PhyRC_Sim:rw", argv)
                self.assertIn(f"{self.root / 'cache' / suffix}/ov:/isaac-sim/.cache/ov:rw", argv)

    def test_active_lane_locks_block_reuse_and_default_but_allow_the_peer(self):
        lockdir = self.root / "cache/study-lanes/demo33"
        lockdir.mkdir(parents=True)
        with (self.root / "cache/runtime.lock").open("w") as shared, (lockdir / "runtime.lock").open("w") as lane:
            fcntl.flock(shared.fileno(), fcntl.LOCK_SH)
            fcntl.flock(lane.fileno(), fcntl.LOCK_EX)
            self.assertIn("already active", self.invoke("demo33").stderr)
            self.assertIn("already has an active", self.invoke().stderr)
            self.assertEqual(self.invoke("demo34").returncode, 0)
        self.assertEqual(self.invoke("demo33").returncode, 0)

    def test_lane_refuses_noncollector_command_or_unprepared_directory(self):
        self.assertNotEqual(self.invoke("demo34", command="prepare").returncode, 0)
        self.assertIn("Prepare the study lane", self.invoke("missing").stderr)


if __name__ == "__main__":
    unittest.main()
