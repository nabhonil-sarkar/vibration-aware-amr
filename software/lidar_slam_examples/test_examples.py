import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from scans import Scan,clean_points,source,shutdown,replay,demo_scans,demo_pose,write_scan
from mapping import LocalSLAM,align,transform

class Tests(unittest.TestCase):
    def test_units_orientation_invalid_and_nearest_bin(self):
        scan=Scan(0,[(47,0,1000),(47,.2,2000),(47,90,2000),(0,180,500),
                     (47,270,0),(47,float('nan'),1),(47,20,9000)])
        points=clean_points(scan)
        np.testing.assert_allclose(points,[[1,0],[0,-2]],atol=1e-12)

    def test_known_transform(self):
        rng=np.random.default_rng(2)
        pts=rng.uniform(-2,2,(360,2))
        expected=np.array([.08,-.03,.025])
        pose,error,fraction=align(pts,transform(pts,expected),np.zeros(3))
        np.testing.assert_allclose(pose,expected,atol=1e-4)
        self.assertLess(error,1e-4)
        self.assertGreater(fraction,.99)

    def test_grid_free_hit_and_unknown(self):
        slam=LocalSLAM(size=4,resolution=.1)
        slam.integrate(np.array([[1.,0.]]))
        x,y=slam.index(np.array([1.,0.]))
        self.assertGreater(slam.grid[y,x],0)
        x,y=slam.index(np.array([.5,0.]))
        self.assertLess(slam.grid[y,x],0)
        self.assertEqual(slam.grid[0,0],0)

    def test_rejected_scan_does_not_change_map_or_pose(self):
        slam=LocalSLAM()
        scan=next(demo_scans())
        slam.update(clean_points(scan))
        before=slam.grid.copy();pose=slam.pose.copy()
        ok,_,_=slam.update(np.array([[1.,1.]]))
        self.assertFalse(ok)
        np.testing.assert_array_equal(before,slam.grid)
        np.testing.assert_array_equal(pose,slam.pose)

    def test_synthetic_motion_accuracy(self):
        slam=LocalSLAM()
        for scan in demo_scans(count=35):
            ok,status,_=slam.update(clean_points(scan))
            self.assertTrue(ok,status)
        truth=demo_pose(34,35)
        self.assertLess(np.linalg.norm(slam.pose[:2]-truth[:2]),.08)
        self.assertLess(abs(slam.pose[2]-truth[2]),np.deg2rad(2))

    def test_sdk_replay_discards_partial_ends(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'test.txt'
            angles=[200,300,0,90,200,300,0,90,200,300,0,90]
            path.write_text('\n'.join(f'theta: {a} Dist: 1000 Q: 47' for a in angles))
            scans=list(replay(path))
            self.assertEqual(len(scans),2)
            self.assertEqual(len(scans[0].samples),4)

    def test_record_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'test.jsonl'
            original=Scan(1.5,[(47,10.,1000.)])
            with path.open('w') as f:write_scan(f,original)
            restored=list(replay(path))[0]
            np.testing.assert_equal(restored.samples,original.samples)
            self.assertEqual(restored.timestamp,original.timestamp)

    def test_cleanup_after_processing_error(self):
        calls=[]
        class Fake:
            def __init__(self,*args,**kwargs):pass
            def get_info(self):return {}
            def get_health(self):return ('Good',0)
            def iter_scans(self,**kwargs):
                yield [(47,0,1000)]
                yield [(47,1,1000)]
            def stop(self):calls.append('stop');raise OSError('fake stop error')
            def stop_motor(self):calls.append('stop_motor')
            def disconnect(self):calls.append('disconnect')
        args=argparse.Namespace(demo=False,replay=None,port='fake')
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError,'processing'):
                with source(args,factory=Fake) as scans:
                    next(scans)
                    raise RuntimeError('processing failed')
        self.assertEqual(calls,['stop','stop_motor','disconnect'])

    def test_pgm_and_yaml_orientation(self):
        slam=LocalSLAM(size=2,resolution=.1)
        slam.grid[0,0]=4
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);slam.save(out)
            data=(out/'map.pgm').read_bytes().split(b'\n',3)[3]
            self.assertEqual(data[-20],0) # bottom-left cell is last image row
            self.assertEqual(data[0],205)
            self.assertIn('origin: [-1.0, -1.0, 0.0]',(out/'map.yaml').read_text())

if __name__=='__main__':unittest.main()
