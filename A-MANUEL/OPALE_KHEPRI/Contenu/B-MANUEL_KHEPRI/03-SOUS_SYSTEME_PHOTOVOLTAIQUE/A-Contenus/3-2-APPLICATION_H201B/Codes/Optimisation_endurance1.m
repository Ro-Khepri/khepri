function [endurance] = optimisation_endurance1(Pu)
%renvoie l'endurance en temps du planeur (hypothese : energie solaire
%totale disponible des le debut du vol)
M = 350; S = 9.5; lbd = 23; h = 500; h_vent_arriere = 300;
fmax = 34; Va = 87/3.6;
ki = 1/(pi*lbd); Cx0=1/(4*ki*fmax^2); Czfmax = power((Cx0/ki), 0.5); g=9.81;
jour = 175; %journee de vol (175 = meilleur, 357 = pire)
rho0 = 1.225; T0=288.15; Th=0.0065;
rho = rho0*power((1+(Th/T0)*h),-4.26);
Vfmax = sqrt(2*M*g/(rho*S*Czfmax));
m_ajoutee = 50; m_moteur = 3.3 * Pu*10^-3/0.8; m_batterie = 46 - m_moteur;
Puissance_solaire = optimisation_cap1(jour,h,24);
Energie_solaire = integration(Puissance_solaire);
Capacite_batterie = 190*m_batterie; Capacite_totale = Capacite_batterie + Energie_solaire;
Duree_fonctionnement_moteur = Capacite_totale/(Pu/0.8);
finesse_optimisee = -1/pente_fonction_puissance2(Pu);
Distance_possible = abs(finesse_optimisee)*(h - h_vent_arriere);
Duree_vol_possible = Distance_possible / (Vfmax*3600);
if Duree_vol_possible <= Duree_fonctionnement_moteur
endurance = Duree_vol_possible;
else
d_moteur = Duree_fonctionnement_moteur*Vfmax*3600;
h_descendue = d_moteur/finesse_optimisee;
d_suivante = fmax*(h - h_vent_arriere - h_descendue);
duree_suivante = d_suivante/(Vfmax*3600);
endurance = Duree_fonctionnement_moteur + duree_suivante;
end
end