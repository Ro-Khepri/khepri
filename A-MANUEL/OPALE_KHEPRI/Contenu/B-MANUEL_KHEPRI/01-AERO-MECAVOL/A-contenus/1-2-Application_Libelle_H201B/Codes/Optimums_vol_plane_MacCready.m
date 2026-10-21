% Optimums du vol plané du H201B Libelle : finesse maximale, taux de chute minimal,
% vitesse MacCready (annexes du rapport SFE 2023-02, SLT Sultan ASIRI, juin 2023),
% adapté de l'exemple MathWorks « Calculating Best Glide Quantities » (Aerospace Toolbox).
% Reconstitué depuis le PDF du rapport (aucun fichier source fourni) :
%  - les valeurs affichées dans le rapport ont été retirées du code et reportées en commentaire ;
%  - deux lignes coupées dans le PDF (legend, disp) ont été rejointes ;
%  - le signe « - » perdu dans (TAB_VZ(i_max_mc)-Vz_mc) a été rétabli.
% Nécessite le fichier new_350.mat (polaire des vitesses à 350 kg numérisée avec Grabit,
% Va en km/h et Vz en m/s), non fourni avec le rapport.
% Résultat donné par le rapport :
%   Mc Cready optimal speed for thermal ascendind velocity Vz=0 : 29.156 m/s

%% Données de l'aéronef (H201B Libelle)
W = 3430; % weight, N
S = 9.8; % wing reference area, m^2;
A = 22.95; % wing aspect ratio
C_D0 = 0.0093; % flaps up parasite drag coefficient
e = 1/(pi*A*0.0139); % airplane efficiency factor
% first case : polaire parabolique
Tab_Cz = .1:.1:1.3;
Tab_Cx = C_D0 + 1/(pi*A*e)*Tab_Cz.^2;
Tab_f = Tab_Cz ./ Tab_Cx;
k2 = 1/(pi*A*e) % rapport : k2 = 0.0139
% speed polar : polaire des vitesses numérisée à 350 kg
load('new_350.mat')
% Tab_Speed_Polar = horzcat(smooth(new_350(:,1)),smooth(new_350(:,2)));
Tab_Speed_Polar = horzcat(new_350(:,1)/3.6,new_350(:,2));
Tab_Cz = W./(.5*1.225*S*Tab_Speed_Polar(:,1).^2);
Tab_Cx = Tab_Speed_Polar(:,2)./(.5*1.225*S*Tab_Speed_Polar(:,1).^3)*W;
Tab_f = Tab_Cz ./ Tab_Cx;
% second case : Cx = Cx0 + k1*Cz + k2 * Cz^2
k1 = .01;
k2 = 1/(pi*A*e)
% Mac Cready (vertical thermal)
Vz1 = 2;

%% Conditions
h = 4000; % altitude, ft
phi = 0; % bank angle, deg
h_m = convlength(h,'ft','m');
[T, a, P, rho] = atmoscoesa(h_m, 'Warning');

