import numpy as np
import matplotlib.pyplot as plt
from plot_functions import *
from scipy import signal
from scipy.spatial import distance
from scipy import ndimage


from utils_ import *
from pressure_functions import *
from termConvection import *
from termreinit import *
from membrane_index import *


# Nb=50;dim=2;L=10
# Nb=100;dim=2;L=20
# Nb=150;dim=2;L=30
# Nb=200;dim=2;L=40
# Nb=250;dim=2;L=50
Nb=300;dim=2;L=60

#defining grid
x=np.linspace(0,L,Nb);y=np.linspace(0,L,Nb)
dsigma=x[1]-x[0]
grid=np.meshgrid(x, y,indexing='ij')

# center= [20, 10]  
center= [11,11]  
# center= [35, 30]  
radius = 2

def initialize_potential(grid,center,radius):    
    Y0 = np.zeros((Nb,Nb))
    for i in range(len(center)):
      Y0 = Y0 + (grid[i] - center[i])**2;
    Y0 = np.sqrt(Y0) - radius
    return Y0

def pressure_total(egfrp,A,mem_len,cur):
    
    pprot=pressure_pro(egfrp)
    pret=pressure_ret(egfrp)
    parea=pressure_area(A,A0,mem_len,egfrp)
    pten=pressure_tension(cur,radius)
    ptot=pprot+pret+parea-pten
    
    return [pprot,pret,parea,pten,ptot] 

def velocity_update(visco_l,ptot,Nv):
        
    kc=0.1 #nN/um3
    tauc=0.08 #nN/um3
    taua=0.1 #nNs/um3  
    
    [Nxm, Nym] = Nv
    
    [lx,ly]=visco_l
    ptotx=ptot*Nxm;ptoty=ptot*Nym
       
    vmx = -(kc/tauc)*lx + (1/tauc +1/taua)*ptotx
    vmy = -(kc/tauc)*ly + (1/tauc +1/taua)*ptoty
    
    return [vmx,vmy]   


def reinitialization(y, grid, dsigma, plot_reint=None,check_efficiency=None):
    
    NN=200  # |Phi|<=1.75 can be successfully reinitialized 
    Mod=[]
    Ys_reinit=[]
    sgnFactor=0#dsigma**2
    # a0=area(np.reshape(y, (Nb,Nb)))
    
    for i in range(NN):
        ydot,mag=reinit(y,grid,sgnFactor,dsigma,check_efficiency=True)
        y=y+0.001*ydot
        Mod.append(np.mean(mag))
        if plot_reint==True:
            Ys_reinit.append(np.reshape(y, (N,N)))
    # a=area(np.reshape(y, (Nb,Nb)))
    # print('area loss is '+str(a0-a))
    if plot_reint==True:
        plot3Dseq(Ys_reinit,grid)
    
    if check_efficiency==True:
        plt.figure()
        plt.plot(np.arange(1,NN+1),Mod,'k-')
        plt.axhline(y=1,ls='--',color='grey')
        plt.ylim(0,2)
        plt.xlim(0,NN)
        plt.ylabel('|Phi|')
        plt.xlabel('Iterations')
        plt.show()
    return y    


tF = 350
dt=0.01
t_eval = np.arange(0,tF,dt)
save = None


#initializing system
Y0=initialize_potential(grid,center,radius)
y0=np.ndarray.flatten(Y0)        
velocity0=np.zeros((Nb,Nb,dim))

L0x=np.zeros((Nb,Nb));L0y=np.zeros((Nb,Nb))

l0x=np.ndarray.flatten(L0x);l0y=np.ndarray.flatten(L0y)  


y=y0.copy();Y=Y0.copy()
velocity=velocity0.copy()
lx=l0x.copy();ly=l0y.copy()

A0=area(Y0)

print(folder_save)

#seed_int=801481 #folder 3
seed_int=13075 #folder 4
#seed_int=469022 #folder 5


shift=True
print('seed '+str(seed_int))

folder_kymo = 'C:\\Users\\nandan\\Dropbox\\Caesar\\EGFR memory paper_after science\\viscoelastic model\\20210806\\signalling module\\data\\'
egfrp_kymo = np.load(os.path.join(folder_kymo,'Kymograph_egfrp_seq_gradient_3_ihss_seed('+str(seed_int)+').npy'))

tt=[1000,5000,9000,11000,15000,19000]
if shift==True:
    egfrp_kymo = np.roll(egfrp_kymo,shift=-4,axis=0)
# egfrp_kymo = egfrp_kymo[:,2000:]
plot_kymo(egfrp_kymo,tt)

