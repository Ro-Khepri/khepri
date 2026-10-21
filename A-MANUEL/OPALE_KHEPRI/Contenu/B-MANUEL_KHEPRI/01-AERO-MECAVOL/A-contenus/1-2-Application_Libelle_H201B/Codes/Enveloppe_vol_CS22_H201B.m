% Enveloppe de vol du H201B Libelle selon la CS-22 amendement 3 :
% domaine de manoeuvre (annexe 1) et domaine de rafale (annexe 2)
% Rapport SFE 2023-02, SLT Pierre André Noël BOUASSE-BOU-KOMBILE-KOMBILE (juin 2023)
% Reconstitué depuis le PDF du rapport (aucun fichier source fourni) :
%  - la ligne « Tab_V_n = ... », tronquée dans le PDF, a été complétée ;
%  - Vmax est calculée en km/h, d'où les divisions par 3,6 (le marqueur du point J
%    est placé en Vmax et non en Vmax/3.6 : à corriger pour l'afficher).
%%%%%%%%%%%%% Données du planeur Libelle H201B %%%%%%%%%%%%%%
b = 15;%envergure
S = 9.8;%surface alaire
Mav = 185;%masse à vide
Mmax = 350;%masse maximale
nz_max_p = 5.3;%facteur de charge maximal positif
n_norm = 4;%facteur de charge à vitesse max sur le ventre
np = 1;% facteur de charge en vol en palier sur le ventre
nn = -1;% facteur de charge en vol en palier sur le dos
Le = 0.653;%corde moyenne
n_normn = -1.5;%facteur de charge maximal à vitesse max sur le dos
Cd = 0.0113; %coefficient de traînée min
Cla = 5.38;%gradiant de portance
Clamax = 1.42;%coefficient de portance max
Clamin = 0.8;%coefficient de portance min
nz_max_n = -2.65;%facteur de charge maximal negatif
g = 9.81;%constante de gravité
rho=1.225;%masse volumique au niveau de la mer
%%%%%%%%%%%%%%%%%%% Domaine de vol %%%%%%%%%%%%%%%%%%%%%%%%%%
%                  Calcul de vitesses                       %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Vitesse de décrochage positive
Vs = sqrt(Mmax*g/(0.5*rho*S*Clamax))
%Vitesse de décrochage négative
Vs_n = sqrt(Mmax*g/(0.5*rho*S*abs(Clamin)))
%Vitesse de manoeuvre positive
Vmap = Vs*sqrt(nz_max_p)
Tab_nz_p = 0:.01:nz_max_p;
Tab_V_p = Vs*sqrt(Tab_nz_p);
%Vitesse de manoeuvre négative
Vman = Vs_n*sqrt(abs(nz_max_n))
Tab_nz_n = 0:-.01:nz_max_n;
Tab_V_n = Vs_n*sqrt(abs(Tab_nz_n));
% Vitesse maximale
Vmax = 18*((Mmax*g/10)/(Cd*S))^(1/3);
figure
plot(Tab_V_p,Tab_nz_p, 'k' ,'LineWidth',2)
hold on
plot(Tab_V_n,Tab_nz_n, 'k' ,'LineWidth',2)
hold on
plot([Vmap Vmax/3.6], [nz_max_p n_norm], 'k','LineWidth',2)
plot([Vs Vs], [1 0], 'k','LineWidth',2)
plot([Vs Vs_n], [0 0], 'k','LineWidth',2)
plot([Vs_n Vs_n], [-1 0], 'k','LineWidth',2)
plot([Vmax/3.6 Vmax/3.6], [n_norm n_normn], 'k', 'LineWidth',2)
plot([Vman Vmax/3.6], [nz_max_n n_normn], 'k', 'lineWidth',2)
axis ([0 100 -4 6])
xlabel('Vitesse en m/s'), ylabel('Facteur de charge')
grid on
hold on
plot(Vmap, nz_max_p, 'ob', 'MarkerSize',4,'MarkerFaceColor','k')
text(Vmap, nz_max_p, '\leftarrow A', 'FontSize',12)
plot(Vman, nz_max_n, 'ob', 'MarkerSize',4,'MarkerFaceColor','k')
text(Vman, nz_max_n, '\leftarrow B', 'FontSize',12)
plot(Vmax/3.6, n_norm, 'ob', 'MarkerSize',4, 'MarkerFaceColor','k' )
text(Vmax/3.6, n_norm, '\leftarrow D', 'FontSize',12)
plot(Vmax/3.6, n_normn, 'ob', 'MarkerSize',4, 'MarkerFaceColor','k' )
text(Vmax/3.6, n_normn, '\leftarrow C', 'FontSize',12)
plot(Vs, np, 'ob', 'MarkerSize',4, 'MarkerFaceColor','k' )
text(Vs, np, '\leftarrow S', 'FontSize',12)
plot(Vs_n, nn, 'ob', 'MarkerSize',4, 'MarkerFaceColor','k' )
text(Vs_n, nn, '\leftarrow S''', 'FontSize',12)
% Domaine de rafale
Tab_V_q = [0 Vmax/3.6];
Tab_V_s = [0 Vmap];
Mu = 2*Mmax/(rho*S*Le*Cla)%mass ratio
K = 0.96*Mu/(5.78075 + 1.090725*Mu)
Ude = [15;7.5];%Intensité des rafales
V_line_15_p = 1 + (K*rho*Ude(1)*Cla*Tab_V_s*S/(2*Mmax*g))
V_line_15_n = 1 + (K*rho*-Ude(1)*Cla*Tab_V_s*S/(2*Mmax*g))
V_line_7_p = 1 + (K*rho*Ude(2)*Cla*Tab_V_q*S/(2*Mmax*g))
V_line_7_n = 1 + (K*rho*-Ude(2)*Cla*Tab_V_q*S/(2*Mmax*g))
nzf_m = 1 + (K*rho*Ude(2)*Cla*Vmax*S/(3.6*2*Mmax*g))
nzf_mn = 1 + (K*rho*-Ude(1)*Cla*Vmap*S/(2*Mmax*g))
nzf_m_vm = 1 + (K*rho*-Ude(2)*Cla*Vmax*S/(3.6*2*Mmax*g))
plot(Tab_V_s,V_line_15_p,'r')
hold on;
plot(Tab_V_s,V_line_15_n,'r')
plot(Tab_V_q,V_line_7_p,'r')
plot(Tab_V_q,V_line_7_n,'r')
plot([Vmap Vmax/3.6], [nz_max_p nzf_m], 'r')
plot([Vmap Vmax/3.6], [nzf_mn nzf_m_vm], 'r')
plot([Vmax/3.6 Vmax/3.6], [nzf_m nzf_m_vm], 'r')
plot(Vmax/3.6, nzf_m, 'ob', 'MarkerSize',4,'MarkerFaceColor','k')
text(Vmax/3.6, nzf_m, '\leftarrow I', 'FontSize',12)
plot(Vmax, nzf_m_vm, 'ob', 'MarkerSize',4,'MarkerFaceColor','k')
text(Vmax/3.6, nzf_m_vm, '\leftarrow J', 'FontSize',12)
plot(Vmap, nzf_mn, 'ob', 'MarkerSize',4,'MarkerFaceColor','k')
text(Vmap, nzf_mn, '\leftarrow A', 'FontSize',12)
text(20,2.5,'Rafales de vent','FontSize',8,'Color','r')
xline(V_line_7_n, '--c')
