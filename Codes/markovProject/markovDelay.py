#Database: https://www.cfa.harvard.edu/castles/
#Interesting References:
#https://towardsdatascience.com/from-scratch-bayesian-inference-markov-chain-monte-carlo-and-metropolis-hastings-in-python-ef21a29e25a
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
c =299792.458 #km/s
kmToMPc = 3.240779289666e-20

def r_dyer_roeder(z, omega_m0, omega_q0, alpha, alpha_x, m, h=0.001):
    """
        This function returns the value for r(z) given a set of cosmological
        parameters (\Omega_{m_0}, \Omega_{q_0}, \alpha, \alpha_x, m) solving
        numerically the Dyer-Roeder equation.

        Input:
        - z (float): redshift
        - (omega_m0, omega_q0, alpha, alpha_x, m) (floats): cosmological parameters
        - h (float): Length of integration steps

        Output:
        - r(z) (float)
    """
    def f_1(z):
        """
        This subfunction multiplies the second order derivative in the
        Dyer-Roeder equation.
        """
        return omega_m0*z+1+omega_q0*(1+z)**(m-2)*(1-1/(1+z)**(m-2))

    def f_2(z):
        """
        This subfunction multiplies the first order derivative in the
        Dyer-Roeder equation.
        """
        return (7*omega_m0*z/2+omega_m0/2+3+omega_q0*(1+z)**(m-2)*\
                ((m+4)/2-3/(1+z)**(m-2)))/(1+z)
    def f_3(z):
        """
        This subfunction multiplies the function r(z) in the
        Dyer-Roeder equation.
        """
        return (3/(2*(1+z)**4))*(alpha*omega_m0*(1+z)**3+alpha_x*m/3*\
                omega_q0*(1+z)**m)

    def F(z,r,v):
        """
        This subfunction is obtained clearing the second derivative of r(z)
        in the Dyer-Roeder equation.
        """
        return -(f_2(z)*v+f_3(z)*r)/f_1(z)

    N=int(z/h) #Number of steps

    z_0 = 0
    #Initial conditions
    r_0 = 0
    v_0 = 1/((1+z_0)**2*(omega_m0*z_0+1+omega_q0*(1+z_0)**(m-2)*\
            (1-1/(1+z_0)**(m-2)))**.5)

    #Numeric Integration Zone
    r = r_0
    v = v_0
    z = z_0

    for ii in range(N):
        #Runge Kutta Fourth Order
        r = r+h*v
        k1 = F(z, r, v)
        k2 = F(z+h/2, r, v+k1*h/2)
        k3 = F(z+h/2, r, v+k2*h/2)
        k4 = F(z+h, r, v+k3*h)
        v=v+h*(k1+2*k2+2*k3+k4)/6
        z += h
    return r

def cosmological_Distances(H_0,z_a, z_b, omega_m0, omega_q0, alpha, alpha_x, m):
    """
        The output of this function is the cosmological distance in function
        of the cosmological parameters, the redshift and the Hubble parameter.

        Input
        - H_0 (float): Hubble parameter
        - z_a,z_b (float): redshift
        - (omega_m0, omega_q0, alpha, alpha_x, m) (floats): cosmological parameters

        Output:
        - D (float): Cosmological distance
    """
    return c*r_dyer_roeder(abs(z_a-z_b), omega_m0, omega_q0, alpha, alpha_x, m)/H_0

def time_delay(th_1, th_2, H_0,z_d, z_s, omega_m0, omega_q0, alpha, alpha_x, m):
    """
        This function calculates the time delay, given the redshift of the source
        z_s, the redshift of the deflector z_d, the cosmological parameters and
        the angular positions of these two objects.

        Input
        - th_1, th_2 (float): angular positions
        - H_0 (float): Hubble parameter
        - z_s,z_d (float): redshift
        - (omega_m0, omega_q0, alpha, alpha_x, m) (floats): cosmological parameters

        Output:
        - Dt (float): time delay
    """
    D_d = cosmological_Distances(H_0,z_d, 0, omega_m0, omega_q0, alpha, alpha_x, m)
    D_ds = cosmological_Distances(H_0,z_d, z_s, omega_m0, omega_q0, alpha, alpha_x, m)
    D_s = cosmological_Distances(H_0,z_s, 0, omega_m0, omega_q0, alpha, alpha_x, m)

    DTheta_squared = abs(th_1**2-th_2**2)
    return (1+z_d)*D_d*D_s*DTheta_squared/(2*D_ds*c*kmToMPc)

