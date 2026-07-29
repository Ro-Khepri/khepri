function [pente]=pente_fonction_puissance2(Pu)
%renvoie la valeur de la pente en fonction de la puissance du moteur
M = 350; Ca = 35.7; e = 15; L = 6.20; S = 9.5; lbd = 23;
h = 500; fmax = 34;
ki = 1/(pi*lbd); Cx0=1/(4*ki*fmax^2); Cxfmax=2*Cx0;
Czfmax = power((Cx0/ki), 0.5); g=9.81;
rho0 = 1.225; T0=288.15; Th=0.0065;
rho = rho0*power((1+(Th/T0)*h),-4.26);
Vfmax = sqrt(2*M*g/(rho*S*Czfmax));
pente = Pu/(Vfmax*M*g) - 0.5*rho*S*Vfmax^2*Cxfmax/(M*g);
end