%Annexe 10 : calcul de l'heure de depart optimal
Pu = [1000:2500];
jour = 175;
Puissance_solaire = optimisation_cap1(jour,500,500);
t0 = debut_de_vol(Puissance_solaire);
tf = fin_de_vol(Puissance_solaire);
maximum = 0; decollage = 0;
for j = floor(t0)+1:floor(tf)
endurance_opt=[];
for k = 1000:2500
endurance_opt = [endurance_opt, optimisation_endurance3(k, j)];
end
max_endurancej = max(endurance_opt);
if max_endurancej > maximum
maximum = max_endurancej; decollage = j;
end
end
% optimisation_endurance3 = optimisation_endurance2 avec l'heure de
% decollage en parametre d'entree (boucle demarree a floor(d/dt))