# -*- coding: utf-8 -*-
"""
Created on Thu Jul  6 14:03:27 2023

@author: Bangchen Yin

The dimer engine of model devi
"""
import os
import argparse
from ase.build import bulk
from ase import Atom, Atoms
from ase.dimer import DimerControl, MinModeAtoms, MinModeTranslate
from ase.visualize import view
from ase.constraints import FixAtoms
from ase.io import read,write
from ase.io.trajectory import Trajectory
from deepmd.infer import calc_model_devi
from deepmd.calculator import DP
import numpy as np
import faulthandler
def write_lamptrj(atoms,forces,step):
    f_conf=open("conf.lmp","r")
    lines=f_conf.readlines()
    for line in lines:
        if "atom types" in line:
            n_atoms=int(line.split()[0])
    fname="./traj/"+str(step)+".lammpstrj"
   
    posname="./traj/"+str(step)+".poscar"
    f=open(fname,"w")
    f.write("ITEM: TIMESTEP\n")
    f.write(str(step)+'\n')
    f.write("ITEM: NUMBER OF ATOMS\n")
    f.write(str(len(atoms))+'\n')
    f.write("ITEM: BOX BOUNDS xy xz yz pp pp pp\n")
    o_line="0.00 "+str(atoms.cell[0][0])+" 0.00\n"
    t_line="0.00 "+str(atoms.cell[1][1])+" 0.00\n"
    th_line="0.00 "+str(atoms.cell[2][2])+" 0.00\n"
    f.write(o_line)
    f.write(t_line)
    f.write(th_line)
    print(atoms.cell)
    f.write("ITEM: ATOMS id type x y z fx fy fz\n")
    count=1
    pre=""
    for atom in atoms:
        xyz=atom.position
        f.write(str(atom.index+1)+" ")
        if(atom.symbol==pre)or(pre==""):
          f.write(str(count)+" ")
        else:
            count+=1
            f.write(str(count)+" ")
        pre=atom.symbol
        for ii in xyz:
            f.write(str(ii)+" ")
        for idf in forces[atom.index]:
            f.write(str(idf)+" ")
        f.write("\n")


def main(args):
    current_directory = os.getcwd()
    parent_directory_1 = os.path.dirname(current_directory)
    parent_directory_2 = os.path.dirname(parent_directory_1)
    pa3 = os.path.dirname(parent_directory_2)
    atoms=read(pa3+"/Data/devi/00/POSCAR")
    if args.fix:
        #TODO:YOU can modify different ways to fix atoms here, if you want to fix atoms[i], then just make the mask[i]=True
      mask=[atom.index<args.index for atom in atoms]
      atoms.set_constraint(FixAtoms(mask=mask))
    atoms.calc = DP(model="../graph.001.pb")
        #TODO: YOU can also change the ways of displacement for your own example, we basically provide the gaussian displacement.
        #More information could be found at https://wiki.fysik.dtu.dk/ase/ase/dimer.html
    with DimerControl(initial_eigenmode_method='displacement',maximum_translation=args.trans,
                      displacement_method='gauss', displacement_center=18,dimer_separation=0.0005,displacement_radius=args.radius,logfile=None, #TODO: make it adjustable
                      ) as d_control:
        d_atoms = MinModeAtoms(atoms, d_control)
        d_atoms.displace()
        with MinModeTranslate(d_atoms, trajectory='dimer_method.traj',
                              logfile='log') as dim_rlx:
            dim_rlx.run(fmax=0.02,steps=200)
            traj = Trajectory('dimer_method.traj')
            if not os.path.exists("traj"):
              os.system("mkdir traj")
            count=0
            box=[]
            coor=[]
            atype=[]
            k=0
            pre=""
            for atom in atoms:
               if atom.symbol != pre:
                 pre=atom.symbol
                 k+=1
               atype.append(k-1)
            for atoms in traj:
                if box ==[]:
                    box= np.array(atoms.cell).reshape([1,-1])[0]
                else:
                   box=np.append(box,np.array(atoms.cell).reshape([1,-1])[0])
                if coor==[]:
                    coor=np.array(atoms.positions).reshape([1,-1])[0]
                else:
                    coor=np.append(coor,np.array(atoms.positions).reshape([1,-1])[0])
                forces= np.zeros([len(atoms),3])
                write_lamptrj(atoms,forces,count)
                 
                 
                count+=1
          
            coor=np.array([coor])
            box=np.array([box])
            from deepmd.infer import DeepPot as DPot
            graphs = [DPot("../graph.000.pb"), DPot("../graph.001.pb"), DPot("../graph.002.pb"), DPot("../graph.003.pb")]
            model_devi = calc_model_devi(coor, box, atype, graphs,fname="model_devi.out",frequency=1)
            print("finish!") 
 



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fix", type=bool,default=False, help="Whether to fix the atoms")
    parser.add_argument("index", type=int,default=-1, help="atom's tag<index will be fixed")
    parser.add_argument("trans",type=float,default=0.1,help="max step size")
    parser.add_argument("center",type=int,default=0,help="displace center")
    parser.add_argument("radius",type=float,default=2,help="displace radius")


    args = parser.parse_args()
    main(args)