load=None
load_at = 140
# load_from = '\\\\billy.storage.mpi-dortmund.mpg.de\\abt2\\group\\agkoseska\\Temp_Storage(June2020)\\Akhilesh\\ViscoElasticModel\\20210610\\3\\'
# load_from = '\\\\billy.storage.mpi-dortmund.mpg.de\\abt2\\group\\agkoseska\\Temp_Storage(June2020)\\Abhishek\\ViscoElasticModel\\20210610\\1\\'
load_from = 'C:\\Users\\nandan\\Desktop\\soma_temp\\Viscoelastic simulations\\20210802\\9\\'


j=0
if load==True:
    j=load_at

# for i in range(int(load_at/0.1),len(t_eval)):  
for i in range(1,len(t_eval)):
# for i in range(5000,5001):    
# for i in range(20000,20001):  

    
    print(i,end='\r')
    
    # if i==792:
    #     print('stop')
    
    # if load==True and i==int(load_at/0.1):
    if load==True:
        Y= np.load(os.path.join(load_from,'potential_'+str(load_at)+'.npy'))
        Visco=np.load(os.path.join(load_from,'visco_'+str(load_at)+'.npy'))
        Lx=Visco[:,:,0];Ly=Visco[:,:,1]
        y=np.ndarray.flatten(Y)
        lx=np.ndarray.flatten(Lx);ly=np.ndarray.flatten(Ly)
    else:
        Y=np.reshape(y,(Nb,Nb))    
        Lx=np.reshape(lx,(Nb,Nb));Ly=np.reshape(ly,(Nb,Nb))

    cell_mask=masking_cell(Y)    
    membrane_annotated,pm_bins = membrane_sorted(cell_mask)
    # first_index = np.argwhere(membrane_annotated==0)
    membrane_indxs=membrane_indx_anticlockwise(membrane_annotated)
    mem_len=len(membrane_indxs[0])
              
    egfrp=egfrp_kymo[:,i]
    # 
    #     egfrp=np.roll(egfrp,-1)
    mask_overlayed = activity_overlaying(egfrp,pm_bins)
    egfrp = mask_overlayed[membrane_indxs]
    
    
    # curr_x=np.arange(len(egfrp))
    # new_x=np.linspace(0,len(egfrp),mem_len)
    # egfrp= np.interp(new_x, curr_x, egfrp)

    # mask_overlayed=cell_mask.copy()*np.nan
    # mask_overlayed[membrane_indxs]=egfrp
    # mask_overlayed[np.where(membrane_annotated==0)]=2*np.nanmax(mask_overlayed)

    
    Nv=normal_vectors(Y,dsigma)
    [Nvx,Nvy]=Nv
 
    A=area(Y)
    curvature_field=curvarure(Nv,dsigma)
    cur=curvature_field[membrane_indxs]
               
    [pprot,pret,parea,pten,ptot]  = pressure_total(egfrp,A,mem_len,cur)
        
    Nvxm, Nvym = Nvx[membrane_indxs], Nvy[membrane_indxs]
    visco_l = [Lx[membrane_indxs],Ly[membrane_indxs]]    
    vm=velocity_update(visco_l,ptot,[Nvxm, Nvym])
    [vmx,vmy]=vm
    
    
    # velocity[:,:,0]=nearest_neighbour_extrapolation(vmx,membrane_indxs,Nb)
    # velocity[:,:,1]=nearest_neighbour_extrapolation(vmy,membrane_indxs,Nb)
    # Ptot=nearest_neighbour_extrapolation(ptot,membrane_indxs,Nb)
    [velocity[:,:,0],velocity[:,:,1],Ptot] = nearest_neighbour_extrapolation([vmx,vmy,ptot],membrane_indxs,Nb)
    
    Ptotx=Ptot*Nvx;Ptoty=Ptot*Nvy
    
    ydot = f_potential(y, grid, velocity, dsigma)
    y = y + dt * ydot
 
    lxdot = f_visco(lx,lx,Ptotx,grid,velocity,dsigma)
    lydot = f_visco(ly,ly,Ptoty,grid,velocity,dsigma)
    lx = lx + dt * lxdot
    ly = ly + dt * lydot
    
    y=reinitialization(y, grid, dsigma, check_efficiency=None)
    

    if i%1==0:
        if i==10:
            save_grid=True
        else:
            save_grid=None
        
        pressure = np.zeros((Nb,Nb,dim))
        visco = np.zeros((Nb,Nb,dim))
        pressure[:,:,0]=Ptotx;pressure[:,:,1]=Ptoty
        visco[:,:,0]=Lx;visco[:,:,1]=Ly
        
        plot_membrane(mask_overlayed,lim=L,f=j)
        # plot_all_vectors([Ptotx,Ptoty],[-Lx,-Ly],[velocity[:,:,0],velocity[:,:,1]],grid,mask_overlayed,membrane_indxs,signal_pos=None,lim=L,f=j)
        
        
        # save_membrane_mask(mask_overlayed,save_grid,f=j)
        # save_other_quants(grid,Y,membrane_indxs,pressure,visco,velocity,save_grid,f=j)


        j=j+1
