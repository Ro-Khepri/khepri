function [endurance] = optimisation_endurance2(Pu)
%second modele : l'energie solaire est distribuee pas a pas dans le temps
%(et non disponible en totalite des le debut du vol)
N = 500; dt = 24/N;
M = 350; S = 9.5; lbd = 23; h = 500; h_vent_arriere = 300; fmax = 34;
ki = 1/(pi*lbd); Cx0=1/(4*ki*fmax^2); Czfmax = power((Cx0/ki), 0.5); g=9.81;
jour = 357;
rho0 = 1.225; T0=288.15; Th=0.0065;
rho = rho0*power((1+(Th/T0)*h),-4.26);
Vfmax = sqrt(2*M*g/(rho*S*Czfmax));
m_ajoutee = 50; m_moteur = 3.3*Pu*10^-3/0.8; m_batterie = 46 - m_moteur;
Capacite_batterie = 190*m_batterie; Capacite_totale = Capacite_batterie;
cap = optimisation_cap2(jour,h);
Puissance_solaire = optimisation_cap1(jour,h,N);
t0 = debut_de_vol(Puissance_solaire);
Test_charge = 0; altitude = h; temps_de_fin=[];
for p = 1:N
if Puissance_solaire(p)~=0 && altitude > 300
if Test_charge==0
if Capacite_totale > 0
Capacite_totale = Capacite_totale - (Pu/0.8)*dt + Puissance_solaire(p)*dt;
altitude = altitude - Vfmax*3600*dt*abs(pente_fonction_puissance2(Pu));
else
Test_charge = 1;
end
else
if Capacite_totale < Capacite_batterie
altitude = altitude - Vfmax*3600*fmax*dt;
Capacite_totale = Capacite_totale + Puissance_solaire(p)*dt;
else
Test_charge = 0;
end
end
elseif Puissance_solaire(p)~=0
temps_de_fin = [temps_de_fin, p*24/N];
end
end
if isempty(temps_de_fin)
endurance = fin_de_vol(Puissance_solaire) - t0;
else
endurance = temps_de_fin(1) - t0;
end
end