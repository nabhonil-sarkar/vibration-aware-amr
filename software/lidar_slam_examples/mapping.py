"""Educational local SLAM: scan-to-map ICP + occupancy grid, no loop closure."""
import math
import numpy as np
from scipy.spatial import cKDTree

def rotation(theta):
    c,s = math.cos(theta),math.sin(theta)
    return np.array([[c,-s],[s,c]])

def transform(points, pose):
    return points @ rotation(pose[2]).T + pose[:2]

def wrap(theta):
    return (theta+math.pi) % (2*math.pi)-math.pi

def align(points, reference, initial, gate=.3):
    """Trimmed point-to-point ICP; return pose, RMSE and match fraction."""
    tree=cKDTree(reference)
    pose=np.array(initial,dtype=float).copy()
    for _ in range(25):
        moved=transform(points,pose)
        distances,indices=tree.query(moved)
        valid=distances<gate
        if valid.sum()<30:
            return pose,float('inf'),float(valid.mean())
        cutoff=np.quantile(distances[valid],.85)
        keep=valid & (distances<=cutoff)
        a,b=moved[keep],reference[indices[keep]]
        ac,bc=a.mean(axis=0),b.mean(axis=0)
        u,_,vt=np.linalg.svd((a-ac).T @ (b-bc))
        r=vt.T @ u.T
        if np.linalg.det(r)<0:
            vt[-1]*=-1
            r=vt.T @ u.T
        shift=bc-r@ac
        turn=math.atan2(r[1,0],r[0,0])
        pose[:2]=r@pose[:2]+shift
        pose[2]=wrap(pose[2]+turn)
        if np.linalg.norm(shift)<1e-5 and abs(turn)<1e-5:
            break
    distances,_=tree.query(transform(points,pose))
    valid=distances<gate
    rmse=float(np.sqrt(np.mean(distances[valid]**2))) if valid.any() else float('inf')
    return pose,rmse,float(valid.mean())

def line_cells(x0,y0,x1,y1):
    """Integer Bresenham ray, inclusive at both ends."""
    dx,dy=abs(x1-x0),-abs(y1-y0)
    sx,sy=1 if x0<x1 else -1,1 if y0<y1 else -1
    err=dx+dy
    while True:
        yield x0,y0
        if x0==x1 and y0==y1:
            break
        e=2*err
        if e>=dy: err+=dy; x0+=sx
        if e<=dx: err+=dx; y0+=sy

class LocalSLAM:
    def __init__(self,size=20.0,resolution=.05):
        if size<=0 or resolution<=0:
            raise ValueError('Map size and resolution must be positive')
        self.n=int(round(size/resolution))
        if not 20<=self.n<=2000:
            raise ValueError('Choose between 20 and 2000 cells across the map')
        self.resolution=resolution
        self.size=self.n*resolution
        self.origin=-self.size/2
        self.grid=np.zeros((self.n,self.n),dtype=np.float32)
        self.pose=np.zeros(3)
        self.landmarks={}
        self.accepted=0
        self.rejected=0

    def index(self,point):
        return tuple(np.floor((point-self.origin)/self.resolution).astype(int))

    def inside(self,point):
        return np.all(point>=self.origin) and np.all(point<self.origin+self.size)

    def update(self,points):
        if len(points)<80:
            self.rejected+=1
            return False,'too few valid returns',None
        candidate=self.pose.copy()
        rmse=0.
        if self.landmarks:
            reference=np.array(list(self.landmarks.values()))
            candidate,rmse,fraction=align(points,reference,self.pose)
            if (fraction<.55 or rmse>.12 or np.linalg.norm(candidate[:2]-self.pose[:2])>.35
                    or abs(wrap(candidate[2]-self.pose[2]))>math.radians(15)):
                self.rejected+=1
                return False,'scan match rejected',rmse if math.isfinite(rmse) else None
        if not self.inside(candidate[:2]):
            self.rejected+=1
            return False,'sensor outside map',None
        self.pose=candidate
        world=transform(points,self.pose)
        self.integrate(world)
        for point in world:
            if self.inside(point):
                self.landmarks.setdefault(self.index(point),point.copy())
        # Bound work for this educational example; oldest landmarks fall out.
        while len(self.landmarks)>12000:
            self.landmarks.pop(next(iter(self.landmarks)))
        self.accepted+=1
        return True,'accepted',rmse

    def integrate(self,world):
        x0,y0=self.index(self.pose[:2])
        free,occupied=set(),set()
        for point in world:
            x1,y1=self.index(point)
            cells=list(line_cells(x0,y0,x1,y1))
            for x,y in cells[:-1]:
                if 0<=x<self.n and 0<=y<self.n:
                    free.add((x,y))
            if 0<=x1<self.n and 0<=y1<self.n:
                occupied.add((x1,y1))
        # Within each scan, a hit wins over a crossing free ray.
        for x,y in free-occupied: self.grid[y,x]=max(-4,self.grid[y,x]-.4)
        for x,y in occupied: self.grid[y,x]=min(4,self.grid[y,x]+.85)

    def pixels(self):
        image=np.full(self.grid.shape,205,dtype=np.uint8)
        image[self.grid < -.62]=254
        image[self.grid > .62]=0
        return image

    def save(self,out):
        pixels=np.flipud(self.pixels()) # PGM row 0 is top, grid row 0 is bottom.
        with (out/'map.pgm').open('wb') as f:
            f.write(f'P5\n{self.n} {self.n}\n255\n'.encode())
            f.write(pixels.tobytes())
        (out/'map.yaml').write_text(
            f'image: map.pgm\nmode: trinary\nresolution: {self.resolution}\n'
            f'origin: [{self.origin}, {self.origin}, 0.0]\nnegate: 0\n'
            'occupied_thresh: 0.65\nfree_thresh: 0.196\n',encoding='utf-8')