%% Best Glide Data
lift_to_drag_ratio=Tab_Cz./Tab_Cx;
[lift_to_drag_ratio_max,i_ltdrm]=max(lift_to_drag_ratio);
TAS_bg = sqrt( (2*W)/(rho*S*Tab_Cz(i_ltdrm)) ); % TAS, m/s
KTAS_bg = convvel(TAS_bg,'m/s','kts')';
KCAS_bg = correctairspeed(KTAS_bg,a,P,'TAS','CAS')';
gamma_bg_rad = asin( -1/lift_to_drag_ratio_max );
gamma_bg = convang(gamma_bg_rad,'rad','deg');
D_bg = -W*sin(gamma_bg_rad);
L_bg = W*cos(gamma_bg_rad);
qbar = dpressure([TAS_bg' zeros(size(TAS_bg,2),2)], rho);
C_D_bg = D_bg./(qbar*S);
C_L_bg = L_bg./(qbar*S);

%% Verification
TAS = 0.3048*(50:200)'; % true airspeed, m/s
KTAS = convvel(TAS,'m/s','kts')'; % true airspeed, kts
KCAS = correctairspeed(KTAS,a,P,'TAS','CAS')'; % corrected airspeed, kts
qbar = dpressure([TAS zeros(size(TAS,1),2)], rho);
Dp = qbar*S.*C_D0;
Di = (2*W^2)/(rho*S*pi*e*A).*(TAS.^-2);
D = Dp + Di;
L = W;
% Plot L/D versus KCAS
h1 = figure;
plot(KCAS,L./D);
title('L/D vs. KCAS');
xlabel('KCAS'); ylabel('L/D');
hold on
plot(KCAS_bg,L_bg/D_bg,'Marker','o','MarkerFaceColor','black',...
'MarkerEdgeColor','black','Color','white');
hold off
legend('L/D','L_{bg}/D_{bg}','Location','Best');
annotation('textarrow',[0.49 0.49],[0.23 0.12],'String','KCAS_{bg}');
% Plot parasite, induced, and total drag curves
h2 = figure;
plot(KCAS,Dp,KCAS,Di,KCAS,D);
title('Parasite, induced, and total drag curves');
xlabel('KCAS'); ylabel('Drag, N');
hold on
plot(KCAS_bg,D_bg,'Marker','o','MarkerFaceColor','black',...
'MarkerEdgeColor','black','Color','white');
hold off
legend('Parasite, D_p','Induced, D_i','Total, D','D_{bg}','Location','Best');
annotation('textarrow',[0.49 0.49],[0.23 0.12],'String','KCAS_{bg}');
close(h1,h2);

%% Best descent rate
C_L_bdr = sqrt(3*C_D0*pi*A*e);
TAS_bdr = sqrt( (2*W)/(rho*S*C_L_bdr) ); % TAS, m/s
K_i=1/(pi*A*e);
C_D_bdr = C_D0+K_i*C_L_bdr^2;
Vdr=-TAS_bdr*C_D_bdr/C_L_bdr; % descent rate
Power_Required=D.*TAS;
[Power_Required_min,i_prm]=min(Power_Required);
TAS_bdr = TAS(i_prm); % TAS, m/s
KTAS_bdr = convvel(TAS_bdr,'m/s','kts')'; % true airspeed, kts
KCAS_bdr = correctairspeed(KTAS_bdr,a,P,'TAS','CAS')';
TAB_VA=sqrt(W./(0.5*rho*S*Tab_Cz));
TAB_VZ=-0.5*rho*S*TAB_VA.^3.*Tab_Cx/W;
% plot power curve
h3 = figure;
plot(KCAS,Dp.*TAS,KCAS,Di.*TAS,KCAS,D.*TAS);
title('Parasite, induced, and total drag power curves');
xlabel('KCAS'); ylabel('POWER REQUIRED , W');
hold on
plot(KCAS_bdr,Power_Required_min,'Marker','o','MarkerFaceColor','black',...
'MarkerEdgeColor','black','Color','white');
hold off
legend('Parasite, DP_p','Induced, DP_i','Total, DP','DP_{bdr}','Location','Best');
annotation('textarrow',[0.29 0.29],[0.23 0.12],'String','KCAS_{bdr}');

%% Mac Cready
Vz_mc = 0 % vitesse de montée attendue dans la prochaine ascendance, m/s
figure; plot(TAB_VA,TAB_VZ)
slope_Mac=(Vz_mc-TAB_VZ)./(0-TAB_VA);
[MAX_slope_Mac,i_max_mc]=max(slope_Mac) % rapport : MAX_slope_Mac = -0.0336, i_max_mc = 175
hold on; plot([0 TAB_VA(1)],[Vz_mc (Vz_mc+(TAB_VZ(i_max_mc)-Vz_mc)/(TAB_VA(i_max_mc)-0)*TAB_VA(1))]);
plot(TAB_VA(i_max_mc),TAB_VZ(i_max_mc),'r*') % plot([0 TAB_VA(i_max_mc)],[Vz_mc TAB_VZ(i_max_mc)])
xlabel('Vitesse (m/s)'); ylabel('Vz (m/s)'); title('McCready')
disp( ['Mc Cready optimal speed for thermal ascendind velocity Vz=',num2str(Vz_mc),' : ',num2str(TAB_VA(i_max_mc)),' m/s'])
