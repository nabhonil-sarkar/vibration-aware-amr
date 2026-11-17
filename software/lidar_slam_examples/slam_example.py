#!/usr/bin/env python3
"""Educational local SLAM from A1 scans; estimates pose and builds a map."""
import argparse
import csv
import json
import math
import sys
from scans import add_arguments,prepare_output,source,bounded,clean_points,write_scan
from mapping import LocalSLAM

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    parser.add_argument('--map-size',type=float,default=20,help='Square map side in metres')
    parser.add_argument('--resolution',type=float,default=.05,help='Metres per map cell')
    args=parser.parse_args()
    slam=LocalSLAM(args.map_size,args.resolution)
    out=prepare_output(args,'slam')
    import matplotlib
    if not args.plot: matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,8))
    extent=[slam.origin,slam.origin+slam.size,slam.origin,slam.origin+slam.size]
    im=ax.imshow(slam.pixels(),origin='lower',extent=extent,cmap='gray',vmin=0,vmax=255)
    trail,=ax.plot([],[],color='#e55532',linewidth=1.5,label='Estimated sensor path')
    ax.set(xlabel='Map X (m)',ylabel='Map Y (m)',aspect='equal');ax.legend()
    if args.plot: plt.ion();plt.show()
    xs,ys=[],[]
    count,bad=0,0
    error=None
    try:
        with source(args) as stream, (out/'scans.jsonl').open('w',encoding='utf-8') as raw, (out/'trajectory.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f)
            writer.writerow(['scan','source_time','accepted','x_m','y_m','yaw_deg','match_rmse_m','status'])
            for scan in bounded(stream,args):
                write_scan(raw,scan)
                ok,status,rmse=slam.update(clean_points(scan))
                count+=1;bad=0 if ok else bad+1
                writer.writerow([count,scan.timestamp,ok,*slam.pose[:2],math.degrees(slam.pose[2]),rmse,status])
                if ok: xs.append(slam.pose[0]);ys.append(slam.pose[1])
                print(f'Scan {count}: {status}; x={slam.pose[0]:.2f} m y={slam.pose[1]:.2f} m yaw={math.degrees(slam.pose[2]):.1f} deg',flush=True)
                if args.plot:
                    if not plt.fignum_exists(fig.number): break
                    im.set_data(slam.pixels());trail.set_data(xs,ys)
                    ax.set_title('Local SLAM example - no loop closure');plt.pause(.001)
                if bad>=10:
                    raise RuntimeError('10 scans rejected in a row. Stop, return near last tracked pose, and start a new run.')
    except KeyboardInterrupt:
        print('\nStopped by user; saving results.')
    except Exception as exc:
        error=str(exc);print(f'ERROR: {error}',file=sys.stderr)
    finally:
        if slam.accepted==0 and error is None: error='No usable scans; map is empty'
        slam.save(out)
        im.set_data(slam.pixels());trail.set_data(xs,ys)
        ax.set_title(('SYNTHETIC DEMO - ' if args.demo else '')+'Local SLAM example / no loop closure')
        fig.savefig(out/'map.png',dpi=160);plt.close(fig)
        (out/'summary.json').write_text(json.dumps({'method':'scan-to-map ICP + occupancy grid; no loop closure',
          'source':'synthetic' if args.demo else str(args.replay or args.port),
          'accepted':slam.accepted,'rejected':slam.rejected,'final_pose_m_m_rad':slam.pose.tolist(),
          'map_resolution_m':slam.resolution,'error':error},indent=2),encoding='utf-8')
        print('Saved:',out.resolve())
    return 1 if error else 0

if __name__=='__main__': sys.exit(main())
