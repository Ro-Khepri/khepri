% Identification de la polaire du H201B Libelle à partir de la polaire des vitesses
% du dossier de calcul du constructeur (annexe 3 du rapport SFE 2023-02,
% SLT Pierre André Noël BOUASSE-BOU-KOMBILE-KOMBILE, juin 2023).
% Reconstitué depuis le PDF du rapport (aucun fichier source fourni).
% Nécessite le fichier new_250.mat : points (Va en km/h, Vz en m/s) numérisés avec
% Grabit sur la polaire des vitesses du dossier de calcul (non fourni avec le rapport).
clear all; close all; clc;
%chargement de point précédemment obtenus avec Grabit
load('new_250.mat')
%Données du planeur
Mmin = 250;%masse minimale
Mmax = 350;%masse maxmale
g = 9.81;%acceleration de la pesanteur
rho = 1.225;%masse volumique de lair
s = 9.8;%surface alaire
%inversion des points et conversion des vitesses de km/h en m/s
Va = flipud(new_250(:,1))/3.6;
%calcul de Cz pour masse égale a 250kg
Cz_min = (2*Mmin*g)./(rho*s*Va.^2);
%inversion des points de vitesses
Vz = flipud(new_250(:,2));
%calcul de Cx pour masse égale a 250kg
Cx_min = Vz*(Mmin*g)./(0.5*rho*s*Va.^3);
% lissage des donnees obtenues par numerisation
p_min = polyfit(Cz_min,Cx_min,2);
Cz = linspace(0,1.3,200);
Cx = polyval(p_min,Cz);
%affichage des courbes de polaire de Cx = f(Cz) a m=250kg
figure
plot(Cz_min,Cx_min,'.')
hold on
plot(Cz,Cx)
hold off
legend('donnees','identification')
xlabel('Cz'); ylabel('Cx')
%affichage des courbes de polaire de vitesses a m=250kg
figure
plot(Va,-Vz,'.')
hold on
Va_c = sqrt((2*Mmin*g)./(rho*s*Cz));
Vz_c = (0.5*rho*s*((2*Mmin*g)./(rho*s*Cz)).^(3/2).*Cx)/(Mmin*g);
plot(Va_c(18:end),-Vz_c(18:end))
hold off
legend('donnees','identification')
xlabel('Va (m/s)'); ylabel('Vz (m/s)')
