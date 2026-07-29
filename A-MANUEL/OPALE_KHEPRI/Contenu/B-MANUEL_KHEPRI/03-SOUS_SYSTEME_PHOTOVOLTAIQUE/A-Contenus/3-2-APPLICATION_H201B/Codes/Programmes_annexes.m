function [Puissance] = puissance_planeur_plat(day)
%puissance recue par un planeur suppose completement horizontal (sans
%prise en compte de la courbure des ailes)
M = 350; S = 9.5; lbd = 23; h = 500; fmax = 34;
ki = 1/(pi*lbd); Cx0=1/(4*ki*fmax*fmax); Czfmax = power((Cx0/ki), 0.5);
rho0 = 1.225; P0 = 101325; T0 = 288.15; Th = 0.0065; g = 9.81;
rho = rho0*power(1+(Th/T0)*h,-4.26); Ph = P0*power(1+(Th/T0)*h,-3.26);
Va = sqrt((2*M*g)/(rho*S*Czfmax));
Puissance = [];
for h = 0:23
  p = Modele_eclairement_solaire_3(P0,Ph,day,h,43.16,0,0,0);
  Puissance = [Puissance; p*9.5*0.16];
end
end

function [temps_debut_de_vol] = debut_de_vol(liste)
%heure a laquelle la puissance solaire devient non nulle (lever du soleil)
t0=0;
for p = 1:length(liste)
  if liste(p) ~= 0 && t0==0
    t0 = p*24/length(liste);
  end
end
temps_debut_de_vol = t0;
end

function [temps_de_fin_de_vol] = fin_de_vol(liste)
%heure a laquelle la puissance solaire redevient nulle (coucher du soleil)
tf=0;
for p = 1:length(liste)-1
  if liste(p) ~= 0 && liste(p+1)==0 && tf==0
    tf = p*24/length(liste);
  end
end
temps_de_fin_de_vol = tf;
end

function [integrale] = integration(liste)
%integration par la methode des trapezes
integrale = 0;
for i=1:length(liste)-1
  integrale = integrale + (liste(i)+liste(i+1))*(24/(length(liste)-1))/2;
end
end