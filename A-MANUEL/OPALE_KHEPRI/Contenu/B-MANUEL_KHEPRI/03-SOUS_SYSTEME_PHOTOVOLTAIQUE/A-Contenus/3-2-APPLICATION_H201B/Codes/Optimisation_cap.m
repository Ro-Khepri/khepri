function [cap] = optimisation_cap2(jour,h)
%renvoie une liste de 24 cap pour optimiser la puissance pendant une
%journee (24h) avec comme parametre de definition le jour pendant lequel on
%vole
%Donnees planeur
M = 350; %masse maximal [kg]
Ca = 35.7 ; % charge alaire [kg/m2]
e = 15 ; % envergure [m]
L =6.20; %longueur[m]
S =9.5; %surface alaire [m2]
lbd= 23; %allongement
fmax= 34; % finesse max
ki= 1/(pi*lbd); % car portance elliptique
Cx0=1/(4*ki*fmax*fmax);
Cxfmax= 2*Cx0;
Czfmax = power((Cx0/ki), 0.5);
latitude_deg=43.16;%position Salon de provence
%modele atmosphere
rho0 = 1.225; %kg.m-3
P0= 101325; %Pa
T0=288.15; %K
Th = 0.0065;
g=9.81;
rho = rho0*power(1+(Th/T0)*h,-4.26);
Ph = P0 * power(1+(Th/T0)*h,-3.26);
%surface du planeur
S1 = 0.98; S2 = 0.61; S3 = 3.1;
S5 = (0.30+0.42)*1.05; S6 = (0.26+0.45)*0.75;
surface_totale=S1+S2+S3+S5+S6;
N=5; %nombre d'increments
cap_test = transpose(2*pi/N*[0:N-1]);
cap=[]; Puissance_solaire=[]; P=[]; Heure=[];
for h = 0:23
Heure = [Heure; h];
if Modele_eclairement_solaire_3(P0,Ph,jour,h,latitude_deg,0,0,0)==0
cap = [cap, 300]; P = [P zeros(N,1)]; Puissance_solaire = [Puissance_solaire, 0];
else
p1 = Modele_eclairement_solaire_3(P0,Ph,jour,h,45,atan(0.42),cap,0);
p2 = Modele_eclairement_solaire_3(P0,Ph,jour,h,45,atan(0.11),cap,0);
p3 = Modele_eclairement_solaire_3(P0,Ph,jour,h,45,atan(0.17),cap,0);
p5 = Modele_eclairement_solaire_3(P0,Ph,jour,h,45,0,cap,0);
p6 = Modele_eclairement_solaire_3(P0,Ph,jour,h,45,pi/2,cap,0);
P = [P p1*S1 + p2*S2 + p3*S3 + p5*S5 + p6*S6];
[max_p,indice_max]=max(P(:,h));
cap = [cap, indice_max*2*pi/N];
end
end
end