def likelihood_Function(H_0, omega_m0, omega_q0, alpha,
        alpha_x, m, data):
        """
            This function returns the likelihood function given the set of
            cosmological parameters and the experimental data.

            Input
            - H_0 (float): Hubble parameter
            - (omega_m0, omega_q0, alpha, alpha_x, m) (floats): cosmological parameters
            - data (list of lists): set of data from the observations

            Output:
            - L (float): likelihood function
        """
        #Unpacking
        z_ds = [x[0] for x in data]
        z_ss = [x[1] for x in data]
        delta_ts = [x[2] for x in data]
        theta_is = [x[3] for x in data]
        theta_js = [x[4] for x in data]


        acumulator = 0
        for x in range(len(data)):
            acumulator -= (delta_ts[x]-time_delay(theta_is[x], theta_js[x], H_0,z_ds[x], z_ss[x], omega_m0, omega_q0, alpha, alpha_x, m))**2

        return acumulator

def model_Prior(H_0,omega_m0, omega_q0, alpha, alpha_x, m, deviations):
    """
        This prior distribution discards all the values that doesn't have
        physical meaning.

        Input
        - H_0 (float): Hubble parameter
        - (omega_m0, omega_q0, alpha, alpha_x, m) (floats): cosmological parameters
        - means (list): ordered list with the means of all the parameters
        - deviations (list): ordered list with the deviations of all the parameters

        Output:
        - Prior value (float): value of the prior function
    """
    parameters = [H_0,omega_m0, omega_q0, alpha, alpha_x, m]
    #Accept only valid cosmological parameters
    cond = H_0<0 or omega_m0>1 or omega_q0>1 or omega_m0<0 or omega_q0<0\
            or alpha<0 or alpha_x<0 or m<0 or (omega_m0+omega_q0)>1
    for ii in deviations:
        cond = cond or (ii<0)
    if cond:
        return 0
    return 1

def transition_Model(means, deviations):
    """
        This function chooses the new values to be compared with the last values
        using a normal like distribution for all the parameters.

        Input:
        - means (list): list with all the means of the cosmological parameters
        - deviations (list): list with all the deviations of the cosmological parameters

        Output:
        - l (list): list with the new means and deviations for the cosmological parameters,
        structured as follows: new_means+new_deviations
    """
    l = []
    hyperDeviations=[0.5, 0.05,0.05,.5,.5,.5]
    deviations = [0.5,0.01,0.01,0.5,0.5,0.5]
    for x,y in zip(means, deviations):
        l.append(np.random.normal(x,y))
    for x,y in zip(deviations,hyperDeviations):
        l.append(np.random.normal(x,y))
    return l


def acceptance_rule(old, new):
    """
        This function determines if accept or reject the new data, based on the
        detailed balance method.

        Input:
        - old (float): old value of detailed balance condition
        - new (float): new value of detailed balance condition

        Output:
        - (Bool): True if accepting, False if rejecting
    """
    if new>old:
        return True
    else:
        accept = np.random.uniform(0,1)
        return (accept < np.exp(new-old))

def metropolis_Hastings(param_init, iterations, deviations,data):
    """
        This function implements the Metropolis Hastings method for obtaining
        the best possible parameters from a set of data.

        Input:
        - param_init (list): initial parameters
        - iterations (int): number of iterations
        - deviations (list): initial deviations
        - data (list of lists): experimental data
    """
    #Order of Data
    # H_0,omega_m0, omega_q0, alpha, alpha_x, m

    x = param_init
    accepted = []
    rejected = []
    likely_accepted = []
    x = x+deviations
    for ii in range(iterations):
        x_new =  transition_Model(x[:6], x[6:])
        x_lik = likelihood_Function(x[0], x[1], x[2], x[3],
                x[4], x[5], data)
        x_new_lik = likelihood_Function(x_new[0], x_new[1], x_new[2], x_new[3],
         x_new[4], x_new[5],data)

        if (acceptance_rule(x_lik + np.log(model_Prior(x[0], x[1], x[2], x[3],
                x[4], x[5], x[6:])),x_new_lik+np.log(model_Prior(x_new[0], x_new[1], x_new[2], x_new[3],
                 x_new[4], x_new[5], x_new[6:])))):
            x = x_new
            accepted.append(x_new)
            likely_accepted.append(x_new_lik)
        else:
            rejected.append(x_new)
        print("Iteration %i/%i"%(ii+1,iterations), end="\r")

    graph_Likelihood(likely_accepted)
    return np.array(accepted), np.array(rejected)

