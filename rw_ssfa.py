import math

def rw_ssfa(Attach,Detach,Kirb,LGD,Granul,Mat,Senior):

    if Mat <1:
        Mat = 1
    elif Mat > 5:
        Mat = 5

    # Supervisory parameter

    if Senior==True and Granul >= 25:
        (A,B,C,D,E)=(0,3.56,-1.85,0.55,0.07)
    elif Senior == True and Granul < 25:
        (A,B,C,D,E)=(0.11,2.61,-2.91,0.68,0.07)
    elif Senior == False and Granul >= 25:
        (A,B,C,D,E)=(0.16,2.87,-1.03,0.21,0.07)
    elif Senior == False and Granul < 25:
        (A,B,C,D,E)=(0.22,2.35,-2.46,0.48,0.07)

    p_param = max(0.3,A+B/Granul + C*Kirb + D*LGD +E*Mat)

    a_param = -1/(p_param * Kirb)
    u_param = D - Kirb
    l_param = max(Attach-Kirb,0)

    Kssfa = (math.exp(a_param*u_param)-math.exp(a_param*l_param))/(a_param*(u_param-l_param))

    if Attach >= Kirb:
        return max(Kssfa * 12.5,0.15)
    elif Attach < Kirb and Detach > Kirb:
        return 12.5*(Kirb - Attach)/(Detach-Attach)+12.5*Kssfa*(Detach-Kirb)/(Detach-Attach)
    else:
        return Detach * 12.5
