#!/usr/bin/env python3
"""Read A1 scans, print distances, record JSONL, save a view. No motor drive."""
import argparse
import json
import sys
import numpy as np
from scans import add_arguments,prepare_output,source,bounded,clean_points,write_scan

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    args=parser.parse_args()
    out=prepare_output(args,'lidar')
    import matplotlib
    if not args.plot: matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7,7))
    dots=ax.scatter([],[],s=4)
    ax.scatter([0],[0],c='red',marker='^',label='Sensor')
    ax.set(xlim=(-8,8),ylim=(-8,8),xlabel='Sensor X (m)',ylabel='Sensor Y (m)',aspect='equal')
    ax.grid(True);ax.legend()
    if args.plot: plt.ion();plt.show()
    count,total,valid=0,0,0
    last=np.empty((0,2))
    error=None
    try:
        with (out/'scans.jsonl').open('w',encoding='utf-8') as recording, source(args) as stream:
            for scan in bounded(stream,args):
                write_scan(recording,scan)
                last=clean_points(scan)
                count+=1;total+=len(scan.samples);valid+=len(last)
                nearest=f'{np.linalg.norm(last,axis=1).min():.2f} m' if len(last) else 'no valid return'
                print(f'Scan {count}: {len(last)} valid angular bins; nearest={nearest}',flush=True)
                if args.plot:
                    if not plt.fignum_exists(fig.number): break
                    dots.set_offsets(last);ax.set_title('Live LiDAR scan (not a map)')
                    plt.pause(.001)
    except KeyboardInterrupt:
        print('\nStopped by user; saving results.')
    except Exception as exc:
        error=str(exc);print(f'ERROR: {error}',file=sys.stderr)
    finally:
        if not count and error is None: error='No complete scans received'
        dots.set_offsets(last)
        ax.set_title(('SYNTHETIC DEMO - ' if args.demo else '')+'Latest LiDAR scan (not SLAM)')
        fig.savefig(out/'scan.png',dpi=160);plt.close(fig)
        (out/'summary.json').write_text(json.dumps({'source':'synthetic' if args.demo else str(args.replay or args.port),
             'scans':count,'raw_samples':total,'retained_angular_bins':valid,'error':error},indent=2),encoding='utf-8')
        print('Saved:',out.resolve())
    return 1 if error else 0

if __name__=='__main__': sys.exit(main())