def graph_Likelihood(likelihood):
    f = plt.figure()
    plt.plot(range(1,len(likelihood)+1), likelihood)
    plt.xlabel("Accepted Values")
    plt.ylabel("Likelihood")
    plt.tight_layout()
    plt.savefig("likelihood.png")

def graph_Confidence(result):
    # H_0,omega_m0, omega_q0, alpha, alpha_x, m
    H_0 = [ii[0] for ii in result]
    omega_m0 = [ii[1] for ii in result]
    omega_q0 = [ii[2] for ii in result]
    alpha = [ii[3] for ii in result]
    alpha_x = [ii[4] for ii in result]
    m = [ii[5] for ii in result]

    f = plt.figure(figsize=(15,15))
    gs = GridSpec(5, 5)
    f1 = f.add_subplot(gs[0, 0])
    f1.scatter(H_0, omega_m0, s=1)
    f1.set_xlabel(r"$H_0$")
    f1.set_ylabel(r"$\Omega_{m_0}$")

    f2 = f.add_subplot(gs[0, 1])
    f2.scatter(H_0, omega_q0, s=1)
    f2.set_xlabel(r"$H_0$")
    f2.set_ylabel(r"$\Omega_{q_0}$")

    f3 = f.add_subplot(gs[0, 2])
    f3.scatter(H_0, alpha, s=1)
    f3.set_xlabel(r"$H_0$")
    f3.set_ylabel(r"$\alpha$")

    f4 = f.add_subplot(gs[0, 3])
    f4.scatter(H_0, alpha_x, s=1)
    f4.set_xlabel(r"$H_0$")
    f4.set_ylabel(r"$\alpha_x$")

    f5 = f.add_subplot(gs[0, 4])
    f5.scatter(H_0, m, s=1)
    f5.set_xlabel(r"$H_0$")
    f5.set_ylabel(r"$m$")

    #New row ========
    f6 = f.add_subplot(gs[1, 0])
    f6.scatter(m, omega_m0, s=1)
    f6.set_xlabel(r"$m$")
    f6.set_ylabel(r"$\Omega_{m_0}$")

    f7 = f.add_subplot(gs[1, 1])
    f7.scatter(m, omega_q0, s=1)
    f7.set_xlabel(r"$m$")
    f7.set_ylabel(r"$\Omega_{q_0}$")

    f8 = f.add_subplot(gs[1, 2])
    f8.scatter(m, alpha, s=1)
    f8.set_xlabel(r"$m$")
    f8.set_ylabel(r"$\alpha$")

    f9 = f.add_subplot(gs[1, 3])
    f9.scatter(m, alpha_x, s=1)
    f9.set_xlabel(r"$m$")
    f9.set_ylabel(r"$\alpha_x$")

    #New row ========
    f10 = f.add_subplot(gs[2, 0])
    f10.scatter(alpha_x, omega_m0, s=1)
    f10.set_xlabel(r"$\alpha_x$")
    f10.set_ylabel(r"$\Omega_{m_0}$")

    f11 = f.add_subplot(gs[2, 1])
    f11.scatter(alpha_x, omega_q0, s=1)
    f11.set_xlabel(r"$\alpha_x$")
    f11.set_ylabel(r"$\Omega_{q_0}$")

    f12 = f.add_subplot(gs[2, 2])
    f12.scatter(alpha_x, alpha, s=1)
    f12.set_xlabel(r"$\alpha_x$")
    f12.set_ylabel(r"$\alpha$")

    #New row ========
    f13 = f.add_subplot(gs[3, 0])
    f13.scatter(alpha, omega_m0, s=1)
    f13.set_xlabel(r"$\alpha$")
    f13.set_ylabel(r"$\Omega_{m_0}$")

    f14 = f.add_subplot(gs[3, 1])
    f14.scatter(alpha, omega_q0, s=1)
    f14.set_xlabel(r"$\alpha$")
    f14.set_ylabel(r"$\Omega_{q_0}$")

    #New row ========
    f15 = f.add_subplot(gs[4, 0])
    f15.scatter(omega_q0, omega_m0, s=1)
    f15.set_xlabel(r"$\Omega_{q_0}$")
    f15.set_ylabel(r"$\Omega_{m_0}$")

    plt.tight_layout()
    plt.savefig("result.pdf")
