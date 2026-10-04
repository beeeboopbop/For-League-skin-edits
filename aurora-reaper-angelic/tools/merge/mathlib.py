import numpy as np
def qmat(q):
    x,y,z,w=q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def trs(t,q,s):
    M=np.eye(4); M[:3,:3]=qmat(q)@np.diag(s); M[:3,3]=t; return M
def decompose(M):
    t=M[:3,3].copy(); A=M[:3,:3]; s=np.linalg.norm(A,axis=0); R=A/s
    tr=R.trace()
    if tr>0:
        S=np.sqrt(tr+1)*2; w=0.25*S; x=(R[2,1]-R[1,2])/S; y=(R[0,2]-R[2,0])/S; z=(R[1,0]-R[0,1])/S
    elif R[0,0]>R[1,1] and R[0,0]>R[2,2]:
        S=np.sqrt(1+R[0,0]-R[1,1]-R[2,2])*2; w=(R[2,1]-R[1,2])/S; x=0.25*S; y=(R[0,1]+R[1,0])/S; z=(R[0,2]+R[2,0])/S
    elif R[1,1]>R[2,2]:
        S=np.sqrt(1+R[1,1]-R[0,0]-R[2,2])*2; w=(R[0,2]-R[2,0])/S; x=(R[0,1]+R[1,0])/S; y=0.25*S; z=(R[1,2]+R[2,1])/S
    else:
        S=np.sqrt(1+R[2,2]-R[0,0]-R[1,1])*2; w=(R[1,0]-R[0,1])/S; x=(R[0,2]+R[2,0])/S; y=(R[1,2]+R[2,1])/S; z=0.25*S
    return t,np.array([x,y,z,w]),s
